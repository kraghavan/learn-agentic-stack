# ✍️ Researcher + Writer Pipeline

> **Project 3.1** from the Agentic AI Learning Pathway
> Your first multi-agent system with A2A (Agent-to-Agent) handoff

## Overview

This project demonstrates **multi-agent orchestration** - two specialized AI agents working together to produce better output than either could alone.

**Spoiler:** It's simpler than you think!

## What "Multi-Agent" Really Means

```
"Multi-Agent" = Multiple Claude calls with different system prompts
"A2A Handoff"  = Structured JSON output from one → input to another
```

That's it. No special frameworks. No complex protocols. Just smart orchestration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              RESEARCHER + WRITER PIPELINE                   │
│                                                             │
│   User: "Write about AI trends in 2026"                    │
│                         │                                   │
│                         ▼                                   │
│   ┌─────────────────────────────────────┐                  │
│   │       🔍 RESEARCHER AGENT            │                  │
│   │                                      │                  │
│   │  System: "You are a research agent"  │                  │
│   │                                      │                  │
│   │  Tasks:                              │                  │
│   │  - Gather information                │                  │
│   │  - Extract key facts                 │                  │
│   │  - Identify sources                  │                  │
│   │  - Suggest article structure         │                  │
│   │                                      │                  │
│   │  Output: Structured JSON             │                  │
│   └──────────────────┬──────────────────┘                  │
│                      │                                      │
│                      ▼  HANDOFF                             │
│              ┌──────────────┐                               │
│              │  {           │                               │
│              │   "topic"    │                               │
│              │   "facts"    │                               │
│              │   "sources"  │                               │
│              │   "sections" │                               │
│              │  }           │                               │
│              └──────┬───────┘                               │
│                     │                                       │
│                     ▼                                       │
│   ┌─────────────────────────────────────┐                  │
│   │        ✍️ WRITER AGENT               │                  │
│   │                                      │                  │
│   │  System: "You are a writer agent"    │                  │
│   │                                      │                  │
│   │  Input: Research notes from above    │                  │
│   │                                      │                  │
│   │  Tasks:                              │                  │
│   │  - Create outline                    │                  │
│   │  - Write first draft                 │                  │
│   │  - Polish and refine                 │                  │
│   │                                      │                  │
│   │  Output: Final article               │                  │
│   └──────────────────┬──────────────────┘                  │
│                      │                                      │
│                      ▼                                      │
│               📄 Final Article                              │
└─────────────────────────────────────────────────────────────┘
```

## Features

- [x] Two specialized agents (Researcher + Writer)
- [x] Structured JSON handoff protocol
- [x] Pipeline visualization in UI
- [x] View handoff data between agents
- [x] Token usage and cost tracking
- [x] Download final article as Markdown

## Quick Start

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs
mkdir -p 02-agent-handshakes/researcher-writer
cd 02-agent-handshakes/researcher-writer
```

### Step 2: Copy Files

```
researcher-writer/
├── orchestrator.py      # Agent definitions + orchestration
├── pipeline_app.py      # Streamlit UI
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Step 3: Run Locally (Recommended for Learning)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key-here"
streamlit run pipeline_app.py
```

### Step 4: Or Use Docker

```bash
export ANTHROPIC_API_KEY="your-key-here"
docker-compose up --build
```

Open http://localhost:8501

---

## How It Works

### 1. The Orchestrator

```python
def run_pipeline(query):
    # Step 1: Research
    research_notes = run_researcher(query)
    
    # Step 2: Write (using research output)
    article = run_writer(research_notes)
    
    return article
```

That's the entire orchestration logic!

### 2. The Handoff Protocol

The Researcher outputs structured JSON:

```json
{
  "topic": "AI Trends in 2026",
  "summary": "A look at emerging AI technologies...",
  "key_facts": [
    "Multimodal AI is mainstream",
    "AI agents are widely deployed",
    "Energy efficiency is a key focus"
  ],
  "sources": [
    {"title": "MIT Tech Review", "snippet": "..."}
  ],
  "suggested_sections": [
    "Introduction",
    "Current State",
    "Emerging Trends",
    "Challenges",
    "Conclusion"
  ],
  "target_audience": "Tech professionals",
  "tone": "professional"
}
```

### 3. Agent Specialization

Each agent has a focused system prompt:

**Researcher:**
```
You are a Research Agent specialized in gathering and organizing information...
```

**Writer:**
```
You are a Writer Agent specialized in creating polished articles...
```

The key insight: **Different prompts = Different behaviors**

---

## Why Multi-Agent?

### Single Agent Approach
```
User → [One Agent Does Everything] → Output

Problems:
- Long, complex prompts
- Mixed responsibilities
- Hard to debug
- Less consistent output
```

### Multi-Agent Approach
```
User → [Researcher] → [Writer] → Output

Benefits:
- Focused prompts
- Clear responsibilities
- Easy to debug (check each stage)
- More consistent output
- Can swap/improve agents independently
```

---

## UI Features

### Pipeline Visualization
See the current stage at a glance:
```
📝 Query → 🔍 Researcher → ✍️ Writer → 📄 Article
   ✓           ✓            ⏳
```

### Tabs
- **Final Article** - The polished output
- **Research Notes** - What the Researcher found
- **Handoff Data** - Raw JSON passed between agents
- **Metrics** - Token usage and costs

---

## Learning Outcomes

- ✅ Agent specialization through prompts
- ✅ Structured handoff protocols (JSON)
- ✅ Pipeline orchestration patterns
- ✅ Multi-agent debugging (inspect each stage)
- ✅ Token usage across multiple calls

---

## Extending the Project

Ideas for enhancement:

1. **Add an Editor Agent** - Review and improve the Writer's output
2. **Parallel Research** - Multiple researchers for different aspects
3. **Feedback Loop** - Writer can ask Researcher for more info
4. **Memory** - Remember user preferences across sessions
5. **Web Search** - Add real web search to Researcher

---

## Key Code Patterns

### Defining an Agent

```python
AGENT_SYSTEM = """You are a [role] specialized in [task].

Your job is to:
1. [Task 1]
2. [Task 2]

OUTPUT FORMAT:
You MUST respond with ONLY a JSON object:
{...}
"""

def run_agent(input_data):
    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        system=AGENT_SYSTEM,
        messages=[{"role": "user", "content": input_data}]
    )
    return parse_response(response)
```

### Handoff Data Class

```python
@dataclass
class HandoffData:
    field1: str
    field2: list
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
```

### Orchestration

```python
def run_pipeline(query):
    result_1 = run_agent_1(query)      # Returns HandoffData
    result_2 = run_agent_2(result_1)   # Takes HandoffData
    return result_2
```

---

## Project Structure

```
researcher-writer/
├── orchestrator.py        # 🧠 The brain
│   ├── ResearchNotes      # Handoff data class
│   ├── ArticleDraft       # Output data class
│   ├── run_researcher()   # Agent 1
│   ├── run_writer()       # Agent 2
│   └── run_pipeline()     # Orchestrator
│
├── pipeline_app.py        # 🖥️ Streamlit UI
│   ├── Pipeline viz
│   ├── Stage management
│   └── Results display
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Next Steps

After mastering this pattern, you'll build:

- **3.2 Code Review Pipeline** - Multiple agents reviewing code
- **3.3 Debate Agents** - Agents that argue different positions
- **3.4 Task Decomposition** - Agent that breaks down complex tasks

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
