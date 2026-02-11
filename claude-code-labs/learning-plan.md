# 🎯 Agentic AI Learning Pathway

> **Personal Development Plan for Karthik Raghavan**
> Transitioning from Software Engineer → AI Engineer
> Focus: Claude Code SDK, MCP Tools, Multi-Agent Systems

---

## 📊 Overview

| Duration | 3-4 months (flexible) |
|----------|----------------------|
| Stack | Claude Code (Local) + Google SDK (Cloud) |
| Hardware | Any device with M4 or equivalent processor, 256Gb storage and 16Gb RAM |
| End Goal | Train agents for specific tasks |

### Philosophy
- **Learn by building** - Each project is a working system
- **Local first** - Master local development before cloud
- **UI included** - Every MCP tool gets a usable interface
- **Observable** - Add metrics/logging to everything

---

## 🏗️ TIER 1: Foundations
*Duration: 1-2 weeks | Complexity: ⭐*

### Project 1.1: File Organizer Agent
**Goal:** First working agent with MCP filesystem tools

| Component | Details |
|-----------|---------|
| MCP Tools | `filesystem` (read, write, list, move) |
| UI | Streamlit dashboard showing folder tree + actions taken |
| Input | Source folder path |
| Output | Organized folder + action log |

**Features:**
- [ ] Scan folder recursively
- [ ] Classify files by type (code, docs, images, data)
- [ ] Organize into subfolders by date/type/project
- [ ] Generate summary report
- [ ] Streamlit UI: folder picker, preview changes, execute button

**Learning Outcomes:**
- MCP filesystem server basics
- Structured output from Claude
- Simple UI integration

---

### Project 1.2: SQLite Query Agent
**Goal:** Natural language → SQL with MCP database tools

| Component | Details |
|-----------|---------|
| MCP Tools | `sqlite` (query, schema, tables) |
| UI | Chat interface + results table |
| Input | Natural language questions |
| Output | SQL query + formatted results |

**Features:**
- [ ] Load any SQLite database
- [ ] Show schema understanding
- [ ] Convert questions to SQL
- [ ] Display results in table format
- [ ] Streamlit UI: DB selector, chat input, SQL preview, results grid

**Learning Outcomes:**
- MCP database server
- Text-to-SQL patterns
- Error handling (bad queries)

---

### Project 1.3: Markdown Note Taker
**Goal:** Persistent note-taking agent

| Component | Details |
|-----------|---------|
| MCP Tools | `filesystem`, custom `notes` server |
| UI | Simple note input + search interface |
| Input | Voice/text notes |
| Output | Organized markdown files |

**Features:**
- [ ] Quick capture mode (append to daily note)
- [ ] Tag extraction and organization
- [ ] Search across all notes
- [ ] Link related notes
- [ ] Streamlit UI: capture box, tag cloud, search, note viewer

**Learning Outcomes:**
- Custom MCP server (your first!)
- Structured file organization
- Text search basics

---

### Project 1.4: Git Commit Summarizer
**Goal:** Automate release notes generation

| Component | Details |
|-----------|---------|
| MCP Tools | `shell` (git commands) |
| UI | Repo selector + generated changelog |
| Input | Git repository path, date range |
| Output | Formatted changelog/release notes |

**Features:**
- [ ] Parse git log with filters
- [ ] Group commits by type (feat, fix, chore)
- [ ] Generate human-readable summaries
- [ ] Export as CHANGELOG.md
- [ ] Streamlit UI: repo picker, date range, format options, preview

**Learning Outcomes:**
- Shell command execution via MCP
- Text summarization patterns
- Markdown generation

---

## 🔧 TIER 2: Tool Building
*Duration: 2-3 weeks | Complexity: ⭐⭐*

### Project 2.1: Custom MCP Server - Browser Bookmarks
**Goal:** Build complete MCP server from scratch

| Component | Details |
|-----------|---------|
| MCP Server | `bookmarks-mcp` (custom) |
| UI | Searchable bookmark manager |
| Browsers | Chrome, Firefox, Safari |
| Protocol | Full MCP implementation |

**Features:**
- [ ] Read bookmarks from browser SQLite/JSON
- [ ] Search by title, URL, folder
- [ ] Add/delete/organize bookmarks
- [ ] Export to various formats
- [ ] Streamlit UI: browser selector, search, folder tree, bulk actions

**MCP Server Structure:**
```
bookmarks-mcp/
├── server.py           # MCP server implementation
├── browsers/
│   ├── chrome.py       # Chrome bookmark parser
│   ├── firefox.py      # Firefox bookmark parser
│   └── safari.py       # Safari bookmark parser
├── schemas/
│   └── tools.json      # Tool definitions
└── README.md
```

**Learning Outcomes:**
- MCP protocol deep dive
- Tool schema definition
- Multi-source data aggregation

---

### Project 2.2: Custom MCP Server - Calendar Integration
**Goal:** OAuth + external API integration

| Component | Details |
|-----------|---------|
| MCP Server | `calendar-mcp` (custom) |
| UI | Calendar view + natural language scheduling |
| Integration | Google Calendar API |
| Auth | OAuth 2.0 flow |

**Features:**
- [ ] OAuth authentication flow
- [ ] Read events (today, week, month)
- [ ] Create events from natural language
- [ ] Find free slots
- [ ] Send meeting invites
- [ ] React UI: calendar component, chat input, event cards

**Learning Outcomes:**
- OAuth in MCP context
- External API integration
- Date/time handling
- React UI basics

---

### Project 2.3: Agent with Memory (ChromaDB)
**Goal:** Persistent conversational memory

| Component | Details |
|-----------|---------|
| Vector DB | ChromaDB (local) |
| Embeddings | sentence-transformers (local) |
| UI | Chat interface with memory indicators |

**Features:**
- [ ] Store conversation history as embeddings
- [ ] Retrieve relevant past context
- [ ] Show "remembering" indicators in UI
- [ ] Memory management (forget, prioritize)
- [ ] Streamlit UI: chat, memory sidebar, relevance scores

**Architecture:**
```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Chat  │────▶│ Claude Agent │────▶│   ChromaDB   │
└─────────────┘     └──────────────┘     └──────────────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐
                    │   Response   │◀────│  Embeddings  │
                    └──────────────┘     └──────────────┘
```

**Learning Outcomes:**
- Vector database operations
- Embedding generation
- RAG pattern basics
- Context window management

---

### Project 2.4: Observable Agent
**Goal:** Full observability stack for any agent

| Component | Details |
|-----------|---------|
| Metrics | InfluxDB |
| Logs | Loki + Promtail |
| Dashboards | Grafana |
| UI | Grafana dashboards (pre-built) |

**Metrics to Track:**
- [ ] API calls (count, latency, tokens)
- [ ] Tool usage (which tools, success rate)
- [ ] Memory hits/misses
- [ ] Error rates
- [ ] Cost tracking ($)

**Reusable Components:**
```
observable-agent/
├── docker-compose.yml      # InfluxDB, Loki, Grafana
├── metrics/
│   ├── collector.py        # Metrics collection wrapper
│   └── dashboards/         # Pre-built Grafana dashboards
├── logging/
│   ├── structured.py       # JSON logging utilities
│   └── promtail-config.yaml
└── README.md
```

**Learning Outcomes:**
- Production observability patterns
- Metrics collection in Python
- Grafana dashboard creation
- Cost tracking

---

## 🤝 TIER 3: Multi-Agent Patterns
*Duration: 2-3 weeks | Complexity: ⭐⭐⭐*

### Project 3.1: Researcher + Writer Duo
**Goal:** First A2A (Agent-to-Agent) handoff

| Component | Details |
|-----------|---------|
| Agent 1 | Researcher (web search, summarize) |
| Agent 2 | Writer (structure, polish) |
| UI | Pipeline view showing both agents |
| Communication | Structured handoff protocol |

**Flow:**
```
User Query → [Researcher Agent] → Research Notes → [Writer Agent] → Final Article
                   │                                      │
                   ▼                                      ▼
            Search Results                          Draft → Edit → Final
```

**Features:**
- [ ] Researcher: web search, extract facts, cite sources
- [ ] Writer: outline, draft, polish
- [ ] Handoff protocol (structured JSON)
- [ ] Streamlit UI: query input, researcher panel, writer panel, final output

**Learning Outcomes:**
- Agent specialization
- Structured handoff protocols
- Pipeline orchestration
- Parallel vs sequential execution

---

### Project 3.2: Code Review Pipeline
**Goal:** Multi-step workflow with different agent roles

| Component | Details |
|-----------|---------|
| Agent 1 | Code Analyzer (logic, patterns) |
| Agent 2 | Security Scanner (vulnerabilities) |
| Agent 3 | Review Writer (synthesize findings) |
| UI | Code diff view + review comments |

**Pipeline:**
```
PR/Code → [Analyzer] → [Security] → [Reviewer] → Final Review
              │            │             │
              ▼            ▼             ▼
          Logic Issues  CVEs Found   Written Review
```

**Features:**
- [ ] Parse code diffs
- [ ] Analyze code quality
- [ ] Check for security issues
- [ ] Generate actionable review comments
- [ ] React UI: code viewer, inline comments, severity indicators

**Learning Outcomes:**
- Code analysis patterns
- Security scanning basics
- Review generation
- Complex UI components

---

### Project 3.3: Debate Agents
**Goal:** Adversarial agent pattern

| Component | Details |
|-----------|---------|
| Agent 1 | Pro (argue for) |
| Agent 2 | Con (argue against) |
| Agent 3 | Synthesizer (balanced conclusion) |
| UI | Debate view with turn-by-turn display |

**Features:**
- [ ] Topic input
- [ ] Alternating arguments (3-5 rounds)
- [ ] Source citation for claims
- [ ] Final synthesis with nuance
- [ ] Streamlit UI: topic input, debate timeline, synthesis panel

**Learning Outcomes:**
- Adversarial prompting
- Turn-based agent coordination
- Synthesis patterns
- Balanced output generation

---

### Project 3.4: Task Decomposition Orchestrator
**Goal:** Master agent with worker delegation

| Component | Details |
|-----------|---------|
| Orchestrator | Plans, delegates, aggregates |
| Workers | Specialized agents (research, code, write) |
| UI | Task tree visualization |
| Pattern | Hierarchical multi-agent |

**Architecture:**
```
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │  (Plan & Merge) │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  Research   │   │    Code     │   │   Writer    │
    │   Worker    │   │   Worker    │   │   Worker    │
    └─────────────┘   └─────────────┘   └─────────────┘
```

**Features:**
- [ ] Complex task input
- [ ] Automatic decomposition
- [ ] Worker assignment
- [ ] Progress tracking
- [ ] Result aggregation
- [ ] Streamlit UI: task input, decomposition tree, progress bars, final output

**Learning Outcomes:**
- Task decomposition algorithms
- Agent orchestration patterns
- Progress tracking
- Result aggregation

---

## 🚀 TIER 4: Full Applications
*Duration: 3-4 weeks | Complexity: ⭐⭐⭐⭐*

### Project 4.1: Personal Knowledge Base
**Goal:** Index and chat with your documents

| Component | Details |
|-----------|---------|
| Ingestion | PDF, Markdown, Text, Code |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |
| UI | Full knowledge management interface |

**Features:**
- [ ] Document upload and indexing
- [ ] Automatic chunking and embedding
- [ ] Semantic search
- [ ] Chat with citations
- [ ] Knowledge graph visualization
- [ ] Streamlit UI: upload, search, chat, graph view, source viewer

**Learning Outcomes:**
- Document processing pipelines
- Advanced RAG patterns
- Citation generation
- Knowledge graph basics

---

### Project 4.2: Dev Environment Agent
**Goal:** Autonomous environment setup

| Component | Details |
|-----------|---------|
| Tools | Shell, filesystem, package managers |
| Platforms | Node, Python, Go, Rust |
| UI | Setup wizard + terminal output |

**Features:**
- [ ] Analyze project requirements
- [ ] Install dependencies
- [ ] Configure environment variables
- [ ] Set up linters/formatters
- [ ] Create docker-compose if needed
- [ ] React UI: project selector, step-by-step wizard, terminal view

**Learning Outcomes:**
- Complex tool orchestration
- Error recovery patterns
- Cross-platform considerations
- DevOps automation

---

### Project 4.3: Meeting Notes → Action Items Pipeline
**Goal:** End-to-end meeting processing

| Component | Details |
|-----------|---------|
| Input | Audio file or transcript |
| Processing | Transcription, extraction, ticketing |
| Integrations | (Mock) Jira, Email, Calendar |
| UI | Meeting dashboard |

**Pipeline:**
```
Audio → [Transcribe] → [Summarize] → [Extract Actions] → [Create Tickets]
                                            │
                                            ▼
                                    [Send Follow-up Email]
```

**Features:**
- [ ] Audio transcription (Whisper)
- [ ] Meeting summarization
- [ ] Action item extraction
- [ ] Assignee detection
- [ ] Ticket creation (mock Jira)
- [ ] Email drafting
- [ ] Streamlit UI: upload, transcript view, action items, ticket preview

**Learning Outcomes:**
- Audio processing
- Information extraction
- External service integration
- End-to-end pipelines

---

### Project 4.4: Local SRE Bot
**Goal:** Monitor and manage local infrastructure

| Component | Details |
|-----------|---------|
| Monitoring | Docker containers, system resources |
| Actions | Restart, scale, alert |
| UI | Infrastructure dashboard |

**Features:**
- [ ] Container health monitoring
- [ ] Resource usage tracking (CPU, RAM, disk)
- [ ] Auto-restart on failure
- [ ] Anomaly detection
- [ ] Incident reports
- [ ] Grafana + Custom UI: container grid, metrics, action buttons, incident log

**Learning Outcomes:**
- Docker API usage
- System monitoring
- Auto-remediation patterns
- Alerting systems

---

## 🧠 TIER 5: Advanced Patterns
*Duration: 4-8 weeks | Complexity: ⭐⭐⭐⭐⭐*

### Project 5.1: Self-Improving Agent
**Goal:** Agent that learns from failures

| Component | Details |
|-----------|---------|
| Feedback Loop | Log failures → Analyze → Improve prompts |
| Storage | SQLite (failure logs) + ChromaDB (examples) |
| UI | Improvement dashboard |

**Features:**
- [ ] Failure detection and logging
- [ ] Pattern analysis in failures
- [ ] Automatic prompt refinement
- [ ] A/B testing of prompts
- [ ] Performance tracking over time
- [ ] Streamlit UI: failure browser, improvement suggestions, metrics

**Learning Outcomes:**
- Feedback loop design
- Prompt optimization
- Evaluation metrics
- Continuous improvement

---

### Project 5.2: Agent Evaluation Framework
**Goal:** Benchmark and compare agent configurations

| Component | Details |
|-----------|---------|
| Test Harness | Standardized test cases |
| Metrics | Accuracy, latency, cost, consistency |
| UI | Comparison dashboard |

**Features:**
- [ ] Test case definition format
- [ ] Automated test execution
- [ ] Multi-configuration comparison
- [ ] Statistical analysis
- [ ] Regression detection
- [ ] Streamlit UI: test runner, results grid, charts, export

**Learning Outcomes:**
- Evaluation design
- Statistical testing
- Benchmark creation
- Regression testing

---

### Project 5.3: Federated Multi-Agent System
**Goal:** Local + Cloud agents working together

| Component | Details |
|-----------|---------|
| Local Agents | Claude Code (MCP) |
| Cloud Agents | Vertex AI (Google SDK) |
| Communication | Message queue (RabbitMQ) |
| UI | Unified control plane |

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    Control Plane UI                      │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│   Local (Mac Mini)  │◀───────▶│   Cloud (GCP)       │
│  ┌───────────────┐  │   MQ    │  ┌───────────────┐  │
│  │ Claude Agent  │  │         │  │ Vertex Agent  │  │
│  └───────────────┘  │         │  └───────────────┘  │
│  ┌───────────────┐  │         │  ┌───────────────┐  │
│  │ Local Tools   │  │         │  │ Cloud Tools   │  │
│  └───────────────┘  │         │  └───────────────┘  │
└─────────────────────┘         └─────────────────────┘
```

**Learning Outcomes:**
- Distributed agent systems
- Cloud integration
- Message queue patterns
- Hybrid architectures

---

### Project 5.4: Domain-Specific Agent Trainer
**Goal:** Rapidly train agents for specific tasks (YOUR END GOAL!)

| Component | Details |
|-----------|---------|
| Training UI | Example collection interface |
| Learning | Few-shot prompt optimization |
| Evaluation | Automatic testing |
| Export | Deployable agent package |

**Features:**
- [ ] Domain definition interface
- [ ] Example collection (input/output pairs)
- [ ] Automatic prompt generation
- [ ] Iterative refinement
- [ ] Performance benchmarking
- [ ] Export as standalone agent
- [ ] Full React UI: domain wizard, example editor, training view, deploy

**This is your capstone project!**

---

## 📅 Suggested Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        MONTH 1                                   │
├─────────────────────────────────────────────────────────────────┤
│ Week 1-2: TIER 1 (Projects 1.1 - 1.4)                           │
│           Foundation projects, basic MCP usage                   │
│                                                                  │
│ Week 3-4: TIER 2 (Projects 2.1 - 2.2)                           │
│           Build your first custom MCP servers                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        MONTH 2                                   │
├─────────────────────────────────────────────────────────────────┤
│ Week 5-6: TIER 2 (Projects 2.3 - 2.4)                           │
│           Memory systems and observability                       │
│                                                                  │
│ Week 7-8: TIER 3 (Projects 3.1 - 3.2)                           │
│           First multi-agent systems                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        MONTH 3                                   │
├─────────────────────────────────────────────────────────────────┤
│ Week 9-10: TIER 3 (Projects 3.3 - 3.4)                          │
│            Advanced multi-agent patterns                         │
│                                                                  │
│ Week 11-12: TIER 4 (Projects 4.1 - 4.2)                         │
│             Full applications                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        MONTH 4+                                  │
├─────────────────────────────────────────────────────────────────┤
│ Week 13-14: TIER 4 (Projects 4.3 - 4.4)                         │
│             Complete full applications                           │
│                                                                  │
│ Week 15+: TIER 5 (Projects 5.1 - 5.4)                           │
│           Advanced patterns + Capstone                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack Reference

### Local Development
| Tool | Purpose |
|------|---------|
| Claude Code | Primary agent SDK |
| MCP | Tool protocol |
| ChromaDB | Local vector DB |
| sentence-transformers | Local embeddings |
| Docker | Container management |
| InfluxDB | Metrics |
| Loki | Logs |
| Grafana | Dashboards |

### UI Frameworks
| Framework | When to Use |
|-----------|-------------|
| Streamlit | Quick prototypes, data-heavy UIs |
| React | Complex interactions, production UIs |
| Gradio | ML-focused demos |

### Cloud (When Ready)
| Service | Purpose |
|---------|---------|
| Vertex AI | Cloud agent hosting |
| BigQuery | Large-scale storage |
| Cloud Run | Agent deployment |
| GCP Vector Search | Production vector DB |

---

### 💻 Local-First Approach
This pathway is designed to run **entirely on your local setup** through TIER 1-4. 
No cloud costs, no API quotas to worry about - just fast local iteration. 
Your $300 GCP credit stays untouched until TIER 5, when you're ready to bridge 
local agents with cloud infrastructure. Cloud integration (Vertex AI, BigQuery, 
Cloud Run) is introduced only in Project 5.3+.

## 📝 Progress Tracking

### TIER 1: Foundations
- [ ] 1.1 File Organizer Agent
- [ ] 1.2 SQLite Query Agent
- [ ] 1.3 Markdown Note Taker
- [ ] 1.4 Git Commit Summarizer

### TIER 2: Tool Building
- [ ] 2.1 Custom MCP Server - Browser Bookmarks
- [ ] 2.2 Custom MCP Server - Calendar Integration
- [ ] 2.3 Agent with Memory (ChromaDB)
- [ ] 2.4 Observable Agent

### TIER 3: Multi-Agent Patterns
- [ ] 3.1 Researcher + Writer Duo
- [ ] 3.2 Code Review Pipeline
- [ ] 3.3 Debate Agents
- [ ] 3.4 Task Decomposition Orchestrator

### TIER 4: Full Applications
- [ ] 4.1 Personal Knowledge Base
- [ ] 4.2 Dev Environment Agent
- [ ] 4.3 Meeting Notes → Action Items Pipeline
- [ ] 4.4 Local SRE Bot

### TIER 5: Advanced Patterns
- [ ] 5.1 Self-Improving Agent
- [ ] 5.2 Agent Evaluation Framework
- [ ] 5.3 Federated Multi-Agent System
- [ ] 5.4 Domain-Specific Agent Trainer ⭐ CAPSTONE

---

## 🎯 Success Criteria

By the end of this pathway, you will be able to:

1. **Build MCP Tools** - Create custom MCP servers for any data source
2. **Design Multi-Agent Systems** - Orchestrate multiple agents with clear handoffs
3. **Add Observability** - Monitor any agent with metrics, logs, dashboards
4. **Create UIs** - Build usable interfaces for agent interactions
5. **Implement Memory** - Add persistent memory using vector databases
6. **Train Agents** - Rapidly create domain-specific agents for any task

---

## 📚 Resources

### Documentation
- [Claude Code Docs](https://docs.anthropic.com/claude-code)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)

### Your Projects
- [multi-agent-vector-ai](https://github.com/kraghavan/agent-force) - Reference implementation
- [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack) - This learning repo

---

*Last Updated: February 2026*
*Created with Claude (Opus 4.5)*