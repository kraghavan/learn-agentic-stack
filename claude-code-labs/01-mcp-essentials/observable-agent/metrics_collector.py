"""
Metrics Collector
Collects and sends metrics to InfluxDB for agent observability.
"""

import os
import time
from datetime import datetime
from typing import Optional, Any
from functools import wraps
from contextlib import contextmanager

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


# InfluxDB settings
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "learn-agentic")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "agent-metrics")

# Cost per token (approximate for Claude)
COST_PER_INPUT_TOKEN = 0.000003  # $3 per 1M tokens
COST_PER_OUTPUT_TOKEN = 0.000015  # $15 per 1M tokens


class MetricsCollector:
    """Collects and sends metrics to InfluxDB."""
    
    def __init__(self):
        self.client = None
        self.write_api = None
        self._connect()
    
    def _connect(self):
        """Connect to InfluxDB."""
        try:
            self.client = InfluxDBClient(
                url=INFLUXDB_URL,
                token=INFLUXDB_TOKEN,
                org=INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        except Exception as e:
            print(f"Warning: Could not connect to InfluxDB: {e}")
            self.client = None
            self.write_api = None
    
    def is_connected(self) -> bool:
        """Check if connected to InfluxDB."""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def _write(self, point: Point):
        """Write a point to InfluxDB."""
        if self.write_api:
            try:
                self.write_api.write(bucket=INFLUXDB_BUCKET, record=point)
            except Exception as e:
                print(f"Warning: Failed to write metric: {e}")
    
    # ============== API Call Metrics ==============
    
    def record_api_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool = True,
        error: str = None
    ):
        """Record an API call to Claude."""
        total_tokens = input_tokens + output_tokens
        cost = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)
        
        point = (
            Point("api_call")
            .tag("model", model)
            .tag("success", str(success).lower())
            .field("input_tokens", input_tokens)
            .field("output_tokens", output_tokens)
            .field("total_tokens", total_tokens)
            .field("latency_ms", latency_ms)
            .field("cost_usd", cost)
        )
        
        if error:
            point = point.field("error", error)
        
        self._write(point)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost,
        }
    
    # ============== Tool Usage Metrics ==============
    
    def record_tool_use(
        self,
        tool_name: str,
        latency_ms: float,
        success: bool = True,
        error: str = None
    ):
        """Record a tool invocation."""
        point = (
            Point("tool_use")
            .tag("tool", tool_name)
            .tag("success", str(success).lower())
            .field("latency_ms", latency_ms)
            .field("count", 1)
        )
        
        if error:
            point = point.field("error", error)
        
        self._write(point)
    
    # ============== Memory Metrics ==============
    
    def record_memory_operation(
        self,
        operation: str,  # 'store', 'retrieve', 'hit', 'miss'
        collection: str,
        latency_ms: float,
        result_count: int = 0
    ):
        """Record a memory/vector DB operation."""
        point = (
            Point("memory_operation")
            .tag("operation", operation)
            .tag("collection", collection)
            .field("latency_ms", latency_ms)
            .field("result_count", result_count)
            .field("count", 1)
        )
        
        self._write(point)
    
    # ============== Error Tracking ==============
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        component: str = "agent"
    ):
        """Record an error."""
        point = (
            Point("error")
            .tag("type", error_type)
            .tag("component", component)
            .field("message", error_message)
            .field("count", 1)
        )
        
        self._write(point)
    
    # ============== Session Metrics ==============
    
    def record_session_event(
        self,
        session_id: str,
        event: str,  # 'start', 'end', 'message'
        metadata: dict = None
    ):
        """Record a session event."""
        point = (
            Point("session")
            .tag("session_id", session_id)
            .tag("event", event)
            .field("count", 1)
        )
        
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (int, float)):
                    point = point.field(key, value)
                else:
                    point = point.tag(key, str(value))
        
        self._write(point)
    
    # ============== Cost Tracking ==============
    
    def record_cost(
        self,
        amount_usd: float,
        category: str = "api",  # 'api', 'storage', 'compute'
        description: str = None
    ):
        """Record a cost event."""
        point = (
            Point("cost")
            .tag("category", category)
            .field("amount_usd", amount_usd)
        )
        
        if description:
            point = point.field("description", description)
        
        self._write(point)
    
    # ============== Query Methods ==============
    
    def get_total_cost(self, hours: int = 24) -> float:
        """Get total cost for the last N hours."""
        if not self.client:
            return 0.0
        
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r["_measurement"] == "api_call")
            |> filter(fn: (r) => r["_field"] == "cost_usd")
            |> sum()
        '''
        
        try:
            result = self.client.query_api().query(query, org=INFLUXDB_ORG)
            for table in result:
                for record in table.records:
                    return record.get_value() or 0.0
        except:
            pass
        
        return 0.0
    
    def get_api_stats(self, hours: int = 24) -> dict:
        """Get API call statistics for the last N hours."""
        if not self.client:
            return {}
        
        stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "success_rate": 0.0,
        }
        
        # This is a simplified version - full implementation would have multiple queries
        try:
            query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["_measurement"] == "api_call")
                |> filter(fn: (r) => r["_field"] == "total_tokens")
                |> count()
            '''
            result = self.client.query_api().query(query, org=INFLUXDB_ORG)
            for table in result:
                for record in table.records:
                    stats["total_calls"] = record.get_value() or 0
        except:
            pass
        
        return stats


# ============== Decorators & Utilities ==============

# Singleton instance
_collector = None

def get_collector() -> MetricsCollector:
    """Get or create the metrics collector singleton."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


@contextmanager
def track_api_call(model: str = "claude-sonnet-4-20250514"):
    """Context manager to track an API call."""
    collector = get_collector()
    start_time = time.time()
    result = {"success": True, "error": None, "input_tokens": 0, "output_tokens": 0}
    
    try:
        yield result
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000
        collector.record_api_call(
            model=model,
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
            latency_ms=latency_ms,
            success=result["success"],
            error=result["error"]
        )


@contextmanager
def track_tool(tool_name: str):
    """Context manager to track a tool invocation."""
    collector = get_collector()
    start_time = time.time()
    success = True
    error = None
    
    try:
        yield
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000
        collector.record_tool_use(
            tool_name=tool_name,
            latency_ms=latency_ms,
            success=success,
            error=error
        )


def track_function(name: str = None):
    """Decorator to track function execution as a tool."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tool_name = name or func.__name__
            with track_tool(tool_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test
    collector = get_collector()
    print(f"Connected to InfluxDB: {collector.is_connected()}")
    
    # Record a test metric
    collector.record_api_call(
        model="claude-sonnet-4-20250514",
        input_tokens=100,
        output_tokens=200,
        latency_ms=500,
        success=True
    )
    print("Test metric recorded!")
