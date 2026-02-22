"""
Bookmarks MCP Server
A Model Context Protocol server for browser bookmark management.

This server exposes bookmark operations as MCP tools that can be used by
Claude Code or other MCP-compatible clients.

Protocol: JSON-RPC 2.0 over stdio
"""

import sys
import json
import logging
from typing import Any

# Import browser parsers
from browsers.chrome import parse_chrome_bookmarks, search_chrome_bookmarks, get_chrome_folders
from browsers.firefox import parse_firefox_bookmarks, search_firefox_bookmarks, get_firefox_folders
from browsers.safari import parse_safari_bookmarks, search_safari_bookmarks, get_safari_folders

# Configure logging to stderr (stdout is for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("bookmarks-mcp")


class BookmarksMCPServer:
    """MCP Server for browser bookmarks."""
    
    def __init__(self):
        self.name = "bookmarks-mcp"
        self.version = "1.0.0"
        
        # Tool definitions
        self.tools = [
            {
                "name": "list_bookmarks",
                "description": "List all bookmarks from specified browser(s). Returns bookmark titles, URLs, and folders.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox", "safari", "all"],
                            "description": "Which browser to read bookmarks from",
                            "default": "all"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of bookmarks to return",
                            "default": 50
                        }
                    }
                }
            },
            {
                "name": "search_bookmarks",
                "description": "Search bookmarks by title or URL across browser(s).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find in bookmark titles or URLs"
                        },
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox", "safari", "all"],
                            "description": "Which browser to search",
                            "default": "all"
                        },
                        "search_titles": {
                            "type": "boolean",
                            "description": "Search in bookmark titles",
                            "default": True
                        },
                        "search_urls": {
                            "type": "boolean",
                            "description": "Search in bookmark URLs",
                            "default": True
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_folders",
                "description": "List all bookmark folders from specified browser(s).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox", "safari", "all"],
                            "description": "Which browser to read folders from",
                            "default": "all"
                        }
                    }
                }
            },
            {
                "name": "get_bookmarks_by_folder",
                "description": "Get all bookmarks in a specific folder.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "folder": {
                            "type": "string",
                            "description": "Folder path to filter by"
                        },
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox", "safari", "all"],
                            "description": "Which browser to read from",
                            "default": "all"
                        }
                    },
                    "required": ["folder"]
                }
            },
            {
                "name": "export_bookmarks",
                "description": "Export bookmarks to various formats (JSON, HTML, or Markdown).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "html", "markdown"],
                            "description": "Export format",
                            "default": "json"
                        },
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox", "safari", "all"],
                            "description": "Which browser to export from",
                            "default": "all"
                        }
                    }
                }
            },
            {
                "name": "get_bookmark_stats",
                "description": "Get statistics about bookmarks (count by browser, folder distribution, etc.).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox", "safari", "all"],
                            "description": "Which browser to analyze",
                            "default": "all"
                        }
                    }
                }
            }
        ]
    
    def _get_bookmarks(self, browser: str = "all") -> list[dict]:
        """Get bookmarks from specified browser(s)."""
        bookmarks = []
        
        if browser in ["chrome", "all"]:
            bookmarks.extend(parse_chrome_bookmarks())
        
        if browser in ["firefox", "all"]:
            bookmarks.extend(parse_firefox_bookmarks())
        
        if browser in ["safari", "all"]:
            bookmarks.extend(parse_safari_bookmarks())
        
        return bookmarks
    
    def _search_bookmarks(
        self,
        query: str,
        browser: str = "all",
        search_titles: bool = True,
        search_urls: bool = True
    ) -> list[dict]:
        """Search bookmarks across browser(s)."""
        results = []
        
        if browser in ["chrome", "all"]:
            results.extend(search_chrome_bookmarks(
                query, search_titles=search_titles, search_urls=search_urls
            ))
        
        if browser in ["firefox", "all"]:
            results.extend(search_firefox_bookmarks(
                query, search_titles=search_titles, search_urls=search_urls
            ))
        
        if browser in ["safari", "all"]:
            results.extend(search_safari_bookmarks(
                query, search_titles=search_titles, search_urls=search_urls
            ))
        
        return results
    
    def _get_folders(self, browser: str = "all") -> list[dict]:
        """Get folder list from browser(s)."""
        folders = []
        
        if browser in ["chrome", "all"]:
            for f in get_chrome_folders():
                folders.append({"folder": f, "browser": "chrome"})
        
        if browser in ["firefox", "all"]:
            for f in get_firefox_folders():
                folders.append({"folder": f, "browser": "firefox"})
        
        if browser in ["safari", "all"]:
            for f in get_safari_folders():
                folders.append({"folder": f, "browser": "safari"})
        
        return folders
    
    def _export_bookmarks(self, browser: str = "all", format: str = "json") -> str:
        """Export bookmarks to specified format."""
        bookmarks = self._get_bookmarks(browser)
        
        if format == "json":
            return json.dumps(bookmarks, indent=2)
        
        elif format == "html":
            html = ['<!DOCTYPE NETSCAPE-Bookmark-file-1>']
            html.append('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">')
            html.append('<TITLE>Bookmarks</TITLE>')
            html.append('<H1>Bookmarks</H1>')
            html.append('<DL><p>')
            
            for bm in bookmarks:
                html.append(f'  <DT><A HREF="{bm["url"]}">{bm["title"]}</A>')
            
            html.append('</DL><p>')
            return '\n'.join(html)
        
        elif format == "markdown":
            md = ['# Bookmarks\n']
            
            # Group by folder
            by_folder = {}
            for bm in bookmarks:
                folder = bm.get("folder", "Unfiled")
                if folder not in by_folder:
                    by_folder[folder] = []
                by_folder[folder].append(bm)
            
            for folder, bms in sorted(by_folder.items()):
                md.append(f'\n## {folder}\n')
                for bm in bms:
                    md.append(f'- [{bm["title"]}]({bm["url"]})')
            
            return '\n'.join(md)
        
        return ""
    
    def _get_stats(self, browser: str = "all") -> dict:
        """Get bookmark statistics."""
        bookmarks = self._get_bookmarks(browser)
        
        stats = {
            "total": len(bookmarks),
            "by_browser": {},
            "by_folder": {},
            "top_domains": {}
        }
        
        for bm in bookmarks:
            # Count by browser
            b = bm.get("browser", "unknown")
            stats["by_browser"][b] = stats["by_browser"].get(b, 0) + 1
            
            # Count by folder
            f = bm.get("folder", "Unfiled")
            stats["by_folder"][f] = stats["by_folder"].get(f, 0) + 1
            
            # Extract domain
            url = bm.get("url", "")
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain:
                    stats["top_domains"][domain] = stats["top_domains"].get(domain, 0) + 1
            except:
                pass
        
        # Keep only top 10 domains
        stats["top_domains"] = dict(
            sorted(stats["top_domains"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return stats
    
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
        
        logger.info(f"Tool call: {tool_name} with args: {arguments}")
        
        try:
            if tool_name == "list_bookmarks":
                browser = arguments.get("browser", "all")
                limit = arguments.get("limit", 50)
                bookmarks = self._get_bookmarks(browser)[:limit]
                result = json.dumps(bookmarks, indent=2)
            
            elif tool_name == "search_bookmarks":
                query = arguments.get("query", "")
                browser = arguments.get("browser", "all")
                search_titles = arguments.get("search_titles", True)
                search_urls = arguments.get("search_urls", True)
                results = self._search_bookmarks(query, browser, search_titles, search_urls)
                result = json.dumps(results, indent=2)
            
            elif tool_name == "list_folders":
                browser = arguments.get("browser", "all")
                folders = self._get_folders(browser)
                result = json.dumps(folders, indent=2)
            
            elif tool_name == "get_bookmarks_by_folder":
                folder = arguments.get("folder", "")
                browser = arguments.get("browser", "all")
                bookmarks = self._get_bookmarks(browser)
                filtered = [b for b in bookmarks if folder.lower() in b.get("folder", "").lower()]
                result = json.dumps(filtered, indent=2)
            
            elif tool_name == "export_bookmarks":
                browser = arguments.get("browser", "all")
                fmt = arguments.get("format", "json")
                result = self._export_bookmarks(browser, fmt)
            
            elif tool_name == "get_bookmark_stats":
                browser = arguments.get("browser", "all")
                stats = self._get_stats(browser)
                result = json.dumps(stats, indent=2)
            
            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                    "isError": True
                }
            
            return {
                "content": [{"type": "text", "text": result}]
            }
        
        except Exception as e:
            logger.error(f"Tool error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
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
        logger.info("Starting Bookmarks MCP Server...")
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                logger.debug(f"Request: {request}")
                
                result = self.handle_request(request)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result
                }
                
                # Write response to stdout
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
    server = BookmarksMCPServer()
    server.run()
