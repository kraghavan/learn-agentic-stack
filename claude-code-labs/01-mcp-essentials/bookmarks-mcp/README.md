# 🔖 Bookmarks MCP Server

> **Project 2.1** from the Agentic AI Learning Pathway
> Build a complete MCP server from scratch for browser bookmark management

## Overview

This project implements a **Model Context Protocol (MCP)** server that exposes browser bookmarks as tools. Claude Code (or any MCP-compatible client) can then search, list, and export your bookmarks using natural language.

**This is your first custom MCP server!**

## What is MCP?

The **Model Context Protocol** is a standard for connecting AI assistants to external tools and data sources. It uses JSON-RPC 2.0 over stdio (standard input/output).

```
┌──────────────┐    JSON-RPC    ┌──────────────┐    File I/O    ┌──────────────┐
│  Claude Code │◄──────────────►│  MCP Server  │◄──────────────►│   Browser    │
│   (Client)   │    (stdio)     │  (server.py) │                │  Bookmarks   │
└──────────────┘                └──────────────┘                └──────────────┘
```

## Features

- [x] Read bookmarks from Chrome, Firefox, Safari
- [x] Search by title and URL
- [x] List bookmark folders
- [x] Filter by folder
- [x] Export to JSON, HTML, Markdown
- [x] Bookmark statistics
- [x] MCP server with 6 tools
- [x] Streamlit UI for visual management

## Project Structure

```
bookmarks-mcp/
├── server.py               # MCP server implementation
├── browsers/
│   ├── __init__.py
│   ├── chrome.py           # Chrome bookmark parser
│   ├── firefox.py          # Firefox bookmark parser
│   └── safari.py           # Safari bookmark parser
├── schemas/
│   └── tools.json          # MCP tool definitions
├── app/
│   └── bookmarks_app.py    # Streamlit UI
├── requirements.txt
└── README.md
```

## Setup

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs/01-mcp-essentials
mkdir -p bookmarks-mcp/{browsers,schemas,app}
cd bookmarks-mcp

# Create __init__.py for browsers package
touch browsers/__init__.py
```

### Step 2: Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Test Browser Parsers

```bash
# Test Chrome
python -c "from browsers.chrome import parse_chrome_bookmarks; print(f'Chrome: {len(parse_chrome_bookmarks())} bookmarks')"

# Test Firefox
python -c "from browsers.firefox import parse_firefox_bookmarks; print(f'Firefox: {len(parse_firefox_bookmarks())} bookmarks')"

# Test Safari
python -c "from browsers.safari import parse_safari_bookmarks; print(f'Safari: {len(parse_safari_bookmarks())} bookmarks')"
```

### Step 4: Run Streamlit UI

```bash
streamlit run app/bookmarks_app.py
```

Open http://localhost:8501

---

## Connecting to Claude Code

### Option A: Global Configuration

Add to `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "bookmarks": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/Users/YOUR_USERNAME/learn-agentic-stack/claude-code-labs/01-mcp-essentials/bookmarks-mcp"
    }
  }
}
```

### Option B: Project Configuration

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "bookmarks": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "./bookmarks-mcp"
    }
  }
}
```

### Using with Claude Code

After configuration, start Claude Code:

```bash
claude
```

Then try commands like:

```
Search my bookmarks for "python"
```

```
List all my bookmark folders
```

```
Export my Chrome bookmarks to markdown
```

```
How many bookmarks do I have in Safari?
```

---

## MCP Tools Reference

### 1. list_bookmarks
List all bookmarks from specified browser(s).

**Input:**
```json
{
  "browser": "chrome" | "firefox" | "safari" | "all",
  "limit": 50
}
```

### 2. search_bookmarks
Search bookmarks by title or URL.

**Input:**
```json
{
  "query": "search term",
  "browser": "all",
  "search_titles": true,
  "search_urls": true
}
```

### 3. list_folders
List all bookmark folders.

**Input:**
```json
{
  "browser": "all"
}
```

### 4. get_bookmarks_by_folder
Get bookmarks in a specific folder.

**Input:**
```json
{
  "folder": "Bookmarks Bar/Tech",
  "browser": "all"
}
```

### 5. export_bookmarks
Export bookmarks to various formats.

**Input:**
```json
{
  "format": "json" | "html" | "markdown",
  "browser": "all"
}
```

### 6. get_bookmark_stats
Get bookmark statistics.

**Input:**
```json
{
  "browser": "all"
}
```

---

## Browser Data Locations (macOS)

| Browser | Path | Format |
|---------|------|--------|
| Chrome | `~/Library/Application Support/Google/Chrome/Default/Bookmarks` | JSON |
| Firefox | `~/Library/Application Support/Firefox/Profiles/*/places.sqlite` | SQLite |
| Safari | `~/Library/Safari/Bookmarks.plist` | Binary Plist |

---

## How MCP Works

### 1. Protocol
MCP uses **JSON-RPC 2.0** for communication:

```json
// Request
{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

// Response
{"jsonrpc": "2.0", "id": 1, "result": {"tools": [...]}}
```

### 2. Transport
Communication happens over **stdio** (standard input/output):
- Client writes JSON to server's stdin
- Server writes JSON to stdout
- Logs go to stderr

### 3. Lifecycle
```
1. Client starts server process
2. Client sends "initialize" request
3. Server responds with capabilities
4. Client can now call tools via "tools/call"
5. Server processes and returns results
```

---

## Learning Outcomes

- ✅ MCP protocol understanding (JSON-RPC 2.0)
- ✅ Tool schema definition
- ✅ Stdio transport implementation
- ✅ Multi-source data aggregation
- ✅ Browser data formats (JSON, SQLite, Plist)
- ✅ Export to multiple formats

---

## Testing the MCP Server

You can test the server manually:

```bash
# Start server
python server.py

# Then type JSON-RPC requests (one per line):
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_bookmark_stats", "arguments": {"browser": "all"}}}
```

Press Ctrl+D to exit.

---

## Troubleshooting

### "No bookmarks found"
- Make sure the browser has been used and has bookmarks
- Check file permissions for bookmark files
- Firefox must be closed (it locks the database)

### "Module not found" errors
- Make sure `browsers/__init__.py` exists
- Check you're in the right directory
- Activate virtual environment

### Claude Code doesn't see the tools
- Verify `config.json` path is correct
- Restart Claude Code after config changes
- Check server logs for errors

---

## Next Steps

After completing this project:
1. Add bookmark creation/deletion (write operations)
2. Add bookmark syncing between browsers
3. Create a Chrome extension interface
4. Add AI-powered bookmark categorization

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
