# 🌐 Federated Multi-Agent System

> **Project 5.3** from the Agentic AI Learning Pathway
> Local + Cloud agents working together via RabbitMQ

## Overview

A federated system where multiple AI agents (Claude, ChatGPT, Gemini) collaborate through a message queue. Each agent specializes in different tasks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane UI (:8501)                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    RabbitMQ       │
                    │   (:5672/:15672)  │
                    └─────────┬─────────┘
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ 🟣 Claude Agent │ │ 🟢 ChatGPT Agent│ │ 🔵 Gemini Agent │
│     (Local)     │ │     (Local)     │ │  (Cloud/Local)  │
│                 │ │                 │ │                 │
│ • Code Review   │ │ • Content Gen   │ │ • Data Analysis │
│ • Architecture  │ │ • Brainstorming │ │ • Web Research  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
   Anthropic API       OpenAI API         Google AI API
```

## Quick Start

```bash
cd ~/learn-agentic-stack/claude-code-labs/04-distributed-agents
mkdir federated-agents && cd federated-agents

# Set API keys
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
GOOGLE_API_KEY=your-key
EOF

# Start everything
docker-compose up --build
```

**Access:**
- Control Plane: http://localhost:8501
- RabbitMQ: http://localhost:15672 (guest/guest)

---

## 📬 Message Schema

### Task Request

```json
{
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_type": "task_request",
    "source_agent": "orchestrator",
    "target_agent": "local_claude",
    "task_type": "code_review",
    "payload": {
        "code": "def hello(): print('world')",
        "language": "python"
    },
    "correlation_id": "job-001",
    "priority": "medium",
    "timestamp": "2024-01-15T10:30:00Z",
    "retry_count": 0
}
```

### Task Response

```json
{
    "message_id": "660e8400-e29b-41d4-a716-446655440001",
    "message_type": "task_response",
    "source_agent": "local_claude",
    "target_agent": "orchestrator",
    "payload": {
        "success": true,
        "result": {
            "review": "Function needs docstring...",
            "model": "claude-sonnet-4-20250514",
            "tokens": 234
        }
    },
    "correlation_id": "job-001"
}
```

### Sample Payloads

**🟣 Claude - Code Review:**
```json
{"code": "def calc(x): return x*2", "language": "python"}
```

**🟢 ChatGPT - Content:**
```json
{"topic": "AI trends", "format": "blog_post", "length": "500_words"}
```

**🔵 Gemini - Research:**
```json
{"query": "LLM agents 2024", "summarize": true}
```

---

## File Mapping

| Download | Rename To |
|----------|-----------|
| `fed_message_schema.py` | `message_schema.py` |
| `fed_message_queue.py` | `message_queue.py` |
| `fed_agents.py` | `agents.py` |
| `fed_orchestrator.py` | `orchestrator.py` |
| `fed_app.py` | `fed_app.py` |
| `fed_requirements.txt` | `requirements.txt` |
| `fed_Dockerfile.agent` | `Dockerfile.agent` |
| `fed_Dockerfile.ui` | `Dockerfile.ui` |
| `fed_docker_compose.yml` | `docker-compose.yml` |

---

## 💰 Costs

| Component | Cost |
|-----------|------|
| RabbitMQ | FREE (local) |
| Claude | ~$0.01-0.05/task |
| ChatGPT | ~$0.001-0.01/task |
| Gemini | ~$0.001-0.01/task |

---

## ⚠️ GCP Cleanup (IMPORTANT!)

If you deployed to Google Cloud, **clean up to avoid charges:**

### Delete Resources

```bash
# Delete Cloud Run service
gcloud run services delete gemini-agent --region=us-central1 --quiet

# Delete container images  
gcloud artifacts docker images delete \
    us-central1-docker.pkg.dev/PROJECT/agents/gemini-agent --quiet

# NUCLEAR: Delete entire project
gcloud projects delete PROJECT_ID
```

### Set Budget Alert

```bash
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT \
    --display-name="Agent Limit" \
    --budget-amount=1.00USD \
    --threshold-rule=percent=90
```

### Console Cleanup

1. [console.cloud.google.com](https://console.cloud.google.com)
2. **Cloud Run** → Delete services
3. **Artifact Registry** → Delete images
4. **Compute Engine** → Delete VMs
5. **Billing** → Set budget alerts

### ✅ Best: Run Locally

**You don't need GCP!** All agents run locally as Docker containers:

```bash
docker-compose up  # Everything runs on Mac Mini
```

The "cloud" Gemini agent just calls the Google AI API - no cloud infrastructure needed.

---

## Queues

| Queue | Agent |
|-------|-------|
| `agent.local.claude` | 🟣 Claude |
| `agent.local.openai` | 🟢 ChatGPT |
| `agent.cloud.gemini` | 🔵 Gemini |
| `agent.orchestrator` | Control Plane |

---

## Learning Outcomes

- ✅ Distributed agent architecture
- ✅ Message queue patterns (RabbitMQ)
- ✅ Multi-LLM integration
- ✅ Agent specialization
- ✅ Docker orchestration
- ✅ Cloud cost management

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*