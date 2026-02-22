"""
Structured Logger
JSON-formatted logging for agent observability.
Logs are picked up by Promtail and sent to Loki.
"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Optional
from pathlib import Path


# Log directory
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "agent.log"


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class StructuredLogger:
    """Logger that outputs structured JSON logs."""
    
    def __init__(self, name: str = "agent"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # File handler
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)
            
            # Console handler (optional, for development)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(console_handler)
    
    def _log(self, level: int, message: str, **kwargs):
        """Log with extra fields."""
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            message,
            (),
            None
        )
        record.extra_fields = kwargs
        self.logger.handle(record)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    # ============== Agent-Specific Log Methods ==============
    
    def log_api_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool = True,
        error: str = None
    ):
        """Log an API call."""
        cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)
        
        self.info(
            "API call completed",
            event="api_call",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=round(cost, 6),
            success=success,
            error=error
        )
    
    def log_tool_use(
        self,
        tool: str,
        latency_ms: float,
        success: bool = True,
        error: str = None
    ):
        """Log a tool invocation."""
        level = logging.INFO if success else logging.ERROR
        
        self._log(
            level,
            f"Tool '{tool}' executed",
            event="tool_use",
            tool=tool,
            latency_ms=round(latency_ms, 2),
            success=success,
            error=error
        )
    
    def log_memory_operation(
        self,
        operation: str,
        collection: str,
        latency_ms: float,
        result_count: int = 0
    ):
        """Log a memory operation."""
        self.info(
            f"Memory {operation}",
            event="memory_operation",
            operation=operation,
            collection=collection,
            latency_ms=round(latency_ms, 2),
            result_count=result_count
        )
    
    def log_session_start(self, session_id: str, user_info: dict = None):
        """Log session start."""
        self.info(
            "Session started",
            event="session_start",
            session_id=session_id,
            user_info=user_info
        )
    
    def log_session_end(
        self,
        session_id: str,
        duration_seconds: float,
        message_count: int
    ):
        """Log session end."""
        self.info(
            "Session ended",
            event="session_end",
            session_id=session_id,
            duration_seconds=round(duration_seconds, 2),
            message_count=message_count
        )
    
    def log_user_message(self, session_id: str, message_preview: str):
        """Log a user message (truncated for privacy)."""
        self.debug(
            "User message received",
            event="user_message",
            session_id=session_id,
            message_preview=message_preview[:100] + "..." if len(message_preview) > 100 else message_preview
        )
    
    def log_agent_response(
        self,
        session_id: str,
        latency_ms: float,
        tokens: int
    ):
        """Log an agent response."""
        self.debug(
            "Agent response sent",
            event="agent_response",
            session_id=session_id,
            latency_ms=round(latency_ms, 2),
            tokens=tokens
        )


# Singleton instance
_logger = None

def get_logger(name: str = "agent") -> StructuredLogger:
    """Get or create the structured logger."""
    global _logger
    if _logger is None:
        _logger = StructuredLogger(name)
    return _logger


if __name__ == "__main__":
    # Test
    logger = get_logger()
    
    logger.info("Application started", version="1.0.0")
    logger.log_api_call(
        model="claude-sonnet-4-20250514",
        input_tokens=100,
        output_tokens=200,
        latency_ms=450.5,
        success=True
    )
    logger.log_tool_use(
        tool="web_search",
        latency_ms=230.0,
        success=True
    )
    logger.warning("High latency detected", latency_ms=5000)
    
    print(f"Logs written to: {LOG_FILE}")
