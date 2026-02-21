# 📝 Markdown Note Taker

> **Project 1.3** from the Agentic AI Learning Pathway
> AI-powered note taking with tags, search, and smart features

## Overview

A persistent note-taking app that stores notes as markdown files. Features include quick capture, tagging, search, daily notes, and AI-powered tools like auto-tagging, summarization, and finding related notes.

## Features

- [x] Quick capture to daily note
- [x] Create/edit/delete notes
- [x] YAML frontmatter for metadata
- [x] Tag extraction (manual + hashtags)
- [x] Tag cloud with filtering
- [x] Full-text search
- [x] Daily notes
- [x] AI: Auto-suggest tags
- [x] AI: Summarize note
- [x] AI: Find related notes
- [x] AI: Expand/improve note
- [x] Markdown rendering
- [x] Docker support

## Setup

### Option A: Local Development

```bash
cd claude-code-labs/01-mcp-essentials/markdown-notes

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run
streamlit run app/notes_app.py
```

### Option B: Docker

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Build and run
docker-compose up --build
```

Open http://localhost:8502

## Project Structure

```
markdown-notes/
├── app/
│   └── notes_app.py         # Main Streamlit app
├── notes/                   # Your notes stored here (persisted)
│   ├── daily-2026-02-12.md
│   ├── my-note.md
│   └── ...
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Usage

### Quick Capture
Type a quick thought in the sidebar → Click "Add to Daily Note" → Appended to today's note

### Create Note
1. Click "➕ New Note"
2. Enter title, tags, content
3. Optionally click "🤖 AI Suggest Tags"
4. Save

### Search & Filter
- Use search box to find notes by content
- Click tags to filter by tag

### AI Tools (right sidebar)
- **Summarize** - Get a 2-3 sentence summary
- **Find Related** - Discover similar notes
- **Expand** - AI helps expand your note based on instruction

## Note Format

Notes are stored as markdown with YAML frontmatter:

```markdown
---
title: My Note Title
created: 2026-02-12 14:30
tags: [python, learning, ideas]
---

# My Note Title

Your content here...

You can also use #hashtags inline!
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MARKDOWN NOTES                           │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │  Streamlit   │      │  Claude API  │      │  Notes/   │  │
│  │     UI       │─────▶│  (AI tools)  │      │   *.md    │  │
│  │  Port 8502   │      │              │      │  (files)  │  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
│         │                                          ▲        │
│         │                                          │        │
│         └──────────── Python I/O ──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Learning Outcomes

- ✅ File I/O with markdown
- ✅ YAML frontmatter parsing
- ✅ Tag extraction (regex)
- ✅ Full-text search
- ✅ Session state management
- ✅ AI-powered features
- ✅ Structured JSON output from Claude
- ✅ Docker containerization

## Example Workflow

1. Open app → See daily note option
2. Quick capture: "Remember to review PR #42"
3. Create detailed note: "Code Review Checklist"
4. AI suggests tags: `code-review`, `process`, `checklist`
5. Later, search "review" → Find both notes
6. Click "Find Related" → Discover connections

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
