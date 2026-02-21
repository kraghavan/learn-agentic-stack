# 📜 Git Commit Summarizer

> **Project 1.4** from the Agentic AI Learning Pathway
> Generate release notes and changelogs from git history using Claude AI

## Overview

Analyze git commit history and generate professional release notes, changelogs, and summaries. The app classifies commits by type, groups them intelligently, and uses Claude AI to create human-readable documentation.

## Features

- [x] Parse git log with date filters
- [x] Auto-classify commits (feat, fix, chore, etc.)
- [x] Commit statistics and breakdown
- [x] Contributor analysis
- [x] AI-powered commit summary
- [x] Generate release notes
- [x] Generate Keep a Changelog entries
- [x] Export as markdown files
- [x] Docker support

## Setup

### Option A: Local Development (Recommended for this project)

```bash
cd claude-code-labs/01-mcp-essentials/git-summarizer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run
streamlit run app/git_summarizer.py
```

Open http://localhost:8501

Then enter the path to any git repo on your Mac, like:
- `/Users/yourname/projects/my-app`
- `~/KarthikaRepo/AI/learn-agentic-stack`

### Option B: Docker

```bash
# Edit docker-compose.yml to mount your repos directory
# Default: ~/KarthikaRepo:/repos

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Build and run
docker-compose up --build
```

In the UI, enter paths relative to the mount, like:
- `/repos/AI/learn-agentic-stack`

## Project Structure

```
git-summarizer/
├── app/
│   └── git_summarizer.py    # Main Streamlit app
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Usage

### 1. Select Repository
Enter the full path to any local git repository.

### 2. Choose Date Range
- Last 7/30/90 days
- All time
- Custom date range

### 3. Fetch Commits
Click to load commit history from the selected branch.

### 4. Generate Output

**📊 Overview Tab**
- Total commits, features, bug fixes
- Commits by type breakdown
- AI summary of changes
- Contributor list

**📝 Release Notes Tab**
- Enter version number
- Generate formatted release notes
- Download as RELEASE_NOTES.md

**📋 Changelog Tab**
- Enter version and date
- Generate Keep a Changelog format entry
- Download as CHANGELOG.md

**🔍 Raw Commits Tab**
- Browse all commits
- Filter by type
- View details

## Commit Classification

The app auto-detects commit types:

| Pattern | Type |
|---------|------|
| `feat:` or `feat(...)` | Feature |
| `fix:` or `bug:` | Bug Fix |
| `docs:` | Documentation |
| `refactor:` | Refactor |
| `test:` | Testing |
| `chore:` | Chore |
| Keywords: "add", "new" | Feature |
| Keywords: "fix", "patch" | Bug Fix |

## Example Output

### Release Notes
```markdown
# Version 1.2.0

## ✨ New Features
- Added user authentication system
- Implemented dark mode toggle

## 🐛 Bug Fixes
- Fixed crash when loading large files
- Resolved timezone display issues

## 👥 Contributors
- Alice Johnson (5 commits)
- Bob Smith (3 commits)
```

### Changelog
```markdown
## [1.2.0] - 2026-02-12

### Added
- User authentication system
- Dark mode toggle

### Fixed
- Crash when loading large files
- Timezone display issues
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GIT SUMMARIZER                           │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │  Streamlit   │      │  Claude API  │      │    Git    │  │
│  │     UI       │─────▶│  (summaries) │      │   Repo    │  │
│  │  Port 8501   │      │              │      │  (local)  │  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
│         │                                          ▲        │
│         │                                          │        │
│         └────────── subprocess (git) ──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Learning Outcomes

- ✅ Shell command execution (subprocess)
- ✅ Git log parsing
- ✅ Commit classification patterns
- ✅ AI text summarization
- ✅ Markdown generation
- ✅ Multiple output formats
- ✅ Docker volume mounts

## Tips

1. **Use Conventional Commits** - Projects with `feat:`, `fix:` prefixes get better classification
2. **Local is easier** - Running locally gives direct access to all repos
3. **Check date range** - Large repos may need narrower date filters

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
