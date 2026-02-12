# 📁 File Organizer Agent

> **Project 1.1** from the Agentic AI Learning Pathway
> First working agent with Claude API + Streamlit UI

## Overview

This agent scans a folder, classifies files by type, and organizes them into subfolders. It uses Claude AI to provide intelligent recommendations.

## Features

- [x] Scan folder recursively
- [x] Classify files by type (code, docs, images, data)
- [x] Preview changes before executing (dry run)
- [x] Execute organization
- [x] Claude AI analysis and recommendations
- [x] Generate downloadable report
- [x] Streamlit UI with folder picker

## Setup

### 1. Prerequisites

```bash
# Python 3.10+
python3 --version

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 2. Install Dependencies

```bash
cd claude-code-labs/01-mcp-essentials/file-organizer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Create Test Files (Optional)

```bash
mkdir -p test-mess
cd test-mess
touch report.pdf notes.txt image1.png image2.jpg
touch script.py data.csv README.md app.js styles.css
touch presentation.pptx budget.xlsx photo.jpeg
touch config.json package.json index.html
cd ..
```

### 4. Run the App

```bash
streamlit run app/file_organizer.py
```

Open http://localhost:8501 in your browser.

## Usage

1. **Enter folder path** in the sidebar (default: `./test-mess`)
2. **Click "Scan Folder"** to analyze the directory
3. **Review the classification** in the table
4. **Click "Ask Claude"** for AI recommendations (optional)
5. **Preview changes** with the dry run button
6. **Execute** to actually move files
7. **Download report** for your records

## File Categories

| Category | Extensions |
|----------|------------|
| Code | .py, .js, .ts, .html, .css, .json, .yaml, etc. |
| Documents | .pdf, .docx, .txt, .md, .pptx, .xlsx, .csv |
| Images | .png, .jpg, .jpeg, .gif, .svg, .webp |
| Data | .json, .xml, .csv, .sql, .db |
| Archives | .zip, .tar, .gz, .rar, .7z |
| Other | Everything else |

## Project Structure

```
file-organizer/
├── app/
│   └── file_organizer.py    # Main Streamlit app
├── test-mess/               # Test files (gitignored)
├── requirements.txt
├── README.md
└── .gitignore
```

## Learning Outcomes

- ✅ Claude API basics (messages.create)
- ✅ Streamlit UI development
- ✅ File system operations in Python
- ✅ Session state management
- ✅ Dry run pattern (preview before execute)

## Next Steps

After completing this project:
1. Add recursive folder scanning option
2. Add undo functionality
3. Add custom classification rules
4. Connect to actual MCP filesystem server (Project 1.2+)

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*