"""
Markdown Note Taker - Project 1.3
A persistent note-taking agent with tagging, search, and AI-powered features.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
from anthropic import Anthropic

# Initialize Claude client
client = Anthropic()

# Notes directory
NOTES_DIR = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

# ============== NOTE FUNCTIONS ==============

def get_all_notes() -> list[dict]:
    """Get all notes with metadata."""
    notes = []
    for file in NOTES_DIR.glob("*.md"):
        content = file.read_text()
        metadata = extract_metadata(content)
        notes.append({
            "filename": file.name,
            "path": str(file),
            "title": metadata.get("title", file.stem),
            "tags": metadata.get("tags", []),
            "created": metadata.get("created", ""),
            "modified": datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            "content": content,
            "preview": get_preview(content),
        })
    return sorted(notes, key=lambda x: x["modified"], reverse=True)


def extract_metadata(content: str) -> dict:
    """Extract YAML frontmatter from markdown."""
    metadata = {}
    
    # Check for YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle tags as list
                    if key == "tags":
                        if value.startswith("[") and value.endswith("]"):
                            # Parse as list: [tag1, tag2] or [tag1,tag2]
                            inner = value[1:-1]  # Remove brackets
                            metadata[key] = [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
                        else:
                            metadata[key] = [t.strip() for t in value.split(",") if t.strip()]
                    else:
                        metadata[key] = value
    
    # Extract tags from content (hashtags)
    hashtags = re.findall(r'#(\w+)', content)
    if hashtags and "tags" not in metadata:
        metadata["tags"] = list(set(hashtags))
    elif hashtags:
        metadata["tags"] = list(set(metadata.get("tags", []) + hashtags))
    
    return metadata


def get_preview(content: str, max_length: int = 150) -> str:
    """Get a preview of the note content."""
    # Remove frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
    
    # Remove markdown formatting
    content = re.sub(r'#+ ', '', content)
    content = re.sub(r'\*\*|\*|__', '', content)
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
    content = content.strip()
    
    if len(content) > max_length:
        return content[:max_length] + "..."
    return content


def get_all_tags() -> dict[str, int]:
    """Get all tags with counts."""
    tag_counts = {}
    for note in get_all_notes():
        for tag in note.get("tags", []):
            tag = tag.lower()
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))


def create_note(title: str, content: str, tags: list[str]) -> str:
    """Create a new note with frontmatter."""
    # Generate filename from title
    filename = re.sub(r'[^\w\s-]', '', title.lower())
    filename = re.sub(r'[\s]+', '-', filename)
    filename = f"{filename}.md"
    
    # Ensure unique filename
    filepath = NOTES_DIR / filename
    counter = 1
    while filepath.exists():
        filepath = NOTES_DIR / f"{filename[:-3]}-{counter}.md"
        counter += 1
    
    # Create frontmatter
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    frontmatter = f"""---
title: {title}
created: {now}
tags: [{', '.join(tags)}]
---

"""
    
    full_content = frontmatter + content
    filepath.write_text(full_content)
    
    return str(filepath)


def update_note(filepath: str, content: str) -> None:
    """Update an existing note."""
    Path(filepath).write_text(content)


def delete_note(filepath: str) -> None:
    """Delete a note."""
    Path(filepath).unlink()


def search_notes(query: str) -> list[dict]:
    """Search notes by content and tags."""
    query = query.lower()
    results = []
    
    for note in get_all_notes():
        score = 0
        
        # Search in title
        if query in note["title"].lower():
            score += 10
        
        # Search in tags
        for tag in note.get("tags", []):
            if query in tag.lower():
                score += 5
        
        # Search in content
        if query in note["content"].lower():
            score += 1
            # Bonus for multiple occurrences
            score += note["content"].lower().count(query)
        
        if score > 0:
            note["score"] = score
            results.append(note)
    
    return sorted(results, key=lambda x: x["score"], reverse=True)


def get_daily_note() -> tuple[str, str]:
    """Get or create today's daily note."""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"daily-{today}.md"
    filepath = NOTES_DIR / filename
    
    if filepath.exists():
        return str(filepath), filepath.read_text()
    else:
        # Create new daily note
        content = f"""---
title: Daily Note - {today}
created: {datetime.now().strftime("%Y-%m-%d %H:%M")}
tags: [daily]
---

# {datetime.now().strftime("%A, %B %d, %Y")}

## Quick Capture

"""
        filepath.write_text(content)
        return str(filepath), content


# ============== AI FUNCTIONS ==============

def ai_extract_tags(content: str) -> list[str]:
    """Use Claude to extract relevant tags from content."""
    prompt = f"""Analyze this note and suggest 3-5 relevant tags. Return ONLY a JSON array of lowercase tag strings, nothing else.

Note content:
{content[:1000]}

Example response: ["python", "learning", "tutorial"]"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        tags = json.loads(response.content[0].text)
        return tags
    except:
        return []


def ai_summarize_note(content: str) -> str:
    """Use Claude to summarize a note."""
    prompt = f"""Summarize this note in 2-3 sentences:

{content[:2000]}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def ai_find_related(content: str, all_notes: list[dict]) -> list[str]:
    """Use Claude to find related notes."""
    note_summaries = "\n".join([
        f"- {n['filename']}: {n['preview']}" 
        for n in all_notes[:20]
    ])
    
    prompt = f"""Given this note content:
{content[:500]}

And these other notes:
{note_summaries}

Which 3 notes are most related? Return ONLY a JSON array of filenames, nothing else.
Example: ["note1.md", "note2.md", "note3.md"]"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        return json.loads(response.content[0].text)
    except:
        return []


def ai_expand_note(content: str, instruction: str) -> str:
    """Use Claude to expand or improve a note."""
    prompt = f"""Here's a note:

{content}

User instruction: {instruction}

Provide the expanded/improved content in markdown format."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Markdown Notes",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Markdown Note Taker")
st.markdown("*AI-powered note taking with tags and search*")

# Initialize session state
if "current_note" not in st.session_state:
    st.session_state.current_note = None
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# Sidebar
with st.sidebar:
    st.header("📚 Notes")
    
    # Quick capture
    with st.expander("⚡ Quick Capture", expanded=True):
        quick_note = st.text_area("Quick note", height=80, key="quick_capture")
        if st.button("Add to Daily Note", use_container_width=True):
            if quick_note:
                filepath, content = get_daily_note()
                new_content = content + f"\n- {quick_note}"
                update_note(filepath, new_content)
                st.success("Added to daily note!")
                st.rerun()
    
    st.divider()
    
    # Search
    search_query = st.text_input("🔍 Search notes", placeholder="Search...")
    
    st.divider()
    
    # Tags
    st.subheader("🏷️ Tags")
    tags = get_all_tags()
    if tags:
        selected_tag = st.selectbox(
            "Filter by tag",
            ["All"] + list(tags.keys()),
            format_func=lambda x: f"{x} ({tags[x]})" if x in tags else x
        )
    else:
        selected_tag = "All"
    
    st.divider()
    
    # Notes list
    st.subheader("📄 All Notes")
    
    notes = get_all_notes()
    
    # Apply filters
    if search_query:
        notes = search_notes(search_query)
    elif selected_tag != "All":
        notes = [n for n in notes if selected_tag.lower() in [t.lower() for t in n.get("tags", [])]]
    
    for note in notes[:20]:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📄 {note['title'][:25]}", key=note['filename'], use_container_width=True):
                st.session_state.current_note = note
                st.session_state.edit_mode = False
        with col2:
            st.caption(note['modified'][:10])

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    # New note button
    if st.button("➕ New Note", type="primary"):
        st.session_state.current_note = "new"
        st.session_state.edit_mode = True
    
    st.divider()
    
    # Display current note or create new
    if st.session_state.current_note == "new":
        st.subheader("Create New Note")
        
        new_title = st.text_input("Title", placeholder="My New Note")
        new_tags_input = st.text_input("Tags (comma-separated)", placeholder="python, learning, ideas")
        new_content = st.text_area("Content", height=400, placeholder="Write your note here...")
        
        col_save, col_ai = st.columns(2)
        
        with col_save:
            if st.button("💾 Save Note", type="primary", use_container_width=True):
                if new_title and new_content:
                    tags = [t.strip() for t in new_tags_input.split(",") if t.strip()]
                    filepath = create_note(new_title, new_content, tags)
                    st.success(f"Note saved: {filepath}")
                    st.session_state.current_note = None
                    st.rerun()
                else:
                    st.error("Title and content required")
        
        with col_ai:
            if st.button("🤖 AI Suggest Tags", use_container_width=True):
                if new_content:
                    with st.spinner("Analyzing..."):
                        suggested_tags = ai_extract_tags(new_content)
                    st.info(f"Suggested tags: {', '.join(suggested_tags)}")
    
    elif st.session_state.current_note:
        note = st.session_state.current_note
        
        # View/Edit toggle
        col_title, col_actions = st.columns([3, 1])
        
        with col_title:
            st.subheader(note["title"])
        
        with col_actions:
            if st.button("✏️ Edit" if not st.session_state.edit_mode else "👁️ View"):
                st.session_state.edit_mode = not st.session_state.edit_mode
                st.rerun()
        
        # Tags display
        if note.get("tags"):
            st.markdown(" ".join([f"`#{tag}`" for tag in note["tags"]]))
        
        st.caption(f"Modified: {note['modified']}")
        
        st.divider()
        
        if st.session_state.edit_mode:
            # Edit mode
            edited_content = st.text_area(
                "Edit content",
                value=note["content"],
                height=400,
                key="edit_area"
            )
            
            col_save, col_delete = st.columns(2)
            
            with col_save:
                if st.button("💾 Save Changes", type="primary", use_container_width=True):
                    update_note(note["path"], edited_content)
                    st.success("Saved!")
                    st.session_state.edit_mode = False
                    st.rerun()
            
            with col_delete:
                if st.button("🗑️ Delete Note", use_container_width=True):
                    delete_note(note["path"])
                    st.session_state.current_note = None
                    st.rerun()
        else:
            # View mode - render markdown
            # Remove frontmatter for display
            content = note["content"]
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2]
            
            st.markdown(content)
    
    else:
        # Welcome screen
        st.info("👈 Select a note from the sidebar or create a new one.")
        
        # Show daily note shortcut
        if st.button("📅 Open Today's Daily Note"):
            filepath, content = get_daily_note()
            notes = get_all_notes()
            for n in notes:
                if n["path"] == filepath:
                    st.session_state.current_note = n
                    st.rerun()

with col2:
    if st.session_state.current_note and st.session_state.current_note != "new":
        note = st.session_state.current_note
        
        st.subheader("🤖 AI Tools")
        
        if st.button("📋 Summarize", use_container_width=True):
            with st.spinner("Summarizing..."):
                summary = ai_summarize_note(note["content"])
            st.info(summary)
        
        if st.button("🔗 Find Related", use_container_width=True):
            with st.spinner("Finding related..."):
                all_notes = get_all_notes()
                related = ai_find_related(note["content"], all_notes)
            if related:
                st.markdown("**Related notes:**")
                for r in related:
                    st.markdown(f"- {r}")
            else:
                st.info("No related notes found")
        
        st.divider()
        
        st.subheader("✨ Expand Note")
        expand_instruction = st.text_input("Instruction", placeholder="Add more examples")
        if st.button("Expand", use_container_width=True):
            if expand_instruction:
                with st.spinner("Expanding..."):
                    expanded = ai_expand_note(note["content"], expand_instruction)
                st.markdown("**Suggested expansion:**")
                st.markdown(expanded)

# Footer
st.divider()
st.caption("Project 1.3 - Markdown Note Taker | learn-agentic-stack")