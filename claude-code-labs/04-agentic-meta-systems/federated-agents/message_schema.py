"""
Message Schema - Project 5.3
Standard message format for federated agent communication via RabbitMQ.
"""

import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from enum import Enum


class MessageType(str, Enum):
    """Types of messages agents can send."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class AgentType(str, Enum):
    """Types of agents in the federated system."""
    LOCAL_CLAUDE = "local_claude"       # Mac Mini - Claude API
    LOCAL_OPENAI = "local_openai"       # Mac Mini - ChatGPT API
    CLOUD_GEMINI = "cloud_gemini"       # GCP - Gemini API
    ORCHESTRATOR = "orchestrator"       # Control plane


class TaskType(str, Enum):
    """Tasks agents can perform."""
    # Claude specialties (reasoning, analysis)
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DESIGN = "architecture_design"
    
    # ChatGPT specialties (creative, conversational)
    CONTENT_GENERATION = "content_generation"
    BRAINSTORMING = "brainstorming"
    
    # Gemini specialties (multimodal, data)
    DATA_ANALYSIS = "data_analysis"
    WEB_RESEARCH = "web_research"
    
    # Collaborative
    MULTI_AGENT_TASK = "multi_agent_task"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AgentMessage:
    """
    Standard message format for agent-to-agent communication.
    
    Example:
    {
        "message_id": "550e8400-e29b-41d4-a716-446655440000",
        "message_type": "task_request",
        "source_agent": "orchestrator",
        "target_agent": "local_claude",
        "task_type": "code_review",
        "payload": {
            "code": "def hello(): print('world')",
            "language": "python"
        },
        "correlation_id": "job-123",
        "priority": "medium",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """
    message_type: MessageType
    source_agent: AgentType
    target_agent: AgentType
    payload: dict
    task_type: Optional[TaskType] = None
    
    # Auto-generated
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    # Tracking
    correlation_id: str = ""
    priority: Priority = Priority.MEDIUM
    retry_count: int = 0
    
    def to_json(self) -> str:
        """Serialize for RabbitMQ."""
        data = {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "source_agent": self.source_agent.value,
            "target_agent": self.target_agent.value,
            "task_type": self.task_type.value if self.task_type else None,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AgentMessage":
        """Deserialize from RabbitMQ."""
        data = json.loads(json_str)
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["message_type"]),
            source_agent=AgentType(data["source_agent"]),
            target_agent=AgentType(data["target_agent"]),
            task_type=TaskType(data["task_type"]) if data.get("task_type") else None,
            payload=data["payload"],
            correlation_id=data.get("correlation_id", ""),
            priority=Priority(data.get("priority", "medium")),
            timestamp=data.get("timestamp", ""),
            retry_count=data.get("retry_count", 0)
        )
    
    def create_response(self, result: dict, success: bool = True) -> "AgentMessage":
        """Create response to this message."""
        return AgentMessage(
            message_type=MessageType.TASK_RESPONSE if success else MessageType.ERROR,
            source_agent=self.target_agent,
            target_agent=self.source_agent,
            task_type=self.task_type,
            payload={"success": success, "result": result},
            correlation_id=self.correlation_id or self.message_id,
            priority=self.priority
        )


# ============== SAMPLE MESSAGES ==============

SAMPLE_MESSAGES = {
    "code_review_request": AgentMessage(
        message_type=MessageType.TASK_REQUEST,
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.LOCAL_CLAUDE,
        task_type=TaskType.CODE_REVIEW,
        payload={
            "code": """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price'] * item['qty']
    return total
""",
            "language": "python",
            "review_type": "security_and_performance"
        },
        correlation_id="job-001"
    ),
    
    "content_request": AgentMessage(
        message_type=MessageType.TASK_REQUEST,
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.LOCAL_OPENAI,
        task_type=TaskType.CONTENT_GENERATION,
        payload={
            "topic": "Benefits of microservices architecture",
            "format": "blog_post",
            "length": "500_words"
        },
        correlation_id="job-002"
    ),
    
    "research_request": AgentMessage(
        message_type=MessageType.TASK_REQUEST,
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.CLOUD_GEMINI,
        task_type=TaskType.WEB_RESEARCH,
        payload={
            "query": "Latest trends in AI agents 2024",
            "sources": 5,
            "summarize": True
        },
        correlation_id="job-003"
    ),
    
    "multi_agent_task": AgentMessage(
        message_type=MessageType.TASK_REQUEST,
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.LOCAL_CLAUDE,  # First agent in chain
        task_type=TaskType.MULTI_AGENT_TASK,
        payload={
            "task": "Create a technical blog post about Python async",
            "workflow": [
                {"agent": "local_claude", "action": "create_outline"},
                {"agent": "local_openai", "action": "write_draft"},
                {"agent": "cloud_gemini", "action": "fact_check"},
                {"agent": "local_claude", "action": "final_review"}
            ]
        },
        correlation_id="job-004"
    )
}


def print_sample_messages():
    """Print all sample messages as JSON."""
    print("=" * 60)
    print("SAMPLE AGENT MESSAGES")
    print("=" * 60)
    
    for name, msg in SAMPLE_MESSAGES.items():
        print(f"\n### {name.upper()} ###")
        print(json.dumps(json.loads(msg.to_json()), indent=2))


if __name__ == "__main__":
    print_sample_messages()