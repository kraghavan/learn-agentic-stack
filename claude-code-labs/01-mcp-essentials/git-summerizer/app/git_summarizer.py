"""
Git Commit Summarizer - Project 1.4
Generate release notes and changelogs from git history using Claude AI.
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st
from anthropic import Anthropic

# Initialize Claude client
client = Anthropic()

# ============== GIT FUNCTIONS ==============

def is_git_repo(path: str) -> bool:
    """Check if path is a valid git repository."""
    git_dir = Path(path) / ".git"
    return git_dir.exists() and git_dir.is_dir()


def run_git_command(repo_path: str, command: list[str]) -> tuple[str, str]:
    """
    Run a git command in the specified repository.
    Returns (stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git"] + command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", "Command timed out"
    except Exception as e:
        return "", str(e)


def get_commits(
    repo_path: str,
    since: str = None,
    until: str = None,
    branch: str = "HEAD",
    max_commits: int = 100
) -> list[dict]:
    """
    Get commits from git log.
    Returns list of commit dictionaries.
    """
    # Build git log command
    # Format: hash|author|date|subject|body
    format_str = "%H|%an|%ai|%s|%b|||COMMIT_END|||"
    
    command = [
        "log",
        branch,
        f"--max-count={max_commits}",
        f"--pretty=format:{format_str}"
    ]
    
    if since:
        command.append(f"--since={since}")
    if until:
        command.append(f"--until={until}")
    
    stdout, stderr = run_git_command(repo_path, command)
    
    if stderr and not stdout:
        return []
    
    commits = []
    raw_commits = stdout.split("|||COMMIT_END|||")
    
    for raw in raw_commits:
        raw = raw.strip()
        if not raw:
            continue
        
        parts = raw.split("|", 4)
        if len(parts) >= 4:
            commit = {
                "hash": parts[0][:8],  # Short hash
                "full_hash": parts[0],
                "author": parts[1],
                "date": parts[2][:10],  # Just the date part
                "subject": parts[3],
                "body": parts[4] if len(parts) > 4 else "",
                "type": classify_commit(parts[3]),
            }
            commits.append(commit)
    
    return commits


def classify_commit(subject: str) -> str:
    """
    Classify commit by conventional commit type.
    """
    subject_lower = subject.lower()
    
    # Check for conventional commit prefix
    prefixes = {
        "feat": "feature",
        "fix": "bugfix",
        "bug": "bugfix",
        "docs": "documentation",
        "doc": "documentation",
        "style": "style",
        "refactor": "refactor",
        "perf": "performance",
        "test": "testing",
        "chore": "chore",
        "build": "build",
        "ci": "ci",
        "revert": "revert",
        "merge": "merge",
        "wip": "wip",
    }
    
    for prefix, commit_type in prefixes.items():
        if subject_lower.startswith(f"{prefix}:") or subject_lower.startswith(f"{prefix}("):
            return commit_type
    
    # Keyword detection
    if any(word in subject_lower for word in ["add", "new", "create", "implement"]):
        return "feature"
    if any(word in subject_lower for word in ["fix", "bug", "patch", "resolve"]):
        return "bugfix"
    if any(word in subject_lower for word in ["update", "upgrade", "bump"]):
        return "update"
    if any(word in subject_lower for word in ["remove", "delete", "drop"]):
        return "removal"
    if any(word in subject_lower for word in ["refactor", "clean", "improve"]):
        return "refactor"
    if "merge" in subject_lower:
        return "merge"
    
    return "other"


def get_branches(repo_path: str) -> list[str]:
    """Get list of branches in the repository."""
    stdout, _ = run_git_command(repo_path, ["branch", "-a"])
    branches = []
    for line in stdout.split("\n"):
        branch = line.strip().replace("* ", "")
        if branch and not branch.startswith("remotes/"):
            branches.append(branch)
    return branches


def get_tags(repo_path: str) -> list[str]:
    """Get list of tags in the repository."""
    stdout, _ = run_git_command(repo_path, ["tag", "-l", "--sort=-creatordate"])
    return [t.strip() for t in stdout.split("\n") if t.strip()]


def get_repo_info(repo_path: str) -> dict:
    """Get basic repository information."""
    # Get remote URL
    remote_stdout, _ = run_git_command(repo_path, ["remote", "get-url", "origin"])
    
    # Get current branch
    branch_stdout, _ = run_git_command(repo_path, ["branch", "--show-current"])
    
    # Get total commit count
    count_stdout, _ = run_git_command(repo_path, ["rev-list", "--count", "HEAD"])
    
    return {
        "remote": remote_stdout.strip(),
        "current_branch": branch_stdout.strip(),
        "total_commits": count_stdout.strip(),
    }


# ============== AI FUNCTIONS ==============

def ai_summarize_commits(commits: list[dict]) -> str:
    """Use Claude to generate a summary of commits."""
    commit_text = "\n".join([
        f"- [{c['type']}] {c['subject']} ({c['author']}, {c['date']})"
        for c in commits[:50]  # Limit for context
    ])
    
    prompt = f"""Analyze these git commits and provide a brief executive summary (3-5 sentences) of what changed:

{commit_text}

Focus on the main themes and significant changes. Be concise."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def ai_generate_release_notes(commits: list[dict], version: str = None) -> str:
    """Use Claude to generate formatted release notes."""
    commit_text = "\n".join([
        f"- {c['hash']} | {c['type']} | {c['subject']} | {c['author']}"
        for c in commits[:50]
    ])
    
    version_str = f"Version {version}" if version else "Release"
    
    prompt = f"""Generate professional release notes in markdown format for these commits.

Commits:
{commit_text}

Requirements:
1. Start with "# {version_str}" header
2. Group changes by type (Features, Bug Fixes, Improvements, etc.)
3. Write user-friendly descriptions (not just commit messages)
4. Include contributor acknowledgments at the end
5. Keep it concise but informative

Output markdown only, no explanations."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def ai_generate_changelog_entry(commits: list[dict], version: str, date: str) -> str:
    """Generate a CHANGELOG.md entry for a version."""
    commit_text = "\n".join([
        f"- [{c['type']}] {c['subject']}"
        for c in commits[:30]
    ])
    
    prompt = f"""Generate a CHANGELOG entry in Keep a Changelog format for version {version} dated {date}.

Commits:
{commit_text}

Use these categories: Added, Changed, Deprecated, Removed, Fixed, Security
Output markdown only. Start with "## [{version}] - {date}" """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Git Commit Summarizer",
    page_icon="📜",
    layout="wide"
)

st.title("📜 Git Commit Summarizer")
st.markdown("*Generate release notes and changelogs from git history*")

# Initialize session state
if "commits" not in st.session_state:
    st.session_state.commits = []
if "repo_path" not in st.session_state:
    st.session_state.repo_path = ""

# Sidebar
with st.sidebar:
    st.header("⚙️ Repository Settings")
    
    # Repository path input
    repo_path = st.text_input(
        "Repository Path",
        value=st.session_state.repo_path or os.getcwd(),
        help="Path to local git repository"
    )
    
    # Validate repo
    if repo_path:
        if is_git_repo(repo_path):
            st.success("✓ Valid git repository")
            st.session_state.repo_path = repo_path
            
            # Show repo info
            info = get_repo_info(repo_path)
            st.caption(f"Branch: `{info['current_branch']}`")
            st.caption(f"Commits: {info['total_commits']}")
        else:
            st.error("✗ Not a git repository")
    
    st.divider()
    
    # Date range
    st.subheader("📅 Date Range")
    
    date_option = st.radio(
        "Time period",
        ["Last 7 days", "Last 30 days", "Last 90 days", "All time", "Custom"]
    )
    
    today = datetime.now()
    
    if date_option == "Last 7 days":
        since_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        until_date = None
    elif date_option == "Last 30 days":
        since_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        until_date = None
    elif date_option == "Last 90 days":
        since_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        until_date = None
    elif date_option == "All time":
        since_date = None
        until_date = None
    else:
        col1, col2 = st.columns(2)
        with col1:
            since_input = st.date_input("From", today - timedelta(days=30))
            since_date = since_input.strftime("%Y-%m-%d")
        with col2:
            until_input = st.date_input("To", today)
            until_date = until_input.strftime("%Y-%m-%d")
    
    st.divider()
    
    # Branch selection
    if is_git_repo(repo_path):
        branches = get_branches(repo_path)
        selected_branch = st.selectbox("Branch", branches if branches else ["main"])
    else:
        selected_branch = "main"
    
    st.divider()
    
    # Fetch commits button
    if st.button("🔍 Fetch Commits", type="primary", use_container_width=True):
        if is_git_repo(repo_path):
            with st.spinner("Fetching commits..."):
                commits = get_commits(
                    repo_path,
                    since=since_date,
                    until=until_date,
                    branch=selected_branch
                )
                st.session_state.commits = commits
            st.success(f"Found {len(commits)} commits")
        else:
            st.error("Please enter a valid repository path")

# Main content
if st.session_state.commits:
    commits = st.session_state.commits
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📝 Release Notes", "📋 Changelog", "🔍 Raw Commits"])
    
    with tab1:
        st.subheader("Commit Overview")
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        # Count by type
        type_counts = {}
        for c in commits:
            t = c["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        with col1:
            st.metric("Total Commits", len(commits))
        with col2:
            st.metric("Features", type_counts.get("feature", 0))
        with col3:
            st.metric("Bug Fixes", type_counts.get("bugfix", 0))
        with col4:
            st.metric("Other", sum(v for k, v in type_counts.items() if k not in ["feature", "bugfix"]))
        
        st.divider()
        
        # Type breakdown
        st.subheader("Commits by Type")
        
        for commit_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"**{commit_type.title()}**")
            with col2:
                st.progress(count / len(commits), text=f"{count} commits")
        
        st.divider()
        
        # AI Summary
        st.subheader("🤖 AI Summary")
        if st.button("Generate Summary"):
            with st.spinner("Analyzing commits..."):
                summary = ai_summarize_commits(commits)
            st.info(summary)
        
        # Contributors
        st.divider()
        st.subheader("👥 Contributors")
        
        authors = {}
        for c in commits:
            authors[c["author"]] = authors.get(c["author"], 0) + 1
        
        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True):
            st.write(f"- **{author}**: {count} commits")
    
    with tab2:
        st.subheader("Release Notes Generator")
        
        version = st.text_input("Version Number", placeholder="1.0.0")
        
        if st.button("🚀 Generate Release Notes", type="primary"):
            with st.spinner("Generating release notes..."):
                release_notes = ai_generate_release_notes(commits, version)
            
            st.session_state.release_notes = release_notes
        
        if "release_notes" in st.session_state:
            st.divider()
            
            # Preview
            st.markdown("### Preview")
            st.markdown(st.session_state.release_notes)
            
            st.divider()
            
            # Download
            st.download_button(
                "⬇️ Download RELEASE_NOTES.md",
                st.session_state.release_notes,
                "RELEASE_NOTES.md",
                "text/markdown"
            )
    
    with tab3:
        st.subheader("Changelog Generator")
        
        col1, col2 = st.columns(2)
        with col1:
            cl_version = st.text_input("Version", placeholder="1.0.0", key="cl_version")
        with col2:
            cl_date = st.date_input("Release Date", datetime.now())
        
        if st.button("📋 Generate Changelog Entry"):
            with st.spinner("Generating changelog..."):
                changelog = ai_generate_changelog_entry(
                    commits,
                    cl_version or "Unreleased",
                    cl_date.strftime("%Y-%m-%d")
                )
            
            st.session_state.changelog = changelog
        
        if "changelog" in st.session_state:
            st.divider()
            
            # Preview
            st.markdown("### Preview")
            st.markdown(st.session_state.changelog)
            
            st.divider()
            
            # Download
            st.download_button(
                "⬇️ Download CHANGELOG.md",
                st.session_state.changelog,
                "CHANGELOG.md",
                "text/markdown"
            )
    
    with tab4:
        st.subheader("Raw Commits")
        
        # Filter by type
        types = list(set(c["type"] for c in commits))
        selected_types = st.multiselect("Filter by type", types, default=types)
        
        filtered = [c for c in commits if c["type"] in selected_types]
        
        # Display as table
        for c in filtered:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.code(c["hash"])
            with col2:
                type_badge = f"`{c['type']}`"
                st.markdown(f"{type_badge} {c['subject']}")
            with col3:
                st.caption(f"{c['author'][:15]}")
                st.caption(c["date"])
            st.divider()

else:
    # Welcome screen
    st.info("👈 Enter a repository path and click 'Fetch Commits' to get started.")
    
    st.markdown("""
    ### How it works
    
    1. **Select Repository** - Enter path to any local git repo
    2. **Choose Date Range** - Filter commits by time period
    3. **Fetch Commits** - Load commit history
    4. **Generate Output** - Create release notes or changelog
    
    ### Features
    
    - 📊 **Overview** - Stats, type breakdown, contributors
    - 📝 **Release Notes** - AI-generated user-friendly release notes
    - 📋 **Changelog** - Keep a Changelog format entries
    - 🔍 **Raw Commits** - Browse and filter all commits
    
    ### Commit Type Detection
    
    Automatically classifies commits by:
    - Conventional commit prefixes (`feat:`, `fix:`, etc.)
    - Keywords in commit messages
    """)

# Footer
st.divider()
st.caption("Project 1.4 - Git Commit Summarizer | learn-agentic-stack")
