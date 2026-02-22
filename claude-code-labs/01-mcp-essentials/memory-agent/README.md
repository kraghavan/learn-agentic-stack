# 🧠 Memory Agent with ChromaDB

> **Project 2.3** from the Agentic AI Learning Pathway
> Persistent conversational memory using vector embeddings

## Overview

Build an AI agent that **remembers**. This project uses ChromaDB (a vector database) to store conversation history and extracted facts, enabling the agent to recall relevant information across sessions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       MEMORY AGENT                               │
│                                                                  │
│   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐    │
│   │  Streamlit  │────▶│ Claude Agent │────▶│   ChromaDB   │    │
│   │  (Chat UI)  │     │  (Brain)     │     │ (Vector DB)  │    │
│   │  Port 8501  │     │              │     │  Port 8000   │    │
│   └─────────────┘     └──────────────┘     └──────────────┘    │
│          │                   │                    │             │
│          │                   ▼                    ▼             │
│          │            ┌──────────────┐     ┌──────────────┐    │
│          │            │   Response   │◀────│  Embeddings  │    │
│          │            └──────────────┘     │  + Retrieval │    │
│          │                                 └──────────────┘    │
│          │                                                      │
│          └─────────────── Docker Compose ──────────────────────│
└─────────────────────────────────────────────────────────────────┘
```

## Features

- [x] Persistent conversation memory
- [x] Automatic fact extraction from conversations
- [x] Semantic search for relevant history
- [x] Memory indicators in UI (shows what was remembered)
- [x] Session management
- [x] Memory management (clear session, clear all)
- [x] Docker Compose setup (one command to run everything)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Anthropic API key

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs/01-mcp-essentials
mkdir -p memory-agent
cd memory-agent
```

### Step 2: Copy Files

```
memory-agent/
├── memory_app.py           # Streamlit UI
├── memory_client.py        # ChromaDB client
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Step 3: Set API Key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Step 4: Run with Docker Compose

```bash
docker-compose up --build
```

That's it! 🎉

### Step 5: Open the App

```
http://localhost:8501
```

---

## How It Works

### 1. Message Storage

When you send a message:
```
User: "I'm working on a Python web app using FastAPI"
```

The message is:
1. Sent to Claude for a response
2. Stored in ChromaDB with embeddings
3. Analyzed for extractable facts

### 2. Fact Extraction

Claude extracts facts from conversations:
```json
[
  "User is working on a Python web app",
  "User is using FastAPI framework"
]
```

These are stored separately for quick retrieval.

### 3. Memory Retrieval

On your next message:
```
User: "How should I structure my project?"
```

The agent:
1. Searches ChromaDB for relevant past messages
2. Retrieves matching facts
3. Includes them in Claude's context
4. Generates a personalized response

### 4. Context Building

Claude receives a system prompt like:
```
## Known Facts About the User
- User is working on a Python web app
- User is using FastAPI framework

## Relevant Past Conversations
- [user] I'm working on a Python web app using FastAPI...
```

---

## Project Structure

```
memory-agent/
├── memory_app.py           # Main Streamlit application
├── memory_client.py        # ChromaDB wrapper (storage/retrieval)
├── Dockerfile              # App container definition
├── docker-compose.yml      # Orchestrates ChromaDB + App
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `chromadb` | 8000 | Vector database for embeddings |
| `memory-agent` | 8501 | Streamlit chat interface |

### Useful Commands

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Stop and remove data
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

---

## Memory Collections

ChromaDB stores two collections:

### 1. `conversations`
Stores all messages with metadata:
```json
{
  "content": "I'm working on a Python web app",
  "role": "user",
  "session_id": "abc123",
  "timestamp": "2026-02-12T14:30:00"
}
```

### 2. `facts`
Stores extracted knowledge:
```json
{
  "fact": "User prefers Python over JavaScript",
  "category": "user_preference",
  "confidence": 1.0,
  "source": "session:abc123"
}
```

---

## UI Features

### Chat Interface
- Standard chat with memory-aware responses
- Memory indicators showing what was recalled

### Memory Sidebar
- Connection status to ChromaDB
- Memory statistics (conversations, facts)
- Session management
- View stored facts
- Clear memory options

---

## Learning Outcomes

- ✅ Vector database concepts
- ✅ Embedding-based similarity search
- ✅ RAG (Retrieval-Augmented Generation) pattern
- ✅ Context window management
- ✅ Docker Compose orchestration
- ✅ Persistent storage with volumes

---

## Troubleshooting

### "Could not connect to ChromaDB"
```bash
# Check if ChromaDB is running
docker-compose ps

# View ChromaDB logs
docker-compose logs chromadb

# Restart services
docker-compose restart
```

### "No memories found"
- Have a few conversations first
- Memories are retrieved based on semantic similarity
- Try asking about topics you discussed before

### Port conflicts
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8501

# Change ports in docker-compose.yml if needed
```

### Reset everything
```bash
# Remove containers and volumes
docker-compose down -v

# Start fresh
docker-compose up --build
```

---

## Extending the Project

Ideas for enhancement:
1. **Memory importance scoring** - Prioritize certain memories
2. **Memory decay** - Older memories become less relevant
3. **Multi-user support** - Separate memory per user
4. **Memory visualization** - Graph of connected memories
5. **Export/import memory** - Backup and restore

---

## Local Development (without Docker)

If you prefer running locally:

```bash
# Terminal 1: Start ChromaDB
docker run -p 8000:8000 chromadb/chroma

# Terminal 2: Run the app
cd memory-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8000"

streamlit run memory_app.py
```

---

## API Reference

### MemoryClient

```python
from memory_client import get_memory_client

client = get_memory_client()

# Store a message
client.store_message("user", "Hello!", session_id="abc123")

# Get relevant history
history = client.get_relevant_history("What did I say?", n_results=5)

# Store a fact
client.store_fact("User likes Python", category="preference")

# Get relevant facts
facts = client.get_relevant_facts("programming languages")

# Clear session
client.forget_session("abc123")

# Clear everything
client.clear_all_memory()
```

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
