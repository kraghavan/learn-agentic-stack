# 🎯 Task Decomposition Orchestrator

> **Project 3.4** from the Agentic AI Learning Pathway
> Hierarchical pattern: Master agent delegates to specialized workers

## Overview

A master orchestrator agent breaks down complex tasks into subtasks and delegates them to specialized worker agents. This is the **hierarchical multi-agent pattern** - the foundation of sophisticated AI systems.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              TASK DECOMPOSITION ORCHESTRATOR                    │
│                                                                 │
│   Complex Task: "Create a technical blog post about..."        │
│                         │                                       │
│                         ▼                                       │
│   ┌──────────────────────────────────────────────┐             │
│   │            🎯 ORCHESTRATOR                    │             │
│   │               (Planner)                       │             │
│   │                                               │             │
│   │   "Break this into subtasks and assign       │             │
│   │    to appropriate workers"                    │             │
│   └──────────────────┬───────────────────────────┘             │
│                      │                                          │
│          ┌───────────┼───────────┬───────────┐                 │
│          │           │           │           │                 │
│          ▼           ▼           ▼           ▼                 │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│   │🔍Research│ │💻 Code   │ │✍️ Write  │ │📊Analyze│         │
│   │  Worker  │ │ Worker   │ │ Worker   │ │ Worker  │         │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘         │
│        │            │            │            │                │
│        └────────────┴─────┬──────┴────────────┘                │
│                           │                                     │
│                           ▼                                     │
│   ┌──────────────────────────────────────────────┐             │
│   │            🎯 ORCHESTRATOR                    │             │
│   │              (Aggregator)                     │             │
│   │                                               │             │
│   │   "Combine all results into final output"    │             │
│   └──────────────────┬───────────────────────────┘             │
│                      │                                          │
│                      ▼                                          │
│               📄 Final Output                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- [x] Automatic task decomposition
- [x] Worker type assignment (research, code, write, analyze, summarize)
- [x] Dependency management between subtasks
- [x] Parallel execution of independent tasks
- [x] Result aggregation into coherent output
- [x] Task tree visualization
- [x] Progress tracking

## Quick Start

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs/02-agent-handshakes
mkdir -p task-orchestrator
cd task-orchestrator
```

### Step 2: Copy Files

```
task-orchestrator/
├── task_orchestrator.py     → task_orchestrator.py
├── task_app.py              → task_app.py
├── requirements.txt         ← task_requirements.txt
├── Dockerfile               ← task_Dockerfile
├── docker-compose.yml       ← task_docker_compose.yml
└── README.md
```

### Step 3: Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
streamlit run task_app.py
```

### Step 4: Or Use Docker

```bash
export ANTHROPIC_API_KEY="your-key"
docker-compose up --build
```

Open http://localhost:8501

---

## Sample Tasks Included

- Create a technical blog post about microservices architecture
- Research top JavaScript frameworks and write a recommendation guide
- Build a REST API design document
- Create a project proposal for a mobile app
- Write a comprehensive guide to Docker containerization

---

## Worker Types

### 🔍 Research Worker
**Purpose:** Gather information and facts
- Searches for relevant data
- Organizes findings
- Cites sources

### 💻 Code Worker
**Purpose:** Write or analyze code
- Implements functionality
- Follows best practices
- Includes documentation

### ✍️ Write Worker
**Purpose:** Create written content
- Drafts articles, docs, guides
- Matches tone and style
- Structures content logically

### 📊 Analyze Worker
**Purpose:** Analyze information
- Identifies patterns
- Draws conclusions
- Provides insights

### 📝 Summarize Worker
**Purpose:** Condense information
- Extracts key points
- Maintains context
- Creates concise summaries

---

## How It Works

### Step 1: Planning

The Orchestrator analyzes the complex task and creates a plan:

```json
{
  "goal": "Create a comprehensive technical blog post",
  "subtasks": [
    {
      "id": "task_1",
      "title": "Research microservices patterns",
      "worker_type": "research",
      "dependencies": []
    },
    {
      "id": "task_2", 
      "title": "Write code examples",
      "worker_type": "code",
      "dependencies": ["task_1"]
    },
    {
      "id": "task_3",
      "title": "Create comparison table",
      "worker_type": "analyze",
      "dependencies": ["task_1"]
    },
    {
      "id": "task_4",
      "title": "Write final article",
      "worker_type": "write",
      "dependencies": ["task_2", "task_3"]
    }
  ],
  "execution_order": [
    ["task_1"],
    ["task_2", "task_3"],
    ["task_4"]
  ]
}
```

### Step 2: Execution

Tasks are executed respecting dependencies:

```
Phase 1: task_1 (research)
    │
    ▼
Phase 2: task_2 (code) ─┬─ task_3 (analyze)  [PARALLEL]
                        │
                        ▼
Phase 3: task_4 (write) ← receives task_2 + task_3 results
```

### Step 3: Aggregation

The Orchestrator combines all results:

```python
final_output = run_orchestrator_aggregate(
    original_task="Create a technical blog post...",
    goal="Comprehensive article with examples",
    subtask_results={
        "task_1": "Research findings...",
        "task_2": "Code examples...",
        "task_3": "Comparison table...",
        "task_4": "Draft article..."
    }
)
```

---

## Dependency Management

```python
@dataclass
class SubTask:
    id: str
    title: str
    description: str
    worker_type: WorkerType
    dependencies: list[str]  # Task IDs this depends on
    status: TaskStatus
    result: str
```

### Execution Logic

```python
for group in execution_order:
    for task_id in group:
        # Get results from dependencies
        dep_results = {
            dep_id: results[dep_id] 
            for dep_id in subtask.dependencies
        }
        
        # Worker receives dependency results
        result = run_worker(subtask, dependency_results=dep_results)
```

---

## Learning Outcomes

- ✅ Hierarchical agent patterns
- ✅ Task decomposition algorithms
- ✅ Dependency management
- ✅ Worker specialization
- ✅ Result aggregation
- ✅ Progress tracking patterns

---

## Comparison: All Multi-Agent Patterns

| Project | Pattern | Description |
|---------|---------|-------------|
| 3.1 | **Sequential** | A → B (linear handoff) |
| 3.2 | **Fan-out/Fan-in** | A ⟨+⟩ B → C (parallel then merge) |
| 3.3 | **Adversarial** | A ↔ B → C (opposing then synthesize) |
| **3.4** | **Hierarchical** | Orchestrator → Workers → Aggregator |

---

## The Hierarchical Pattern

```python
# The core pattern
def execute_complex_task(task):
    # 1. Orchestrator plans
    plan = orchestrator.plan(task)
    
    # 2. Workers execute
    results = {}
    for subtask in plan.subtasks:
        worker = get_worker(subtask.worker_type)
        results[subtask.id] = worker.execute(subtask)
    
    # 3. Orchestrator aggregates
    final = orchestrator.aggregate(results)
    
    return final
```

### Why Hierarchical?

1. **Scalability** - Add more workers as needed
2. **Specialization** - Each worker excels at one thing
3. **Flexibility** - Orchestrator adapts to any task
4. **Debugging** - Inspect each subtask independently
5. **Reusability** - Workers can be used across projects

---

## Extending the Project

Ideas for enhancement:

1. **Dynamic Workers** - Create workers on-the-fly based on task needs
2. **Worker Feedback** - Workers can request clarification from orchestrator
3. **Quality Checks** - Add a reviewer worker to check outputs
4. **Caching** - Cache worker results for similar subtasks
5. **Human-in-the-Loop** - Allow user approval between phases

---

## TIER 3 Complete! 🎉

You've now built all four multi-agent patterns:

| Pattern | Project | What You Learned |
|---------|---------|------------------|
| Sequential | 3.1 Researcher + Writer | Linear handoffs |
| Fan-out/Fan-in | 3.2 Code Review | Parallel execution |
| Adversarial | 3.3 Debate Agents | Opposing viewpoints |
| Hierarchical | 3.4 Task Orchestrator | Delegation & aggregation |

**Next:** TIER 4 - Production Deployment (CI/CD, Monitoring, Scale)

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
