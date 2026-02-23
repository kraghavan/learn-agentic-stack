

# learn-agentic-stack


# 🤖 learn-agentic-stack

> **The Blueprint for Engineering Agentic Systems**
> A hands-on learning laboratory for building production-grade AI agents using **Claude Code (Local/MCP)** and the **Google Cloud (Vertex AI) SDK**.

## 🎯 Overview
This repository is a structured pathway for software engineers to master the transition from simple LLM prompting to complex, autonomous agentic workflows. It leverages a dual-stack strategy designed for a local-to-cloud architecture.

### The Stack
* **Hardware:** Optimized for **Mac Mini M4** (Unified Memory handles local orchestration).
* **Local Intelligence:** Claude Code + Model Context Protocol (MCP).
* **Cloud Intelligence:** Google Cloud SDK (Vertex AI) using your **$300 GCP Credit**.
* **Memory:** RAG via local Vector DBs (Chroma) and GCP Vector Search.

---

## 🏗️ Repository Architecture

### 🛠️ `claude-code-labs/`
**Focus:** Local-first development and MCP tool-use.
* **01-mcp-essentials:** Building custom servers for local filesystem and SQLite access.
* **02-agent-handshakes:** Implementing A2A (Agent-to-Agent) communication patterns.
* *03-03-agentic-workhorses:* Using agents to autonomously generate React/Streamlit interfaces.

### ☁️ `google-sdk-labs/`
**Focus:** Enterprise integration using Python SDK and GCP.
* **01-vertex-foundations:** Mastering authentication (ADC vs. Service Accounts).
* **02-rag-storage:** Building long-term memory using BigQuery and Vector Search.
* **03-cloud-ops-bot:** An SRE-focused agent for monitoring Cloud Run and billing.

### 🧠 `shared-assets/`
* **prompts/:** Reusable system instructions and persona templates.
* **schemas/:** JSON definitions for consistent tool-calling.
* **data/:** Sample datasets for RAG testing.

---

## 🚀 Getting Started

### 1. Authentication & Safety
To protect your cloud credits, all experiments must be initialized via the setup script:
```bash
# Initialize gcloud and create a restricted Service Account

bash scripts/setup_env.sh

learn-agentic-stack/
├── .claude/                   # Global Claude settings & session data
├── CLAUDE.md                  # Project constitution & "The Truth" for Claude
│
├── 🛠️ claude-code-labs/       # FOLDER 1: Local-First & Multi-Agent Logic
│   ├── 01-mcp-essentials/     # Building custom MCP servers (Filesystem, SQLite)
│   ├── 02-agent-handshakes/   # Examples of A2A (Agent-to-Agent) communication
│   ├── 03-agentic-workhorses/     # Claude creating React/Streamlit UIs for agents
│   └── .mcp-config.json       # Project-specific MCP tool definitions
│
├── ☁️ google-sdk-labs/         # FOLDER 2: GCP & Enterprise Integration
│   ├── 01-vertex-foundations/ # Setting up Vertex AI & Auth with your Mac Mini
│   ├── 02-rag-storage/        # Vector Search & BigQuery as agent memory
│   ├── 03-cloud-ops-bot/      # SRE agent using SDK to monitor Cloud Run
│   └── sa-credentials.json.example # Template for Service Account auth
│
├── 🧠 shared-assets/          # Common resources used by both stacks
│   ├── prompts/               # Reusable system prompts & personas
│   ├── schemas/               # Shared JSON schemas for tool-calling
│   └── data/                  # Sample PDFs/Docs for RAG testing
│
├── scripts/                   # Setup scripts (Env checks, Gcloud init)
└── docker-compose.yml         # To spin up local Vector DBs (Chroma/Pinecone)


---

### 📂 Creating the Directory Structure
Once you've saved the `README.md`, you can run this command in your terminal to create the entire folder structure we discussed:

```bash
mkdir -p claude-code-labs/{01-mcp-essentials,02-agent-handshakes,03-agentic-workhorses} \
         google-sdk-labs/{01-vertex-foundations,02-rag-storage,03-cloud-ops-bot} \
         shared-assets/{prompts,schemas,data} \
         scripts .claude