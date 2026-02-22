# 🎟️ Understanding Tokens in Learn Agentic Stack

> A practical guide to token usage, costs, and optimization for each project

## What Are Tokens?

Tokens are the units Claude uses to process text. Think of them as word pieces:

```
"Hello, how are you?"  →  ["Hello", ",", " how", " are", " you", "?"]  →  6 tokens
"microservices"        →  ["micro", "services"]                        →  2 tokens
```

**Quick Rules:**
- 1 token ≈ 4 characters in English
- 1 token ≈ ¾ of a word
- 100 tokens ≈ 75 words
- 1 page of text ≈ 500 tokens

---

## Claude Sonnet 4 Pricing

| Type | Cost per Token | Cost per Million |
|------|----------------|------------------|
| **Input** | $0.000003 | $3.00 |
| **Output** | $0.000015 | $15.00 |

> ⚠️ **Key insight:** Output tokens cost **5x more** than input tokens!

**Quick Cost Formula:**
```
Cost = (Input Tokens × $0.000003) + (Output Tokens × $0.000015)
```

---

## How Tokens Flow in Each API Call

```
┌──────────────────────────────────────────────────────────────┐
│                     SINGLE API CALL                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT TOKENS (what goes IN):                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ System Prompt    │ ~200-500 tokens (your instructions)  │ │
│  │ User Message     │ ~50-500 tokens (the question/task)   │ │
│  │ Context/History  │ Variable (previous conversation)     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  OUTPUT TOKENS (what comes OUT):                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Claude's Response │ ~100-2000 tokens (the answer)       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Token Usage by Project Tier

### TIER 1: Foundation (Single API Calls)

#### Project 1.1: Basic Chat

```
┌─────────────────────────────────────────┐
│            BASIC CHAT                   │
│         (1 API call per turn)           │
├─────────────────────────────────────────┤
│ INPUT:                                  │
│   System prompt:     ~200 tokens        │
│   User message:      ~50 tokens         │
│   ─────────────────────────────         │
│   Total Input:       ~250 tokens        │
│                                         │
│ OUTPUT:                                 │
│   Response:          ~300 tokens        │
│                                         │
│ COST PER TURN:       ~$0.005            │
└─────────────────────────────────────────┘

10 turns of conversation ≈ $0.05
```

#### Project 1.2: Tool Use Chat

```
┌─────────────────────────────────────────┐
│          TOOL USE CHAT                  │
│    (2 API calls if tool is used)        │
├─────────────────────────────────────────┤
│                                         │
│ CALL 1: Tool Decision                   │
│   Input:  ~500 tokens (includes tools)  │
│   Output: ~100 tokens (tool call JSON)  │
│                                         │
│ CALL 2: Final Response                  │
│   Input:  ~700 tokens (+tool result)    │
│   Output: ~300 tokens (answer)          │
│                                         │
│ TOTAL PER TURN:                         │
│   Input:  ~1,200 tokens                 │
│   Output: ~400 tokens                   │
│   Cost:   ~$0.010                       │
└─────────────────────────────────────────┘
```

---

### TIER 2: MCP & Infrastructure

#### Projects 2.1-2.2: MCP Servers (Bookmarks/Calendar)

MCP servers themselves don't use tokens - they're just Python servers. Token usage happens in Claude Code or claude.ai when it calls your MCP tools.

```
┌─────────────────────────────────────────┐
│         MCP TOOL CALL                   │
├─────────────────────────────────────────┤
│ When Claude uses your MCP tool:         │
│                                         │
│ INPUT:                                  │
│   System + MCP tool schemas: ~800       │
│   User query:                ~100       │
│   Tool result:               ~200       │
│   ─────────────────────────────         │
│   Total:                     ~1,100     │
│                                         │
│ OUTPUT:                                 │
│   Tool call + response:      ~400       │
│                                         │
│ COST PER MCP USE:            ~$0.009    │
└─────────────────────────────────────────┘
```

#### Project 2.3: Memory Agent (ChromaDB)

```
┌─────────────────────────────────────────┐
│          MEMORY AGENT                   │
│    (2-3 API calls per interaction)      │
├─────────────────────────────────────────┤
│                                         │
│ CALL 1: Chat with Memory Context        │
│   System prompt:         ~300 tokens    │
│   Retrieved memories:    ~500 tokens    │
│   User message:          ~100 tokens    │
│   ─────────────────────────────         │
│   Input:                 ~900 tokens    │
│   Output (response):     ~400 tokens    │
│                                         │
│ CALL 2: Fact Extraction (optional)      │
│   Input:                 ~600 tokens    │
│   Output (facts JSON):   ~200 tokens    │
│                                         │
│ TOTAL PER INTERACTION:                  │
│   Input:    ~1,500 tokens               │
│   Output:   ~600 tokens                 │
│   Cost:     ~$0.014                     │
│                                         │
│ Note: ChromaDB embeddings are FREE      │
│ (uses local sentence-transformers)     │
└─────────────────────────────────────────┘
```

#### Project 2.4: Observable Agent

```
┌─────────────────────────────────────────┐
│        OBSERVABLE AGENT                 │
│      (Same as basic chat +              │
│       metrics/logging overhead)         │
├─────────────────────────────────────────┤
│                                         │
│ API CALL:                               │
│   Input:             ~400 tokens        │
│   Output:            ~350 tokens        │
│   Cost:              ~$0.006            │
│                                         │
│ WHAT'S TRACKED (no extra tokens):       │
│   • InfluxDB metrics (local)            │
│   • Loki logs (local)                   │
│   • Grafana dashboards (local)          │
│                                         │
│ Observability infrastructure = FREE     │
│ (all local Docker containers)           │
└─────────────────────────────────────────┘
```

---

### TIER 3: Multi-Agent Patterns ⚠️ Token Multipliers!

> **Critical:** Multi-agent = Multiple API calls = Multiplied costs

#### Project 3.1: Researcher + Writer (Sequential)

```
┌──────────────────────────────────────────────────────────────┐
│              RESEARCHER + WRITER PIPELINE                    │
│                   (2 API calls)                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐        ┌─────────────────┐             │
│  │   RESEARCHER    │   →    │     WRITER      │             │
│  │   (API Call 1)  │        │   (API Call 2)  │             │
│  └─────────────────┘        └─────────────────┘             │
│                                                              │
│  CALL 1 - Researcher:                                        │
│    Input:  ~400 tokens  (system + query)                     │
│    Output: ~800 tokens  (research notes JSON)                │
│    Cost:   $0.013                                            │
│                                                              │
│  CALL 2 - Writer:                                            │
│    Input:  ~1,200 tokens (system + research notes)           │
│    Output: ~1,500 tokens (article)                           │
│    Cost:   $0.026                                            │
│                                                              │
│  ═══════════════════════════════════════════════════════    │
│  TOTAL PER ARTICLE:                                          │
│    Input:    ~1,600 tokens                                   │
│    Output:   ~2,300 tokens                                   │
│    Cost:     ~$0.039                                         │
│    API Calls: 2                                              │
└──────────────────────────────────────────────────────────────┘
```

#### Project 3.2: Code Review Pipeline (Fan-out/Fan-in)

```
┌──────────────────────────────────────────────────────────────┐
│               CODE REVIEW PIPELINE                           │
│                  (3 API calls)                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│          ┌─────────────┐                                     │
│          │   ANALYZER  │  ←─┐                                │
│   Code → │  (Call 1)   │    │ parallel                       │
│          └─────────────┘    │                                │
│          ┌─────────────┐    │    ┌─────────────┐             │
│          │  SECURITY   │  ←─┘    │  REVIEWER   │             │
│          │  (Call 2)   │    →    │  (Call 3)   │             │
│          └─────────────┘         └─────────────┘             │
│                                                              │
│  CALL 1 - Analyzer:                                          │
│    Input:  ~800 tokens  (system + code)                      │
│    Output: ~600 tokens  (analysis JSON)                      │
│    Cost:   $0.011                                            │
│                                                              │
│  CALL 2 - Security Scanner:                                  │
│    Input:  ~800 tokens  (system + code)                      │
│    Output: ~500 tokens  (security JSON)                      │
│    Cost:   $0.010                                            │
│                                                              │
│  CALL 3 - Reviewer:                                          │
│    Input:  ~2,000 tokens (system + code + both analyses)     │
│    Output: ~1,200 tokens (full review)                       │
│    Cost:   $0.024                                            │
│                                                              │
│  ═══════════════════════════════════════════════════════    │
│  TOTAL PER CODE REVIEW:                                      │
│    Input:    ~3,600 tokens                                   │
│    Output:   ~2,300 tokens                                   │
│    Cost:     ~$0.045                                         │
│    API Calls: 3                                              │
└──────────────────────────────────────────────────────────────┘
```

#### Project 3.3: Debate Agents (Adversarial)

```
┌──────────────────────────────────────────────────────────────┐
│                    DEBATE AGENTS                             │
│            (2n + 1 API calls for n rounds)                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  3-ROUND DEBATE = 7 API CALLS:                               │
│                                                              │
│  Round 1:  🟢 Pro (Call 1) → 🔴 Con (Call 2)                 │
│  Round 2:  🟢 Pro (Call 3) → 🔴 Con (Call 4)                 │
│  Round 3:  🟢 Pro (Call 5) → 🔴 Con (Call 6)                 │
│  Synthesis: ⚖️ Synthesizer (Call 7)                          │
│                                                              │
│  TOKEN BREAKDOWN:                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Agent      │ Input  │ Output │ Calls │ Subtotal       │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ Pro        │ ~1,800 │ ~1,200 │   3   │ $0.024         │ │
│  │ Con        │ ~2,100 │ ~1,200 │   3   │ $0.025         │ │
│  │ Synthesizer│ ~2,500 │   ~800 │   1   │ $0.020         │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ TOTAL      │ ~6,400 │ ~3,200 │   7   │ $0.069         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ⚠️ More rounds = More tokens!                               │
│     5 rounds = 11 calls ≈ $0.11                              │
└──────────────────────────────────────────────────────────────┘
```

#### Project 3.4: Task Orchestrator (Hierarchical)

```
┌──────────────────────────────────────────────────────────────┐
│               TASK DECOMPOSITION ORCHESTRATOR                │
│              (2 + n API calls for n subtasks)                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  TYPICAL FLOW (4 subtasks):                                  │
│                                                              │
│  Planning:    📋 Orchestrator (Call 1)                       │
│  Execution:   🔍 Research Worker (Call 2)                    │
│               💻 Code Worker (Call 3)                        │
│               ✍️ Write Worker (Call 4)                       │
│               📊 Analyze Worker (Call 5)                     │
│  Aggregation: 📋 Orchestrator (Call 6)                       │
│                                                              │
│  TOKEN BREAKDOWN:                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Phase       │ Input  │ Output │ Calls │ Subtotal      │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ Planning    │   ~500 │   ~600 │   1   │ $0.011        │ │
│  │ Workers     │ ~3,200 │ ~4,000 │   4   │ $0.070        │ │
│  │ Aggregation │ ~4,500 │ ~1,500 │   1   │ $0.036        │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ TOTAL       │ ~8,200 │ ~6,100 │   6   │ $0.117        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ⚠️ Complex tasks = More subtasks = More tokens!             │
│     6 subtasks ≈ 8 calls ≈ $0.15                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Summary: Cost Per Project

| Project | Pattern | API Calls | Tokens | Est. Cost |
|---------|---------|-----------|--------|-----------|
| **TIER 1** |
| 1.1 Basic Chat | Single | 1 | ~550 | $0.005 |
| 1.2 Tool Use | Single+Tool | 2 | ~1,600 | $0.010 |
| **TIER 2** |
| 2.1-2.2 MCP Servers | Tool | 2 | ~1,500 | $0.009 |
| 2.3 Memory Agent | RAG | 2-3 | ~2,100 | $0.014 |
| 2.4 Observable Agent | Single | 1 | ~750 | $0.006 |
| **TIER 3** |
| 3.1 Researcher+Writer | Sequential | 2 | ~3,900 | $0.039 |
| 3.2 Code Review | Fan-out/In | 3 | ~5,900 | $0.045 |
| 3.3 Debate (3 rounds) | Adversarial | 7 | ~9,600 | $0.069 |
| 3.4 Task Orchestrator | Hierarchical | 6+ | ~14,300 | $0.117 |

---

## Multi-Agent Token Multiplication

```
┌──────────────────────────────────────────────────────────────┐
│              WHY MULTI-AGENT COSTS MORE                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  SINGLE AGENT:                                               │
│  ┌───────────┐                                               │
│  │  Claude   │  1 call = ~$0.005                             │
│  └───────────┘                                               │
│                                                              │
│  SEQUENTIAL (A → B):                                         │
│  ┌───────────┐    ┌───────────┐                              │
│  │  Agent A  │ →  │  Agent B  │  2 calls                     │
│  └───────────┘    └───────────┘                              │
│  + Agent B receives A's output as input                      │
│  = ~$0.04 (8x single agent!)                                 │
│                                                              │
│  HIERARCHICAL (Orchestrator + Workers):                      │
│  ┌───────────┐                                               │
│  │   Orch    │ ──┬──┬──┬──→ Aggregate                        │
│  └───────────┘   │  │  │                                     │
│              ┌───┴──┴──┴───┐                                 │
│              │ W1  W2  W3  │   6+ calls                      │
│              └─────────────┘                                 │
│  + Each worker may receive context from orchestrator         │
│  + Aggregator receives ALL worker outputs                    │
│  = ~$0.12 (24x single agent!)                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘

THE PATTERN:
┌─────────────────────────────────────────────────────────────┐
│  More agents = More API calls = More tokens = Higher cost   │
│                                                             │
│  Each handoff ADDS tokens because:                          │
│  1. Output from Agent A → Input to Agent B                  │
│  2. Agent B needs its own system prompt too                 │
│  3. Context compounds as it passes through pipeline         │
└─────────────────────────────────────────────────────────────┘
```

---

## Token Tracking Code

Add this to any project to track costs:

```python
def track_usage(response, label="API Call"):
    """Print token usage and cost for any Claude API response."""
    usage = response.usage
    
    input_cost = usage.input_tokens * 0.000003
    output_cost = usage.output_tokens * 0.000015
    total_cost = input_cost + output_cost
    
    print(f"\n{'='*50}")
    print(f"📊 {label} - Token Usage")
    print(f"{'='*50}")
    print(f"  📥 Input:  {usage.input_tokens:,} tokens (${input_cost:.4f})")
    print(f"  📤 Output: {usage.output_tokens:,} tokens (${output_cost:.4f})")
    print(f"  💵 Total:  ${total_cost:.4f}")
    print(f"{'='*50}\n")
    
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost": total_cost
    }

# Usage:
response = claude.messages.create(...)
track_usage(response, "Researcher Agent")
```

---

## Budget Planning

### Development Phase (Learning)

| Activity | Per Use | Weekly Uses | Weekly Cost |
|----------|---------|-------------|-------------|
| Basic chat testing | $0.005 | 50 | $0.25 |
| Tool use testing | $0.01 | 30 | $0.30 |
| Multi-agent runs | $0.05-0.12 | 20 | $1.50 |
| **Weekly Total** | | | **~$2.05** |
| **Monthly Total** | | | **~$8.20** |

### Active Development

| Activity | Per Use | Monthly Uses | Monthly Cost |
|----------|---------|--------------|--------------|
| Single agent tests | $0.01 | 200 | $2.00 |
| Multi-agent pipelines | $0.08 | 100 | $8.00 |
| Complex orchestrations | $0.15 | 50 | $7.50 |
| **Monthly Total** | | | **~$17.50** |

---

## Cost Optimization Tips

### 1. Use Shorter System Prompts

```python
# ❌ Verbose (costs more)
SYSTEM = """You are a research assistant. Your job is to help users 
find information. You should be thorough and comprehensive. Always 
cite your sources. Be helpful and friendly. Follow best practices..."""

# ✅ Concise (saves tokens)
SYSTEM = """Research assistant. Be thorough, cite sources, stay concise."""
```

### 2. Limit Output Tokens

```python
# Set appropriate max_tokens
response = claude.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,  # Limit output for simple tasks
    messages=[...]
)
```

### 3. Truncate Handoff Data

```python
# ❌ Passing full content
writer_input = researcher_output  # Could be 2000+ tokens

# ✅ Pass summary only
writer_input = researcher_output["summary"]  # ~200 tokens
```

### 4. Run Workers in Parallel

```python
# Parallel execution doesn't save tokens but saves TIME
# (Same total tokens, but faster execution)
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(run_worker, subtasks))
```

### 5. Cache Repeated Calls

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_research(query: str) -> str:
    """Cache research results to avoid duplicate API calls."""
    return run_researcher(query)
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────┐
│                    TOKEN QUICK REFERENCE                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CONVERSION:                                                 │
│    1 token ≈ 4 characters ≈ 0.75 words                       │
│    1 page ≈ 500 tokens                                       │
│    1 code file ≈ 200-800 tokens                              │
│                                                              │
│  PRICING (Sonnet 4):                                         │
│    Input:  $3 per million  = $0.000003 per token             │
│    Output: $15 per million = $0.000015 per token             │
│                                                              │
│  TYPICAL COSTS:                                              │
│    Simple chat turn:     ~$0.005                             │
│    Tool use turn:        ~$0.01                              │
│    2-agent pipeline:     ~$0.04                              │
│    3-agent pipeline:     ~$0.05                              │
│    Complex orchestration: ~$0.10-0.15                        │
│                                                              │
│  FORMULA:                                                    │
│    Cost = (Input × $0.000003) + (Output × $0.000015)         │
│                                                              │
│  RULE OF THUMB:                                              │
│    Each additional agent ≈ 1.5-2x more tokens                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## See Also

- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [Token Counter Tool](https://www.anthropic.com/token-counter)
- Project READMEs for specific token tracking implementations

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
