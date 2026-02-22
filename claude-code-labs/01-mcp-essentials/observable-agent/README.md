# 📊 Observable Agent

> **Project 2.4** from the Agentic AI Learning Pathway
> Full observability stack: metrics, logs, and dashboards

## Overview

Build a production-ready observability stack for any AI agent. This project sets up InfluxDB (metrics), Loki (logs), and Grafana (dashboards) using Docker Compose, with a sample agent that demonstrates full observability.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OBSERVABLE AGENT STACK                           │
│                                                                         │
│   ┌─────────────┐    metrics    ┌─────────────┐                        │
│   │  Agent App  │──────────────▶│  InfluxDB   │───┐                    │
│   │  Port 8501  │               │  Port 8086  │   │                    │
│   └──────┬──────┘               └─────────────┘   │                    │
│          │                                         │    ┌─────────────┐│
│          │ logs                                    ├───▶│   Grafana   ││
│          ▼                                         │    │  Port 3000  ││
│   ┌─────────────┐    ships     ┌─────────────┐    │    └─────────────┘│
│   │    Logs     │─────────────▶│   Promtail  │────┤                   │
│   │  (files)    │              └──────┬──────┘    │                    │
│   └─────────────┘                     │           │                    │
│                                       ▼           │                    │
│                               ┌─────────────┐     │                    │
│                               │    Loki     │─────┘                    │
│                               │  Port 3100  │                          │
│                               └─────────────┘                          │
│                                                                         │
│                         Docker Compose                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

- [x] **Metrics Collection** - API calls, tokens, latency, cost
- [x] **Structured Logging** - JSON logs shipped to Loki
- [x] **Pre-built Dashboard** - Grafana dashboard ready to use
- [x] **Cost Tracking** - Per-request and cumulative costs
- [x] **Tool Observability** - Track tool usage and success rates
- [x] **Docker Compose** - One command to run everything
- [x] **Reusable Components** - Use in any agent project

## Quick Start

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs/01-mcp-essentials
mkdir -p observable-agent/{config,dashboards,logs}
cd observable-agent
```

### Step 2: Copy Files

```
observable-agent/
├── observable_app.py           → observable_app.py
├── metrics_collector.py        → metrics_collector.py
├── structured_logger.py        → structured_logger.py
├── Dockerfile                  ← observable_Dockerfile
├── docker-compose.yml          ← observable_docker_compose.yml
├── requirements.txt            ← observable_requirements.txt
├── config/
│   ├── loki-config.yaml        ← loki-config.yaml
│   ├── promtail-config.yaml    ← promtail-config.yaml
│   └── grafana-datasources.yaml ← grafana-datasources.yaml
├── dashboards/
│   ├── dashboard-provider.yaml ← dashboard-provider.yaml
│   └── agent-dashboard.json    ← agent-dashboard.json
├── logs/                       (created automatically)
└── README.md
```

### Step 3: Set API Key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Step 4: Run Everything

```bash
docker-compose up --build
```

### Step 5: Access the UIs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Agent App** | http://localhost:8501 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **InfluxDB** | http://localhost:8086 | admin / adminpassword |

### ⚠️ Step 6: Generate Some Data!

> **Important:** Dashboards will be empty until you use the agent!

1. Open http://localhost:8501
2. **Send a few chat messages** (e.g., "Hello", "What's 2+2?", "Tell me a joke")
3. Each message generates metrics: tokens, latency, cost
4. Now check Grafana - you'll see data!

---

## What Gets Tracked

### API Call Metrics (`api_call`)

| Field | Description |
|-------|-------------|
| `model` | Model used (tag) |
| `input_tokens` | Input token count |
| `output_tokens` | Output token count |
| `total_tokens` | Total tokens |
| `latency_ms` | Request latency |
| `cost_usd` | Estimated cost |
| `success` | Success/failure (tag) |

### Tool Usage Metrics (`tool_use`)

| Field | Description |
|-------|-------------|
| `tool` | Tool name (tag) |
| `latency_ms` | Execution time |
| `success` | Success/failure (tag) |
| `error` | Error message if failed |

### Session Metrics (`session`)

| Field | Description |
|-------|-------------|
| `session_id` | Session identifier (tag) |
| `event` | start/end/message (tag) |
| `duration_seconds` | Session duration |
| `message_count` | Messages in session |

### Error Tracking (`error`)

| Field | Description |
|-------|-------------|
| `type` | Error type (tag) |
| `component` | Component that errored (tag) |
| `message` | Error message |

---

## Structured Logs

Logs are written as JSON to `logs/agent.log` and shipped to Loki:

```json
{
  "timestamp": "2026-02-12T14:30:00.000Z",
  "level": "INFO",
  "message": "API call completed",
  "event": "api_call",
  "model": "claude-sonnet-4-20250514",
  "input_tokens": 150,
  "output_tokens": 300,
  "latency_ms": 450.5,
  "cost_usd": 0.00495,
  "success": true
}
```

---

## Grafana Dashboard

The pre-built dashboard includes:

### Top Row - Key Metrics
- Total API Calls
- Total Tokens Used
- Total Cost ($)
- Average Latency

### Middle Row - Time Series
- Tokens Over Time
- Latency Over Time

### Bottom Row - Logs
- Live log stream from Loki

---

## Using in Your Own Agent

### 1. Add Metrics Collection

```python
from metrics_collector import get_collector, track_api_call

metrics = get_collector()

# Track an API call
with track_api_call("claude-sonnet-4-20250514") as result:
    response = claude.messages.create(...)
    result["input_tokens"] = response.usage.input_tokens
    result["output_tokens"] = response.usage.output_tokens

# Track a tool
from metrics_collector import track_tool

with track_tool("my_tool"):
    do_something()

# Or use decorator
from metrics_collector import track_function

@track_function("my_tool")
def my_function():
    pass
```

### 2. Add Structured Logging

```python
from structured_logger import get_logger

logger = get_logger()

# Standard logging
logger.info("Something happened", extra_field="value")

# Agent-specific logging
logger.log_api_call(
    model="claude-sonnet-4-20250514",
    input_tokens=100,
    output_tokens=200,
    latency_ms=500,
    success=True
)

logger.log_tool_use(
    tool="web_search",
    latency_ms=230,
    success=True
)
```

---

## Docker Commands

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f observable-agent

# Stop everything
docker-compose down

# Stop and remove volumes (resets all data)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

---

## Troubleshooting

### "No data in Grafana dashboards"

**Most common cause:** You haven't chatted with the agent yet!

1. Open http://localhost:8501
2. Send a few messages
3. Check Grafana again (set time range to "Last 15 minutes")

### Diagnostic Commands

**Check all services running:**
```bash
docker-compose ps
```

Expected output - all services "Up":
```
NAME               STATUS         PORTS
grafana            Up            0.0.0.0:3000->3000/tcp
influxdb           Up            0.0.0.0:8086->8086/tcp
loki               Up            0.0.0.0:3100->3100/tcp
observable-agent   Up            0.0.0.0:8501->8501/tcp
promtail           Up
```

**Test InfluxDB connection from agent:**
```bash
docker exec -it observable-agent python -c "
from metrics_collector import get_collector
c = get_collector()
print('Connected:', c.is_connected())
"
```

**Query InfluxDB for data:**
```bash
docker exec influxdb influx query \
  'from(bucket:"agent-metrics") |> range(start: -1h) |> limit(n:5)' \
  --org learn-agentic \
  --token my-super-secret-token
```

**Check if bucket exists:**
```bash
docker exec influxdb influx bucket list \
  --org learn-agentic \
  --token my-super-secret-token
```

**Query Loki for logs:**
```bash
curl -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="observable-agent"}' \
  --data-urlencode 'limit=5' | jq '.data.result'
```

**Check for errors across all services:**
```bash
docker-compose logs | grep -i error
```

### "Cannot connect to InfluxDB"
```bash
docker-compose logs influxdb
```

### "InfluxDB shows 'skipping setup'"

Old data in volume. Clear it:
```bash
docker-compose down -v
docker-compose up --build
```

### "Dashboard name cannot be same as folder"

The dashboard JSON title conflicts with folder name. Fixed in latest version - re-download `agent-dashboard.json`.

### "Promtail: empty ring" error

Loki wasn't ready when Promtail started. It auto-retries - wait 30 seconds or:
```bash
docker-compose restart promtail
```

### Reset everything
```bash
docker-compose down -v
docker-compose up --build
```

---

## Cost Tracking

The agent calculates costs based on Claude's pricing:
- Input: $3 per 1M tokens ($0.000003/token)
- Output: $15 per 1M tokens ($0.000015/token)

View costs in:
- Grafana dashboard (Total Cost panel)
- InfluxDB (query `cost_usd` field)
- Agent UI (per-message and session totals)

---

## Learning Outcomes

- ✅ Time-series databases (InfluxDB)
- ✅ Log aggregation (Loki + Promtail)
- ✅ Dashboard creation (Grafana)
- ✅ Structured logging patterns
- ✅ Metrics collection in Python
- ✅ Cost tracking for AI applications
- ✅ Docker Compose orchestration

---

## Extending the Project

Ideas for enhancement:
1. **Alerting** - Set up Grafana alerts for high costs or errors
2. **More metrics** - Track memory usage, custom business metrics
3. **Tracing** - Add OpenTelemetry for distributed tracing
4. **Retention policies** - Configure data retention in InfluxDB
5. **Export** - Export dashboards and configs for reuse

---

## Known Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Empty Grafana dashboards | No data generated yet | Chat with the agent first! |
| "skipping setup" in InfluxDB | Old volume data | `docker-compose down -v` |
| "empty ring" in Promtail | Loki not ready | Auto-retries, or restart Promtail |
| "Dashboard name same as folder" | JSON title conflict | Fixed in latest version |
| Healthcheck failures | Containers lack curl | We use `service_started` instead |

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
