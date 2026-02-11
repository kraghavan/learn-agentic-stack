# 🤖 Project Constitution: learn-agentic-stack

## 🎯 Context
This repository is an educational blueprint for building Agentic AI systems. It bridges local orchestration (Mac Mini M4) with cloud scale (GCP).

## 🛠️ Tech Stack & Roles
- **Primary LLMs:** Claude 3.5 Sonnet (Local/Agentic) & Gemini 1.5 Flash (Cloud/SDK)
- **Infrastructure:** Google Cloud Platform (Vertex AI, Cloud Run, BigQuery)
- **Frameworks:** MCP (Model Context Protocol), Python SDK, CrewAI/LangGraph
- **Local Env:** Mac Mini M4, zsh, uv/pip

## 📜 Behavior Guidelines (The Rules)
- **Budget Guardian:** ALWAYS check the GCP billing/budget status before provisioning new cloud resources. We have a $300 limit.
- **Model Selection:** Prefer `gemini-1.5-flash` for high-volume tasks or initial testing. Reserve `pro` models for complex reasoning.
- **MCP usage:** When working in `claude-code-labs/`, prioritize creating modular MCP servers over monolithic scripts.
- **A2A Logic:** When implementing Agent-to-Agent handshakes, use structured JSON for message passing.

## 📁 Critical Path Rules
- **`claude-code-labs/`**: Focus on local tool-calling and filesystem interaction.
- **`google-sdk-labs/`**: Use Service Account authentication (`sa-credentials.json`). Never hardcode keys.
- **`shared-assets/`**: Centralize all system prompts here to maintain persona consistency.

## ⌨️ Custom Commands & Skills
- `uv run scripts/setup_env.sh`: Refresh environment variables and GCP auth.
- `gcloud billing budgets describe`: Manual check of the project's financial health.
- `/init`: Run this within sub-folders to generate specific local context.

## 🏗️ Architecture Standard
We use a **"Platform-Agent"** approach: Agents should not just perform tasks, but provision the infrastructure (Queues, DBs) they need to succeed.