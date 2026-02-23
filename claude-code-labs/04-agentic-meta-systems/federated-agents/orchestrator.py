"""
Orchestrator - Project 5.3
Central control plane for federated agent system.
"""

import time
import threading
from typing import Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime

from message_schema import (
    AgentMessage, AgentType, MessageType, TaskType, Priority
)
from message_queue import MessageQueue, AGENT_QUEUES


@dataclass
class TaskStatus:
    """Track status of a submitted task."""
    task_id: str
    task_type: TaskType
    target_agent: AgentType
    status: str = "pending"  # pending, processing, completed, failed
    submitted_at: str = ""
    completed_at: str = ""
    result: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.submitted_at:
            self.submitted_at = datetime.utcnow().isoformat()


class Orchestrator:
    """
    Central orchestrator for the federated agent system.
    
    Responsibilities:
    - Submit tasks to agents
    - Track task status
    - Handle multi-agent workflows
    - Monitor agent health
    """
    
    def __init__(self):
        self.mq = MessageQueue()
        self.tasks: dict[str, TaskStatus] = {}
        self.agent_status: dict[AgentType, dict] = {}
        self.response_handlers: dict[str, Callable] = {}
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None
    
    def connect(self) -> bool:
        """Connect to message queue."""
        return self.mq.connect()
    
    def disconnect(self):
        """Disconnect and cleanup."""
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=2)
        self.mq.disconnect()
    
    def start_listener(self):
        """Start background thread to listen for responses."""
        self._running = True
        self._listener_thread = threading.Thread(target=self._listen_for_responses)
        self._listener_thread.daemon = True
        self._listener_thread.start()
    
    def _listen_for_responses(self):
        """Background listener for responses."""
        while self._running:
            try:
                message = self.mq.get_message(AgentType.ORCHESTRATOR)
                if message:
                    self._handle_response(message)
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Listener error: {e}")
                time.sleep(1)
    
    def _handle_response(self, message: AgentMessage):
        """Handle a response from an agent."""
        correlation_id = message.correlation_id
        
        # Update task status
        if correlation_id in self.tasks:
            task = self.tasks[correlation_id]
            
            if message.message_type == MessageType.TASK_RESPONSE:
                task.status = "completed"
                task.result = message.payload.get("result", message.payload)
            elif message.message_type == MessageType.ERROR:
                task.status = "failed"
                task.result = message.payload
            
            task.completed_at = datetime.utcnow().isoformat()
        
        # Call handler if registered
        if correlation_id in self.response_handlers:
            handler = self.response_handlers.pop(correlation_id)
            handler(message)
    
    def submit_task(
        self,
        target: AgentType,
        task_type: TaskType,
        payload: dict,
        priority: Priority = Priority.MEDIUM,
        on_complete: Callable = None
    ) -> str:
        """
        Submit a task to an agent.
        
        Returns:
            correlation_id for tracking
        """
        message = AgentMessage(
            message_type=MessageType.TASK_REQUEST,
            source_agent=AgentType.ORCHESTRATOR,
            target_agent=target,
            task_type=task_type,
            payload=payload,
            priority=priority
        )
        
        # Track task
        task = TaskStatus(
            task_id=message.message_id,
            task_type=task_type,
            target_agent=target
        )
        self.tasks[message.message_id] = task
        message.correlation_id = message.message_id
        
        # Register callback
        if on_complete:
            self.response_handlers[message.message_id] = on_complete
        
        # Send
        if self.mq.send_message(message):
            task.status = "processing"
            return message.message_id
        else:
            task.status = "failed"
            return ""
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a task."""
        return self.tasks.get(task_id)
    
    def wait_for_task(self, task_id: str, timeout: int = 60) -> Optional[dict]:
        """Wait for a task to complete."""
        start = time.time()
        
        while time.time() - start < timeout:
            task = self.tasks.get(task_id)
            if task and task.status in ["completed", "failed"]:
                return task.result
            time.sleep(0.5)
        
        return None
    
    def submit_and_wait(
        self,
        target: AgentType,
        task_type: TaskType,
        payload: dict,
        timeout: int = 60
    ) -> Optional[dict]:
        """Submit a task and wait for result."""
        task_id = self.submit_task(target, task_type, payload)
        if not task_id:
            return None
        return self.wait_for_task(task_id, timeout)
    
    def submit_workflow(
        self,
        workflow: list[dict],
        initial_input: dict
    ) -> str:
        """
        Submit a multi-agent workflow.
        
        Args:
            workflow: List of {"agent": AgentType, "task": TaskType, "transform": fn}
            initial_input: Starting payload
        
        Returns:
            workflow_id
        """
        # TODO: Implement full workflow engine
        # For now, just submit to first agent
        if not workflow:
            return ""
        
        first = workflow[0]
        return self.submit_task(
            target=AgentType(first["agent"]) if isinstance(first["agent"], str) else first["agent"],
            task_type=TaskType(first["task"]) if isinstance(first["task"], str) else first["task"],
            payload={
                "input": initial_input,
                "workflow": workflow,
                "step": 0
            }
        )
    
    def check_agent_health(self) -> dict[str, str]:
        """Check health of all agents."""
        health = {}
        
        for agent_type in [AgentType.LOCAL_CLAUDE, AgentType.LOCAL_OPENAI, AgentType.CLOUD_GEMINI]:
            # Send heartbeat
            message = AgentMessage(
                message_type=MessageType.HEARTBEAT,
                source_agent=AgentType.ORCHESTRATOR,
                target_agent=agent_type,
                payload={}
            )
            self.mq.send_message(message)
        
        # Check queue stats as proxy for health
        stats = self.mq.get_queue_stats()
        
        for agent, info in stats.items():
            if info.get("consumers", 0) > 0:
                health[agent] = "healthy"
            else:
                health[agent] = "no_consumers"
        
        return health
    
    def get_all_tasks(self) -> list[TaskStatus]:
        """Get all tracked tasks."""
        return list(self.tasks.values())
    
    def clear_completed_tasks(self):
        """Remove completed tasks from memory."""
        self.tasks = {
            k: v for k, v in self.tasks.items()
            if v.status not in ["completed", "failed"]
        }


# ============== CLI INTERFACE ==============

def main():
    """Command-line interface for orchestrator."""
    orchestrator = Orchestrator()
    
    if not orchestrator.connect():
        print("❌ Failed to connect to RabbitMQ")
        return
    
    orchestrator.start_listener()
    
    print("\n🎮 Federated Agent Orchestrator")
    print("Commands: health, submit, status, quit\n")
    
    try:
        while True:
            cmd = input("orchestrator> ").strip().lower()
            
            if cmd == "quit":
                break
            
            elif cmd == "health":
                health = orchestrator.check_agent_health()
                for agent, status in health.items():
                    icon = "✅" if status == "healthy" else "⚠️"
                    print(f"  {icon} {agent}: {status}")
            
            elif cmd == "status":
                tasks = orchestrator.get_all_tasks()
                if not tasks:
                    print("  No tasks")
                for task in tasks[-10:]:
                    print(f"  [{task.status}] {task.task_id[:8]}... → {task.target_agent.value}")
            
            elif cmd.startswith("submit"):
                # Quick test submit
                task_id = orchestrator.submit_task(
                    target=AgentType.LOCAL_CLAUDE,
                    task_type=TaskType.CODE_REVIEW,
                    payload={"code": "print('hello')", "language": "python"}
                )
                print(f"  Submitted: {task_id}")
            
            else:
                print("  Unknown command")
    
    except KeyboardInterrupt:
        pass
    
    finally:
        orchestrator.disconnect()
        print("\n👋 Goodbye")


if __name__ == "__main__":
    main()