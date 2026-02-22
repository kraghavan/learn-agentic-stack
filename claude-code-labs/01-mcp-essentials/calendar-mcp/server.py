"""
Calendar MCP Server
A Model Context Protocol server for Google Calendar integration.

Protocol: JSON-RPC 2.0 over stdio
"""

import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from calendar_client import get_client, GoogleCalendarClient

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("calendar-mcp")


class CalendarMCPServer:
    """MCP Server for Google Calendar operations."""
    
    def __init__(self):
        self.name = "calendar-mcp"
        self.version = "1.0.0"
        self.client: GoogleCalendarClient = None
        
        # Tool definitions
        self.tools = [
            {
                "name": "authenticate",
                "description": "Authenticate with Google Calendar. Must be called first before other operations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_calendars",
                "description": "List all calendars the user has access to.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_events_today",
                "description": "Get all events for today.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID (default: primary)",
                            "default": "primary"
                        }
                    }
                }
            },
            {
                "name": "get_events_week",
                "description": "Get all events for the next 7 days.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID (default: primary)",
                            "default": "primary"
                        }
                    }
                }
            },
            {
                "name": "get_events_range",
                "description": "Get events within a specific date range.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format"
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID (default: primary)",
                            "default": "primary"
                        }
                    },
                    "required": ["start_date", "end_date"]
                }
            },
            {
                "name": "search_events",
                "description": "Search for events by keyword.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID (default: primary)",
                            "default": "primary"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_event",
                "description": "Create a new calendar event.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Event title"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time in ISO format (optional, defaults to start + 1 hour)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Event description"
                        },
                        "location": {
                            "type": "string",
                            "description": "Event location"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of attendee email addresses"
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID (default: primary)",
                            "default": "primary"
                        }
                    },
                    "required": ["summary", "start_time"]
                }
            },
            {
                "name": "delete_event",
                "description": "Delete a calendar event.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Event ID to delete"
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID (default: primary)",
                            "default": "primary"
                        }
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "find_free_slots",
                "description": "Find available time slots in the calendar.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Required duration in minutes",
                            "default": 60
                        },
                        "days_ahead": {
                            "type": "integer",
                            "description": "Number of days to search",
                            "default": 7
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID (default: primary)",
                            "default": "primary"
                        }
                    }
                }
            }
        ]
    
    def _ensure_client(self):
        """Ensure client is initialized and authenticated."""
        if self.client is None:
            self.client = get_client()
        if not self.client.is_authenticated():
            self.client.authenticate()
    
    # ============== Tool Handlers ==============
    
    def handle_authenticate(self, args: dict) -> str:
        """Handle authentication."""
        try:
            self.client = get_client()
            self.client.authenticate()
            return json.dumps({"success": True, "message": "Authenticated successfully"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def handle_list_calendars(self, args: dict) -> str:
        """List all calendars."""
        self._ensure_client()
        calendars = self.client.get_calendars()
        return json.dumps(calendars, indent=2)
    
    def handle_get_events_today(self, args: dict) -> str:
        """Get today's events."""
        self._ensure_client()
        calendar_id = args.get("calendar_id", "primary")
        events = self.client.get_events_today(calendar_id)
        return json.dumps(events, indent=2, default=str)
    
    def handle_get_events_week(self, args: dict) -> str:
        """Get this week's events."""
        self._ensure_client()
        calendar_id = args.get("calendar_id", "primary")
        events = self.client.get_events_week(calendar_id)
        return json.dumps(events, indent=2, default=str)
    
    def handle_get_events_range(self, args: dict) -> str:
        """Get events in a date range."""
        self._ensure_client()
        
        start_date = datetime.fromisoformat(args["start_date"])
        end_date = datetime.fromisoformat(args["end_date"])
        calendar_id = args.get("calendar_id", "primary")
        
        events = self.client.get_events(
            calendar_id=calendar_id,
            time_min=start_date,
            time_max=end_date
        )
        return json.dumps(events, indent=2, default=str)
    
    def handle_search_events(self, args: dict) -> str:
        """Search events."""
        self._ensure_client()
        
        query = args["query"]
        calendar_id = args.get("calendar_id", "primary")
        
        events = self.client.get_events(
            calendar_id=calendar_id,
            query=query,
            time_max=datetime.utcnow() + timedelta(days=365)
        )
        return json.dumps(events, indent=2, default=str)
    
    def handle_create_event(self, args: dict) -> str:
        """Create a new event."""
        self._ensure_client()
        
        start_time = datetime.fromisoformat(args["start_time"])
        end_time = None
        if args.get("end_time"):
            end_time = datetime.fromisoformat(args["end_time"])
        
        event = self.client.create_event(
            summary=args["summary"],
            start_time=start_time,
            end_time=end_time,
            description=args.get("description"),
            location=args.get("location"),
            attendees=args.get("attendees"),
            calendar_id=args.get("calendar_id", "primary")
        )
        return json.dumps(event, indent=2, default=str)
    
    def handle_delete_event(self, args: dict) -> str:
        """Delete an event."""
        self._ensure_client()
        
        success = self.client.delete_event(
            event_id=args["event_id"],
            calendar_id=args.get("calendar_id", "primary")
        )
        return json.dumps({"success": success})
    
    def handle_find_free_slots(self, args: dict) -> str:
        """Find free time slots."""
        self._ensure_client()
        
        duration = args.get("duration_minutes", 60)
        days = args.get("days_ahead", 7)
        calendar_id = args.get("calendar_id", "primary")
        
        time_max = datetime.utcnow() + timedelta(days=days)
        
        slots = self.client.find_free_slots(
            duration_minutes=duration,
            time_max=time_max,
            calendar_id=calendar_id
        )
        return json.dumps(slots, indent=2)
    
    # ============== MCP Protocol Handlers ==============
    
    def handle_initialize(self, params: dict) -> dict:
        """Handle initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
    
    def handle_tools_list(self, params: dict) -> dict:
        """Handle tools/list request."""
        return {"tools": self.tools}
    
    def handle_tools_call(self, params: dict) -> dict:
        """Handle tools/call request."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        logger.info(f"Tool call: {tool_name}")
        
        handlers = {
            "authenticate": self.handle_authenticate,
            "list_calendars": self.handle_list_calendars,
            "get_events_today": self.handle_get_events_today,
            "get_events_week": self.handle_get_events_week,
            "get_events_range": self.handle_get_events_range,
            "search_events": self.handle_search_events,
            "create_event": self.handle_create_event,
            "delete_event": self.handle_delete_event,
            "find_free_slots": self.handle_find_free_slots,
        }
        
        handler = handlers.get(tool_name)
        
        if handler:
            try:
                result = handler(arguments)
                return {"content": [{"type": "text", "text": result}]}
            except Exception as e:
                logger.error(f"Tool error: {e}")
                return {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True
                }
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            }
    
    def handle_request(self, request: dict) -> dict:
        """Route request to appropriate handler."""
        method = request.get("method", "")
        params = request.get("params", {})
        
        handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
        }
        
        handler = handlers.get(method)
        
        if handler:
            return handler(params)
        else:
            return {"error": {"code": -32601, "message": f"Method not found: {method}"}}
    
    def run(self):
        """Run the MCP server (stdio transport)."""
        logger.info("Starting Calendar MCP Server...")
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                result = self.handle_request(request)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result
                }
                
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response), flush=True)
            
            except Exception as e:
                logger.error(f"Server error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    server = CalendarMCPServer()
    server.run()
