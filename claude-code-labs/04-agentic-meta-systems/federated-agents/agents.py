"""
Federated Agents - Project 5.3
Local (Claude, OpenAI) and Cloud (Gemini) agents.
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from message_schema import (
    AgentMessage, AgentType, MessageType, TaskType, Priority
)
from message_queue import MessageQueue

# LLM Clients
from anthropic import Anthropic

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ============== BASE AGENT ==============

class BaseAgent(ABC):
    """Base class for all federated agents."""
    
    def __init__(self, agent_type: AgentType, mq: MessageQueue = None):
        self.agent_type = agent_type
        self.mq = mq
        self.running = False
    
    @abstractmethod
    def process_task(self, task_type: TaskType, payload: dict) -> dict:
        """Process a task and return result."""
        pass
    
    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle an incoming message."""
        if message.message_type == MessageType.TASK_REQUEST:
            try:
                result = self.process_task(message.task_type, message.payload)
                return message.create_response(result, success=True)
            except Exception as e:
                return message.create_response(
                    {"error": str(e)},
                    success=False
                )
        
        elif message.message_type == MessageType.HEARTBEAT:
            return AgentMessage(
                message_type=MessageType.STATUS_UPDATE,
                source_agent=self.agent_type,
                target_agent=message.source_agent,
                payload={"status": "alive", "agent": self.agent_type.value}
            )
        
        return None
    
    def start(self):
        """Start listening for messages."""
        if not self.mq:
            print("❌ No message queue configured")
            return
        
        self.running = True
        print(f"🚀 {self.agent_type.value} agent starting...")
        self.mq.consume(self.agent_type, self.handle_message)
    
    def send_task(
        self,
        target: AgentType,
        task_type: TaskType,
        payload: dict,
        correlation_id: str = ""
    ) -> bool:
        """Send a task to another agent."""
        if not self.mq:
            return False
        
        message = AgentMessage(
            message_type=MessageType.TASK_REQUEST,
            source_agent=self.agent_type,
            target_agent=target,
            task_type=task_type,
            payload=payload,
            correlation_id=correlation_id
        )
        
        return self.mq.send_message(message)


# ============== LOCAL CLAUDE AGENT ==============

class LocalClaudeAgent(BaseAgent):
    """
    Local agent using Claude API.
    
    Specialties:
    - Code review and analysis
    - Architecture design
    - Complex reasoning
    """
    
    def __init__(self, mq: MessageQueue = None):
        super().__init__(AgentType.LOCAL_CLAUDE, mq)
        self.client = Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    def process_task(self, task_type: TaskType, payload: dict) -> dict:
        """Process task using Claude."""
        
        if task_type == TaskType.CODE_REVIEW:
            return self._code_review(payload)
        elif task_type == TaskType.ARCHITECTURE_DESIGN:
            return self._architecture_design(payload)
        else:
            return self._general_task(task_type, payload)
    
    def _code_review(self, payload: dict) -> dict:
        """Review code for issues."""
        code = payload.get("code", "")
        language = payload.get("language", "python")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system="You are a senior code reviewer. Review code for bugs, security issues, and improvements. Be concise.",
            messages=[{
                "role": "user",
                "content": f"Review this {language} code:\n\n```{language}\n{code}\n```"
            }]
        )
        
        return {
            "review": response.content[0].text,
            "model": self.model,
            "tokens": response.usage.input_tokens + response.usage.output_tokens
        }
    
    def _architecture_design(self, payload: dict) -> dict:
        """Design system architecture."""
        requirements = payload.get("requirements", "")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system="You are a solutions architect. Design clean, scalable architectures.",
            messages=[{
                "role": "user",
                "content": f"Design architecture for:\n{requirements}"
            }]
        )
        
        return {
            "architecture": response.content[0].text,
            "model": self.model
        }
    
    def _general_task(self, task_type: TaskType, payload: dict) -> dict:
        """Handle general tasks."""
        prompt = payload.get("prompt", json.dumps(payload))
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "result": response.content[0].text,
            "task_type": task_type.value if task_type else "general",
            "model": self.model
        }


# ============== LOCAL OPENAI AGENT ==============

class LocalOpenAIAgent(BaseAgent):
    """
    Local agent using OpenAI ChatGPT API.
    
    Specialties:
    - Content generation
    - Creative writing
    - Brainstorming
    """
    
    def __init__(self, mq: MessageQueue = None):
        super().__init__(AgentType.LOCAL_OPENAI, mq)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.client = openai.OpenAI()
        self.model = "gpt-4o-mini"  # Cost-effective
    
    def process_task(self, task_type: TaskType, payload: dict) -> dict:
        """Process task using ChatGPT."""
        
        if task_type == TaskType.CONTENT_GENERATION:
            return self._generate_content(payload)
        elif task_type == TaskType.BRAINSTORMING:
            return self._brainstorm(payload)
        else:
            return self._general_task(task_type, payload)
    
    def _generate_content(self, payload: dict) -> dict:
        """Generate content."""
        topic = payload.get("topic", "")
        format_type = payload.get("format", "article")
        length = payload.get("length", "medium")
        
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": f"You are a content writer. Create {format_type}s. Length: {length}."},
                {"role": "user", "content": f"Write about: {topic}"}
            ]
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": self.model,
            "tokens": response.usage.total_tokens
        }
    
    def _brainstorm(self, payload: dict) -> dict:
        """Brainstorm ideas."""
        topic = payload.get("topic", "")
        count = payload.get("ideas", 5)
        
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": "You are a creative brainstorming partner."},
                {"role": "user", "content": f"Generate {count} creative ideas for: {topic}"}
            ]
        )
        
        return {
            "ideas": response.choices[0].message.content,
            "model": self.model
        }
    
    def _general_task(self, task_type: TaskType, payload: dict) -> dict:
        """Handle general tasks."""
        prompt = payload.get("prompt", json.dumps(payload))
        
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "result": response.choices[0].message.content,
            "model": self.model
        }


# ============== CLOUD GEMINI AGENT ==============

class CloudGeminiAgent(BaseAgent):
    """
    Cloud agent using Google Gemini API.
    
    Specialties:
    - Data analysis
    - Web research
    - Fact checking
    
    NOTE: This runs in GCP for the demo, but can also run locally.
    """
    
    def __init__(self, mq: MessageQueue = None):
        super().__init__(AgentType.CLOUD_GEMINI, mq)
        
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def process_task(self, task_type: TaskType, payload: dict) -> dict:
        """Process task using Gemini."""
        
        if task_type == TaskType.DATA_ANALYSIS:
            return self._analyze_data(payload)
        elif task_type == TaskType.WEB_RESEARCH:
            return self._research(payload)
        else:
            return self._general_task(task_type, payload)
    
    def _analyze_data(self, payload: dict) -> dict:
        """Analyze data."""
        data = payload.get("data", "")
        analysis_type = payload.get("analysis_type", "summary")
        
        response = self.model.generate_content(
            f"Analyze this data ({analysis_type}):\n{data}"
        )
        
        return {
            "analysis": response.text,
            "model": "gemini-1.5-flash"
        }
    
    def _research(self, payload: dict) -> dict:
        """Research a topic."""
        query = payload.get("query", "")
        
        response = self.model.generate_content(
            f"Research and summarize: {query}\n\nProvide key facts and insights."
        )
        
        return {
            "research": response.text,
            "model": "gemini-1.5-flash"
        }
    
    def _general_task(self, task_type: TaskType, payload: dict) -> dict:
        """Handle general tasks."""
        prompt = payload.get("prompt", json.dumps(payload))
        
        response = self.model.generate_content(prompt)
        
        return {
            "result": response.text,
            "model": "gemini-1.5-flash"
        }


# ============== AGENT FACTORY ==============

def create_agent(agent_type: AgentType, mq: MessageQueue = None) -> BaseAgent:
    """Factory to create agents."""
    agents = {
        AgentType.LOCAL_CLAUDE: LocalClaudeAgent,
        AgentType.LOCAL_OPENAI: LocalOpenAIAgent,
        AgentType.CLOUD_GEMINI: CloudGeminiAgent
    }
    
    agent_class = agents.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class(mq)


# ============== STANDALONE AGENT RUNNER ==============

def run_agent(agent_type: str):
    """Run a single agent (for Docker/CLI)."""
    from message_queue import MessageQueue
    
    agent_enum = AgentType(agent_type)
    
    # Connect to queue
    mq = MessageQueue()
    if not mq.connect():
        print("❌ Could not connect to RabbitMQ")
        return
    
    # Create and start agent
    agent = create_agent(agent_enum, mq)
    
    try:
        agent.start()
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped")
    finally:
        mq.disconnect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        agent_type = sys.argv[1]
        run_agent(agent_type)
    else:
        print("Usage: python agents.py <agent_type>")
        print("Agent types: local_claude, local_openai, cloud_gemini")