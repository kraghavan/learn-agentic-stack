# ⚖️ Debate Agents

> **Project 3.3** from the Agentic AI Learning Pathway
> Adversarial pattern: Pro vs Con with balanced synthesis

## Overview

Three agents engage in structured debate, then a fourth synthesizes a balanced conclusion. This demonstrates **adversarial prompting** - using opposing viewpoints to generate more balanced, well-reasoned outputs.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DEBATE AGENTS                              │
│                                                                 │
│   Topic: "Remote work should be the default"                   │
│                         │                                       │
│                         ▼                                       │
│   ┌──────────────────────────────────────────────┐             │
│   │              ROUND 1                          │             │
│   │  🟢 Pro ─────────────▶ 🔴 Con                │             │
│   │  "Increases          "Reduces                │             │
│   │   productivity"       collaboration"         │             │
│   └──────────────────────────────────────────────┘             │
│                         │                                       │
│                         ▼                                       │
│   ┌──────────────────────────────────────────────┐             │
│   │              ROUND 2                          │             │
│   │  🟢 Pro ─────────────▶ 🔴 Con                │             │
│   │  "Async tools         "Culture suffers       │             │
│   │   solve collab"        without presence"     │             │
│   └──────────────────────────────────────────────┘             │
│                         │                                       │
│                         ▼                                       │
│   ┌──────────────────────────────────────────────┐             │
│   │              ROUND 3                          │             │
│   │  🟢 Pro ─────────────▶ 🔴 Con                │             │
│   │  "Work-life           "Blurred boundaries    │             │
│   │   balance"             hurt wellbeing"       │             │
│   └──────────────────────────────────────────────┘             │
│                         │                                       │
│                         ▼                                       │
│   ┌──────────────────────────────────────────────┐             │
│   │         ⚖️ SYNTHESIZER                        │             │
│   │                                               │             │
│   │  - Analyzes both sides fairly                │             │
│   │  - Identifies areas of agreement             │             │
│   │  - Notes unresolved tensions                 │             │
│   │  - Provides nuanced conclusion               │             │
│   └──────────────────────────────────────────────┘             │
│                         │                                       │
│                         ▼                                       │
│                📝 Balanced Analysis                             │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- [x] Pro and Con agents with distinct perspectives
- [x] Multi-round debates (configurable 1-5 rounds)
- [x] Turn-based coordination
- [x] Rebuttals reference opponent's arguments
- [x] Balanced synthesis with nuance
- [x] Sample topics included
- [x] Real-time debate visualization

## Quick Start

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs/02-agent-handshakes
mkdir -p debate-agents
cd debate-agents
```

### Step 2: Copy Files

```
debate-agents/
├── debate_orchestrator.py   → debate_orchestrator.py
├── debate_app.py            → debate_app.py  
├── requirements.txt         ← debate_requirements.txt
├── Dockerfile               ← debate_Dockerfile
├── docker-compose.yml       ← debate_docker_compose.yml
└── README.md
```

### Step 3: Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
streamlit run debate_app.py
```

### Step 4: Or Use Docker

```bash
export ANTHROPIC_API_KEY="your-key"
docker-compose up --build
```

Open http://localhost:8501

---

## Sample Topics Included

- Remote work should be the default for knowledge workers
- Social media has done more harm than good
- AI will create more jobs than it eliminates
- College degrees are overvalued
- Electric vehicles should replace gas cars by 2035
- Universal Basic Income is viable
- Space exploration funding should increase
- Crypto will replace traditional currency

---

## Agent Details

### 🟢 Pro Agent

**Purpose:** Argue IN FAVOR of the topic

**Behavior:**
- Makes compelling pro arguments
- Builds case across rounds
- Responds to Con's rebuttals
- Uses evidence and examples

**Output:**
```json
{
  "main_point": "Remote work increases productivity",
  "supporting_points": ["No commute time", "Fewer interruptions"],
  "evidence": ["Stanford study showed 13% productivity increase"],
  "rebuttal_to": "Collaboration can happen async via modern tools"
}
```

### 🔴 Con Agent

**Purpose:** Argue AGAINST the topic

**Behavior:**
- Challenges Pro's arguments
- Presents counter-evidence
- Finds weaknesses in Pro's logic
- Maintains consistent position

**Output:**
```json
{
  "main_point": "Remote work reduces team cohesion",
  "supporting_points": ["Spontaneous collaboration lost", "Culture harder to maintain"],
  "evidence": ["Yahoo and IBM reversed remote policies"],
  "rebuttal_to": "Productivity gains don't account for innovation loss"
}
```

### ⚖️ Synthesizer Agent

**Purpose:** Provide balanced analysis

**Behavior:**
- Fairly represents both sides
- Identifies common ground
- Acknowledges unresolved tensions
- Avoids false balance

**Output:**
```json
{
  "summary": "The debate reveals legitimate concerns on both sides...",
  "pro_strengths": ["Strong productivity evidence"],
  "con_strengths": ["Valid culture concerns"],
  "areas_of_agreement": ["Flexibility has value"],
  "key_tensions": ["Individual vs team optimization"],
  "nuanced_conclusion": "A hybrid approach may be optimal...",
  "recommendation": "Consider role-specific policies"
}
```

---

## Why Adversarial Prompting?

### Single Agent Problem

```
User: "Should we adopt remote work?"

Single Agent: "Yes, remote work is great because..."
             (Likely biased toward one view)
```

### Adversarial Solution

```
User: "Should we adopt remote work?"

Pro Agent: "Yes because..." (best pro arguments)
Con Agent: "No because..."  (best con arguments)
Synthesizer: "Considering both..." (balanced view)
```

### Benefits

1. **Better coverage** - Both sides explored thoroughly
2. **Stress-tested arguments** - Weak points exposed
3. **Reduced bias** - Not stuck in one perspective  
4. **Nuanced output** - Acknowledges complexity
5. **User empowerment** - Reader can decide for themselves

---

## Turn-Based Coordination

```python
def run_debate(topic, num_rounds):
    all_arguments = []
    
    for round in range(num_rounds):
        # Pro goes first, sees all previous arguments
        pro_arg = run_pro(topic, round, all_arguments)
        all_arguments.append(pro_arg)
        
        # Con responds, sees Pro's new argument
        con_arg = run_con(topic, round, all_arguments)
        all_arguments.append(con_arg)
    
    # Synthesizer sees complete debate
    synthesis = run_synthesizer(topic, all_arguments)
    
    return synthesis
```

**Key insight:** Each agent sees the full history, enabling real rebuttals.

---

## Learning Outcomes

- ✅ Adversarial prompting patterns
- ✅ Turn-based agent coordination
- ✅ Argument/rebuttal dynamics
- ✅ Synthesis from opposing views
- ✅ Balanced output generation
- ✅ State management across rounds

---

## Comparison: Multi-Agent Patterns

| Pattern | Project | Description |
|---------|---------|-------------|
| **Sequential** | 3.1 | A → B (linear handoff) |
| **Fan-out/Fan-in** | 3.2 | A ⟨+⟩ B → C (parallel then merge) |
| **Adversarial** | 3.3 | A ↔ B → C (opposing then synthesize) |
| **Hierarchical** | 3.4 | Orchestrator delegates to workers |

---

## Extending the Project

Ideas for enhancement:

1. **Judge Agent** - Score arguments and declare winner
2. **Fact-Checker** - Verify claims made by debaters
3. **Audience Q&A** - User can ask follow-up questions
4. **Debate Formats** - Lincoln-Douglas, Oxford style
5. **Multi-Position** - More than 2 sides (e.g., 3-way debate)

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
