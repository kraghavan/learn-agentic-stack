# 📚 Personal Knowledge Base

> **Project 4.1** from the Agentic AI Learning Pathway
> Index and chat with your documents using RAG

## Overview

A full-featured personal knowledge base that lets you:
- Upload and index documents (PDF, Markdown, Code, Text)
- Search semantically across all your knowledge
- Chat with your documents with citations
- Visualize knowledge as a graph

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   PERSONAL KNOWLEDGE BASE                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    STREAMLIT UI                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │  Chat   │ │ Upload  │ │ Search  │ │  Graph  │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     RAG CHAT                             │   │
│  │  Query → Retrieve Context → Generate Answer → Citations  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│              ┌───────────────┴───────────────┐                 │
│              ▼                               ▼                 │
│  ┌─────────────────────┐        ┌─────────────────────┐        │
│  │   KNOWLEDGE BASE    │        │   DOCUMENT PROCESSOR │        │
│  │                     │        │                      │        │
│  │  • Store chunks     │        │  • PDF extraction    │        │
│  │  • Semantic search  │        │  • Markdown parsing  │        │
│  │  • Vector embeddings│        │  • Code chunking     │        │
│  │  • Citations        │        │  • Text splitting    │        │
│  └──────────┬──────────┘        └──────────────────────┘        │
│             │                                                   │
│             ▼                                                   │
│  ┌─────────────────────┐                                        │
│  │      ChromaDB       │                                        │
│  │  (Vector Database)  │                                        │
│  └─────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- [x] **Multi-format Support** - PDF, Markdown, Text, Code files
- [x] **Smart Chunking** - Sentence-aware, header-aware, code-aware
- [x] **Semantic Search** - Find relevant content by meaning
- [x] **RAG Chat** - Ask questions, get cited answers
- [x] **Knowledge Graph** - Visualize concepts and relationships
- [x] **Document Similarity** - Find related documents
- [x] **Persistent Storage** - Data survives restarts

## Quick Start

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs/03-production-agents
mkdir -p personal-kb
cd personal-kb
```

### Step 2: Copy Files

```
personal-kb/
├── document_processor.py   ← kb_document_processor.py
├── knowledge_base.py       ← kb_knowledge_base.py
├── rag_chat.py             ← kb_rag_chat.py
├── knowledge_graph.py      ← kb_knowledge_graph.py
├── kb_app.py               ← kb_app.py
├── requirements.txt        ← kb_requirements.txt
├── Dockerfile              ← kb_Dockerfile
├── docker-compose.yml      ← kb_docker_compose.yml
└── README.md
```

### Step 3: Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
streamlit run kb_app.py
```

### Step 4: Or Use Docker

```bash
export ANTHROPIC_API_KEY="your-key"
# recommanded here to capture and monitor each apps logs esp database
docker-compose up --build
```

Open http://localhost:8501

---

## Usage Guide

### 📤 Uploading Documents

1. Go to the **Upload** page
2. Drag & drop files or click to select
3. Click **Index** for each file
4. Documents are automatically chunked and embedded

**Supported formats:**
- PDF (`.pdf`)
- Markdown (`.md`)
- Text (`.txt`)
- Python (`.py`)
- JavaScript (`.js`, `.jsx`, `.ts`, `.tsx`)
- HTML (`.html`)
- Config files (`.json`, `.yaml`, `.yml`)

### 💬 Chatting with Documents

1. Go to the **Chat** page
2. Ask questions about your documents
3. Get answers with source citations
4. Click "Sources" to see which chunks were used

**Example questions:**
- "What are the main topics in my documents?"
- "Summarize the key points about X"
- "Compare how different documents discuss Y"

### 🔍 Semantic Search

1. Go to the **Search** page
2. Enter a search query
3. Adjust number of results and relevance threshold
4. Click on results to expand and see full content

### 🕸️ Knowledge Graph

1. Go to the **Graph** page
2. Choose **Concept Graph** to extract entities and relationships
3. Choose **Document Similarity** to see how documents relate

---

## Module Reference

### document_processor.py

```python
from document_processor import DocumentProcessor, Document

processor = DocumentProcessor(
    chunk_size=500,      # Target chunk size in chars
    chunk_overlap=50,    # Overlap between chunks
    min_chunk_size=100   # Minimum chunk size
)

# Process a file
doc = processor.process_file("paper.pdf")
print(f"Created {len(doc.chunks)} chunks")

# Process raw text
doc = processor.process_text("Your text here", "notes.txt")
```

### knowledge_base.py

```python
from knowledge_base import KnowledgeBase

kb = KnowledgeBase(persist_directory="./kb_data")

# Add document
kb.add_document(doc)

# Search
results = kb.search("machine learning", n_results=5)
for r in results:
    print(f"[{r.score:.2f}] {r.chunk.content[:100]}...")

# Get context for RAG
context, citations = kb.get_context_for_query("What is AI?")
```

### rag_chat.py

```python
from rag_chat import RAGChat

chat = RAGChat(kb)

# Simple query
answer = chat.ask("What are the main concepts?")

# Query with citations
response = chat.chat("Explain the architecture")
print(response.content)
print("Sources:", [c.format() for c in response.citations])
```

### knowledge_graph.py

```python
from knowledge_graph import KnowledgeGraphExtractor

extractor = KnowledgeGraphExtractor()

# Extract from text
graph = extractor.extract_from_text("Your document content...")

# Get Mermaid diagram
print(graph.to_mermaid())

# Get vis.js format for visualization
print(graph.to_vis_js())
```

---

## Chunking Strategies

### Text Documents
- Split by sentences
- Respect chunk size limits
- Add overlap between chunks

### Markdown Documents
- Split by headers (##, ###, etc.)
- Keep headers with their content
- Fall back to text chunking for large sections

### Code Files
- Try to split by functions/classes
- Fall back to line-based chunking
- Preserve code structure

---

## RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAG PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. USER QUERY                                                  │
│     "What is machine learning?"                                │
│                          │                                      │
│                          ▼                                      │
│  2. RETRIEVAL                                                   │
│     ┌──────────────────────────────────────┐                   │
│     │ ChromaDB semantic search              │                   │
│     │ → Find top N relevant chunks          │                   │
│     │ → Score by similarity                 │                   │
│     └──────────────────────────────────────┘                   │
│                          │                                      │
│                          ▼                                      │
│  3. CONTEXT BUILDING                                            │
│     ┌──────────────────────────────────────┐                   │
│     │ [Source 1: doc1.pdf]                  │                   │
│     │ Machine learning is a subset of AI... │                   │
│     │                                       │                   │
│     │ [Source 2: notes.md]                  │                   │
│     │ ML enables computers to learn...      │                   │
│     └──────────────────────────────────────┘                   │
│                          │                                      │
│                          ▼                                      │
│  4. GENERATION                                                  │
│     ┌──────────────────────────────────────┐                   │
│     │ Claude + Context + Query              │                   │
│     │ → Generate answer                     │                   │
│     │ → Include citations [Source N]        │                   │
│     └──────────────────────────────────────┘                   │
│                          │                                      │
│                          ▼                                      │
│  5. RESPONSE                                                    │
│     "Machine learning is a subset of AI    │                   │
│      that enables... [Source 1]"           │                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Token Usage

| Operation | Input | Output | Cost |
|-----------|-------|--------|------|
| Chat (per question) | ~1,500 | ~500 | ~$0.012 |
| Graph extraction | ~2,000 | ~500 | ~$0.014 |
| Document summary | ~3,000 | ~500 | ~$0.017 |

**Note:** ChromaDB embeddings are local (free) - no API cost.

---

## Data Persistence

Data is stored in:
```
kb_data/
├── chroma.sqlite3          # Vector database
├── document_index.json     # Document metadata
└── [uuid]/                 # Embedding files
```

**Docker:** Data persists in the `kb_data` named volume.

**Local:** Data persists in `./kb_data` directory.

---

## Learning Outcomes

- ✅ Document ingestion and chunking strategies
- ✅ Vector embeddings with ChromaDB
- ✅ Semantic search implementation
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ Citation tracking and formatting
- ✅ Knowledge graph extraction
- ✅ Full-stack knowledge management UI

---

## Extending the Project

Ideas for enhancement:

1. **Web Scraping** - Add URLs as documents
2. **OCR Support** - Extract text from images
3. **Auto-tagging** - LLM-generated tags for documents
4. **Export** - Export knowledge to various formats
5. **Multi-user** - Add authentication and user separation
6. **API** - REST API for programmatic access

---

## Troubleshooting

### "No module named 'chromadb'"
```bash
pip install chromadb
```

### "PDF extraction failed"
```bash
pip install PyMuPDF
```

### "Out of memory" with large PDFs
- Increase Docker memory limit
- Or process PDFs in smaller batches

### Slow search
- ChromaDB builds index on first query
- Subsequent queries are faster

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
