# 📅 Calendar MCP Server

> **Project 2.2** from the Agentic AI Learning Pathway
> OAuth + Google Calendar API integration with natural language scheduling

## Overview

A custom MCP server that integrates with Google Calendar. Features OAuth 2.0 authentication, event management, and natural language event creation using Claude.

## Features

- [x] OAuth 2.0 authentication flow
- [x] List user's calendars
- [x] Get events (today, week, month, custom range)
- [x] Search events by keyword
- [x] Create events with attendees
- [x] Delete events
- [x] Find free time slots
- [x] Natural language event parsing
- [x] Streamlit UI

## Project Structure

```
calendar-mcp/
├── calendar_client.py      # Google Calendar API wrapper
├── server.py               # MCP server implementation
├── app/
│   └── calendar_app.py     # Streamlit UI
├── schemas/
│   └── tools.json          # MCP tool definitions
├── credentials.json        # OAuth credentials (YOU ADD THIS)
├── token.pickle            # Auth token (auto-generated)
├── requirements.txt
└── README.md
```

## Setup

### Step 1: Google Cloud Setup

**1. Create Project**
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project (or select existing)

**2. Enable Google Calendar API**
- Go to "APIs & Services" → "Library"
- Search "Google Calendar API"
- Click "Enable"

**3. Configure OAuth Consent Screen**
- Go to "APIs & Services" → "OAuth consent screen"
- Choose "External" user type
- Fill in app name, support email
- Add scope: `https://www.googleapis.com/auth/calendar`
- Click through to complete setup

**4. Add Yourself as Test User (Required!)**
- Go to "APIs & Services" → "OAuth consent screen"
- Scroll down to **"Test users"** section
- Click **"+ ADD USERS"**
- Enter your Gmail address
- Click **Save**

> ⚠️ Without this step, you'll get "Error 403: access_denied"

**4. Create OAuth Credentials**
- Go to "APIs & Services" → "Credentials"
- Click "Create Credentials" → "OAuth client ID"
- Application type: **Desktop app**
- Name: "Calendar MCP"
- Click "Create"
- Click "Download JSON"
- Rename to `credentials.json`
- Move to `calendar-mcp/` folder

### Step 2: Install Dependencies

```bash
cd ~/learn-agentic-stack/claude-code-labs/01-mcp-essentials/calendar-mcp

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Set Anthropic API Key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Step 4: Run the App

```bash
streamlit run app/calendar_app.py
```

Open http://localhost:8501

### Step 5: Authenticate

1. Click "Connect Google Account" in the sidebar
2. A browser window opens for Google OAuth
3. Sign in and grant calendar access
4. You're connected!

---

## MCP Server Usage

### Add to Claude Code

Add to `~/.claude/config.json` or `.mcp.json`:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/calendar-mcp"
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `authenticate` | Connect to Google Calendar |
| `list_calendars` | List all user's calendars |
| `get_events_today` | Get today's events |
| `get_events_week` | Get this week's events |
| `get_events_range` | Get events in date range |
| `search_events` | Search by keyword |
| `create_event` | Create new event |
| `delete_event` | Delete an event |
| `find_free_slots` | Find available time |

### Example Commands in Claude Code

```
What's on my calendar today?
```

```
Schedule a meeting with alice@example.com tomorrow at 2pm
```

```
Find me a free 30-minute slot this week
```

```
Delete my 3pm meeting
```

---

## Natural Language Examples

The app uses Claude to parse natural language into event details:

| Input | Parsed |
|-------|--------|
| "Meeting with Bob tomorrow at 3pm" | Title: "Meeting with Bob", Tomorrow 3:00-4:00 PM |
| "Lunch with team Friday noon for 90 minutes" | Title: "Lunch with team", Friday 12:00-1:30 PM |
| "Call with alice@example.com next Monday 10am" | Title: "Call", Monday 10:00 AM, Attendee: alice@example.com |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CALENDAR MCP                              │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │  Streamlit   │      │  Claude API  │      │  Google   │  │
│  │     UI       │─────▶│  (NL parse)  │      │ Calendar  │  │
│  │  Port 8501   │      │              │      │   API     │  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
│         │                                          ▲        │
│         │              ┌──────────────┐            │        │
│         └─────────────▶│   calendar   │────────────┘        │
│                        │   _client    │   OAuth 2.0         │
│                        └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Learning Outcomes

- ✅ OAuth 2.0 flow implementation
- ✅ Google API client usage
- ✅ Token storage and refresh
- ✅ Date/time handling
- ✅ Natural language parsing with Claude
- ✅ MCP server with external API

---

## Troubleshooting

### "credentials.json not found"
- Download OAuth credentials from Google Cloud Console
- Ensure file is named exactly `credentials.json`
- Place in the `calendar-mcp/` folder

### "Address already in use" (port 8080 conflict)
- Find the process: `lsof -i :8080`
- Kill it: `kill -9 <PID>`
- Or change port in `calendar_client.py`: `flow.run_local_server(port=8090)`

### "Access blocked: This app's request is invalid" or "Error 403: access_denied"
- Go to OAuth consent screen in Google Cloud Console
- Scroll to **Test users** section
- Click **+ ADD USERS**
- Add your Gmail address
- Save and try again

### "Token expired"
- Delete `token.pickle`
- Re-authenticate

### "API not enabled"
- Go to Google Cloud Console
- Enable "Google Calendar API"

---

## Security Notes

- `credentials.json` contains your OAuth client secret - don't commit to git
- `token.pickle` contains your auth token - don't share
- Add both to `.gitignore`

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*