"""
Message Queue - Project 5.3
RabbitMQ connection and message handling for federated agents.
"""

import os
import json
import time
from typing import Callable, Optional
from dataclasses import dataclass

import pika
from pika.exceptions import AMQPConnectionError

from message_schema import AgentMessage, AgentType, MessageType


@dataclass
class QueueConfig:
    """RabbitMQ configuration."""
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    virtual_host: str = "/"
    
    @classmethod
    def from_env(cls) -> "QueueConfig":
        """Load config from environment variables."""
        return cls(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            username=os.getenv("RABBITMQ_USER", "guest"),
            password=os.getenv("RABBITMQ_PASS", "guest"),
            virtual_host=os.getenv("RABBITMQ_VHOST", "/")
        )


# Queue names for each agent
AGENT_QUEUES = {
    AgentType.LOCAL_CLAUDE: "agent.local.claude",
    AgentType.LOCAL_OPENAI: "agent.local.openai",
    AgentType.CLOUD_GEMINI: "agent.cloud.gemini",
    AgentType.ORCHESTRATOR: "agent.orchestrator"
}

# Exchange for broadcasting
BROADCAST_EXCHANGE = "agent.broadcast"


class MessageQueue:
    """
    RabbitMQ message queue handler.
    
    Handles:
    - Connection management with retry
    - Sending messages to specific agents
    - Receiving messages for an agent
    - Broadcasting to all agents
    """
    
    def __init__(self, config: QueueConfig = None):
        self.config = config or QueueConfig.from_env()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
    
    def connect(self, max_retries: int = 5, retry_delay: int = 5) -> bool:
        """Connect to RabbitMQ with retry logic."""
        credentials = pika.PlainCredentials(
            self.config.username,
            self.config.password
        )
        
        params = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            virtual_host=self.config.virtual_host,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        for attempt in range(max_retries):
            try:
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                
                # Declare all queues
                for queue_name in AGENT_QUEUES.values():
                    self.channel.queue_declare(queue=queue_name, durable=True)
                
                # Declare broadcast exchange
                self.channel.exchange_declare(
                    exchange=BROADCAST_EXCHANGE,
                    exchange_type="fanout",
                    durable=True
                )
                
                print(f"✅ Connected to RabbitMQ at {self.config.host}:{self.config.port}")
                return True
                
            except AMQPConnectionError as e:
                print(f"⚠️ Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        print("❌ Failed to connect to RabbitMQ")
        return False
    
    def disconnect(self):
        """Close connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("🔌 Disconnected from RabbitMQ")
    
    def send_message(self, message: AgentMessage) -> bool:
        """Send a message to a specific agent's queue."""
        if not self.channel:
            print("❌ Not connected to RabbitMQ")
            return False
        
        queue_name = AGENT_QUEUES.get(message.target_agent)
        if not queue_name:
            print(f"❌ Unknown target agent: {message.target_agent}")
            return False
        
        try:
            self.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message.to_json(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type="application/json",
                    correlation_id=message.correlation_id,
                    priority={"low": 1, "medium": 5, "high": 9}.get(message.priority.value, 5)
                )
            )
            print(f"📤 Sent {message.message_type.value} to {message.target_agent.value}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False
    
    def broadcast(self, message: AgentMessage) -> bool:
        """Broadcast a message to all agents."""
        if not self.channel:
            return False
        
        try:
            self.channel.basic_publish(
                exchange=BROADCAST_EXCHANGE,
                routing_key="",
                body=message.to_json(),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            print(f"📢 Broadcast {message.message_type.value} to all agents")
            return True
        except Exception as e:
            print(f"❌ Broadcast failed: {e}")
            return False
    
    def consume(
        self,
        agent_type: AgentType,
        callback: Callable[[AgentMessage], Optional[AgentMessage]],
        auto_ack: bool = False
    ):
        """
        Start consuming messages for an agent.
        
        Args:
            agent_type: Which agent's queue to consume from
            callback: Function to process messages, returns response or None
            auto_ack: Whether to auto-acknowledge messages
        """
        if not self.channel:
            print("❌ Not connected")
            return
        
        queue_name = AGENT_QUEUES.get(agent_type)
        if not queue_name:
            print(f"❌ Unknown agent type: {agent_type}")
            return
        
        def on_message(ch, method, properties, body):
            try:
                message = AgentMessage.from_json(body.decode())
                print(f"📥 Received {message.message_type.value} from {message.source_agent.value}")
                
                # Process message
                response = callback(message)
                
                # Send response if provided
                if response:
                    self.send_message(response)
                
                # Acknowledge
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # Set prefetch
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message,
            auto_ack=auto_ack
        )
        
        print(f"👂 {agent_type.value} listening on {queue_name}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            print("🛑 Stopped consuming")
    
    def get_message(self, agent_type: AgentType) -> Optional[AgentMessage]:
        """Get a single message (non-blocking)."""
        if not self.channel:
            return None
        
        queue_name = AGENT_QUEUES.get(agent_type)
        if not queue_name:
            return None
        
        method, properties, body = self.channel.basic_get(queue_name, auto_ack=True)
        
        if body:
            return AgentMessage.from_json(body.decode())
        return None
    
    def get_queue_stats(self) -> dict:
        """Get message counts for all queues."""
        if not self.channel:
            return {}
        
        stats = {}
        for agent, queue_name in AGENT_QUEUES.items():
            try:
                result = self.channel.queue_declare(queue=queue_name, passive=True)
                stats[agent.value] = {
                    "messages": result.method.message_count,
                    "consumers": result.method.consumer_count
                }
            except Exception:
                stats[agent.value] = {"messages": 0, "consumers": 0}
        
        return stats


# Convenience functions
def create_queue() -> MessageQueue:
    """Create and connect a message queue."""
    mq = MessageQueue()
    mq.connect()
    return mq


if __name__ == "__main__":
    # Test connection
    mq = MessageQueue()
    
    if mq.connect():
        stats = mq.get_queue_stats()
        print("\n📊 Queue Stats:")
        for agent, info in stats.items():
            print(f"  {agent}: {info['messages']} messages, {info['consumers']} consumers")
        mq.disconnect()