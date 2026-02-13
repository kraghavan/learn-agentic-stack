# 🗃️ SQLite Query Agent

> **Project 1.2** from the Agentic AI Learning Pathway
> Natural Language → SQL using Claude AI

## Overview

Chat with any SQLite database using plain English. Claude converts your questions to SQL queries, executes them, and explains the results.

## Features

- [x] Load any SQLite database
- [x] Auto-detect schema (tables, columns, types)
- [x] Natural language → SQL conversion
- [x] Confidence scoring for generated queries
- [x] Execute queries with result display
- [x] Natural language result explanations
- [x] Query history tracking
- [x] CSV export
- [x] Streamlit UI with chat interface
- [x] Docker support

## Setup

### Option A: Local Development (Quick)

#### 1. Prerequisites

```bash
# Python 3.10+
python3 --version

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

#### 2. Install Dependencies

```bash
cd claude-code-labs/01-mcp-essentials/sqlite-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### 3. Create Sample Database

```bash
cd data
python create_sample_db.py
cd ..
```

#### 4. Run the App

```bash
streamlit run app/sqlite_agent.py
```

Open http://localhost:8501

---

### Option B: Docker (Recommended)

#### 1. Prerequisites

```bash
# Docker installed
docker --version

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

#### 2. Create Sample Database (First Time Only)

```bash
cd data
python3 create_sample_db.py
cd ..
```

You should see:
```
✅ Database created: sample_store.db
   - 10 customers
   - 10 products
   - 50 orders
```

#### 3. Build and Run

```bash
docker-compose up --build
```

#### 4. Access the UI

Open http://localhost:8501

#### Useful Docker Commands

```bash
# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Check container status
docker-compose ps
```

---

## Project Structure

```
sqlite-agent/
├── app/
│   └── sqlite_agent.py      # Main Streamlit app
├── data/
│   ├── create_sample_db.py  # Script to create test database
│   └── sample_store.db      # Generated test database
├── Dockerfile               # Container definition
├── docker-compose.yml       # Container orchestration
├── .dockerignore            # Files to exclude from build
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Usage

1. **Load database** from sidebar (auto-detects .db files in `data/` folder)
2. **View schema** - see tables and columns
3. **Ask questions** in plain English:
   - "How many customers do we have?"
   - "What are the top 5 products by total sales?"
   - "Show orders from last month"
   - "Which city has the most premium customers?"
   - "What's the average order value by product category?"
4. **Review** the generated SQL and confidence level
5. **Execute** and view results
6. **Export** as CSV if needed

## Example Questions

| Question | Generated SQL |
|----------|--------------|
| How many customers? | `SELECT COUNT(*) FROM customers;` |
| Top selling products | `SELECT p.name, SUM(o.quantity) as total_sold FROM products p JOIN orders o ON p.id = o.product_id GROUP BY p.id ORDER BY total_sold DESC LIMIT 5;` |
| Revenue last month | `SELECT SUM(total_amount) FROM orders WHERE order_date >= date('now', '-1 month');` |
| Premium customers by city | `SELECT city, COUNT(*) FROM customers WHERE is_premium = 1 GROUP BY city;` |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LOCAL / DOCKER                              │
│                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌───────────┐  │
│  │    Streamlit    │     │   Claude API    │     │  SQLite   │  │
│  │   (Port 8501)   │────▶│    (Remote)     │     │   (.db)   │  │
│  │       UI        │     │   Brain/LLM     │     │   File    │  │
│  └────────┬────────┘     └─────────────────┘     └─────┬─────┘  │
│           │                                            │        │
│           └────────────── Python ──────────────────────┘        │
│                      (sqlite_agent.py)                          │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
1. User asks question in plain English
2. Claude API converts question → SQL (with schema context)
3. Python executes SQL against SQLite file
4. Results displayed in Streamlit UI
```

### Docker Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        YOUR MAC                                  │
│                                                                  │
│   Browser ──────────▶ localhost:8501                            │
│                              │                                   │
│                              │ port mapping                      │
│                              ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 DOCKER CONTAINER                         │   │
│   │                                                          │   │
│   │   Streamlit (0.0.0.0:8501) ◀──▶ Claude API (remote)     │   │
│   │         │                                                │   │
│   │         ▼                                                │   │
│   │   /app/data/sample_store.db                             │   │
│   │         │                                                │   │
│   └─────────┼────────────────────────────────────────────────┘   │
│             │ volume mount                                       │
│             ▼                                                    │
│   ./data/sample_store.db  ← File on YOUR Mac (persists!)        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Learning Outcomes

- ✅ Schema extraction from SQLite
- ✅ Prompt engineering for SQL generation
- ✅ Structured output (JSON) from Claude
- ✅ Confidence scoring
- ✅ Error handling for SQL execution
- ✅ Chat history for context
- ✅ Data visualization with pandas
- ✅ Docker containerization
- ✅ Volume mounts for data persistence

---

## Security Notes

⚠️ This is a learning project. For production:
- Never expose to untrusted users (SQL injection risk)
- Use read-only database connections
- Implement query validation
- Add rate limiting

---

## Troubleshooting

### Database not found
```bash
# Create the database first
cd data && python3 create_sample_db.py && cd ..
```

### Docker container won't start
```bash
# Restart Docker Desktop, then:
docker-compose down
docker-compose up --build
```

### API key not working
```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Set it
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Port 8501 already in use
```bash
# Find and kill the process
lsof -i :8501
kill -9 <PID>

# Or use a different port
docker-compose down
# Edit docker-compose.yml: ports: "8502:8501"
docker-compose up
```

---

## Next Steps

After completing this project:
1. Add query caching
2. Support multiple databases simultaneously
3. Add visualization (charts from query results)
4. Implement query suggestions based on schema

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*