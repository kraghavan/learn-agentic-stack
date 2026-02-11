# ☁️ Google SDK & GCP Learning Pathway

> **The Enterprise Agent Strategy**
> Transitioning from Local Prototype → Production Cloud Agent
> Focus: Google Gen AI SDK, Vertex AI, and GCP Infrastructure

---

## 📊 Overview

| Duration | 3-4 months (Syncs with Claude Code Plan) |
|----------|-----------------------------------------|
| Stack    | Google Cloud SDK (Python), Vertex AI, Cloud Run |
| Credits  | Targeted usage of your **$300 GCP Credit** |
| End Goal | Domain-Specific Agent Factory |

### Philosophy
- **Cloud-Native** - Use managed services to reduce "infrastructure toil".
- **Production-Ready** - Focus on IAM, security, and scalability from day one.
- **Cost-Optimized** - Leveraging "Scale-to-Zero" architecture to preserve credits.
- **Observability** - Integrating Cloud Logging and Trace for agent debugging.

---

## 🏗️ TIER 1: Cloud Foundations
*Duration: 1-2 weeks | Complexity: ⭐*

### Project 1.1: Multi-Modal "GCS Sentinel"
**Goal:** Process files automatically using Vertex AI as they land in Cloud Storage.

| Component | Details |
|-----------|---------|
| **SDK** | `google-cloud-aiplatform`, `google-cloud-storage` |
| **Trigger** | Cloud Functions (Event-driven) |
| **Model** | Gemini 1.5 Flash (Cost-effective multi-modal) |

**Features:**
- [ ] Auto-summarize PDFs/Images uploaded to a GCS bucket.
- [ ] Write summary metadata back to the file objects.
- [ ] Send an email alert if a "critical" document is detected.

---

### Project 1.2: "BigQuery Insights" Agent
**Goal:** Natural Language → SQL generator for BigQuery datasets.

| Component | Details |
|-----------|---------|
| **SDK** | `google-cloud-bigquery` |
| **Tool** | Vertex AI Function Calling |
| **Input** | "How many users signed up last Tuesday?" |

**Features:**
- [ ] Schema discovery (Agent reads table metadata).
- [ ] Secure SQL generation (No hardcoded credentials).
- [ ] Data visualization (Agent generates a chart link).

---

## 🔧 TIER 2: Enterprise Tooling
*Duration: 2-3 weeks | Complexity: ⭐⭐*

### Project 2.1: Remote MCP Server on Cloud Run
**Goal:** Deploy your first serverless MCP tool to GCP.

| Component | Details |
|-----------|---------|
| **Host** | Cloud Run (Containerized) |
| **Auth** | Secret Manager for API keys |
| **Tool** | A "Cloud Health" tool that reports on GCP project quotas. |

**Learning Outcomes:**
- Containerizing an agent with Docker.
- Implementing authentication via IAM Service Accounts.

---

### Project 2.2: Vertex AI Search "Grounding"
**Goal:** Build an enterprise RAG system without managing a Vector DB.

| Component | Details |
|-----------|---------|
| **RAG** | Vertex AI Search (Managed RAG Engine) |
| **Data** | Your local research PDFs uploaded to GCP. |
| **UI** | Streamlit app connecting via the SDK. |

---

## 🤝 TIER 3: Cloud Observability & Ops
*Duration: 2-3 weeks | Complexity: ⭐⭐⭐*

### Project 3.1: The "Self-Healing" SRE Bot
**Goal:** Monitor Cloud Run logs and automate incident responses.

| Component | Details |
|-----------|---------|
| **Monitor** | Cloud Logging & Cloud Monitoring |
| **Action** | SDK calls to restart or scale services. |
| **Pattern** | Loop pattern for iterative remediation. |

---

## 🚀 TIER 4: Multi-Agent Cloud Workflows
*Duration: 3-4 weeks | Complexity: ⭐⭐⭐⭐*

### Project 4.1: The A2A Infrastructure Manager
**Goal:** Two agents collaborating via the **Agent2Agent (A2A)** protocol.

| Component | Details |
|-----------|---------|
| **Agent A** | **Architect:** Drafts a Cloud Run deployment spec. |
| **Agent B** | **Operator:** Validates spec and runs `gcloud` commands. |
| **Runtime** | Vertex AI Agent Engine. |

---

## 🧠 TIER 5: The CAPSTONE
### Project 5.4: Domain-Specific Agent Factory ⭐
**Goal:** Your ultimate project. A "Meta-Agent" that builds, evaluates, and deploys other agents.

- **Automated Fine-Tuning:** Uses Vertex AI to tune small models for specific tasks.
- **Automatic Eval:** Uses Vertex AI Evaluation service to check for hallucinations.
- **Deployment:** Automatically pushes new agents to Cloud Run.

---

## 📅 GCP Credit Management Plan

1. **Safety First:** Set a hard budget alert at $50 in the GCP Console.
2. **Flash Preference:** Use `gemini-1.5-flash` for 90% of development.
3. **Clean Up:** Use the `scripts/teardown.sh` script to delete unused Cloud Run services daily.

---

## 📝 Progress Tracking

- [ ] 1.1 Multi-Modal Sentinel
- [ ] 1.2 BigQuery NL Interface
- [ ] 2.1 Cloud Run MCP Server
- [ ] 2.2 Vertex Search Grounding
- [ ] 3.1 Self-Healing SRE Bot
- [ ] 4.1 A2A Infrastructure Manager
- [ ] 5.4 Domain-Specific Agent Factory

---
*Last Updated: February 2026*