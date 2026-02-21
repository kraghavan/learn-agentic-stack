"""
File Organizer Agent - Project 1.1
Uses Claude API to classify and organize files in a directory.
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import streamlit as st
from anthropic import Anthropic

# Initialize Claude client
client = Anthropic()

# File type classifications
FILE_CATEGORIES = {
    "code": [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".yaml", ".yml", ".sh", ".bash", ".go", ".rs", ".java", ".c", ".cpp", ".h"],
    "documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pptx", ".ppt", ".xlsx", ".xls", ".csv"],
    "images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff"],
    "data": [".json", ".xml", ".csv", ".sql", ".db", ".sqlite"],
    "archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
}


def scan_directory(folder_path: str) -> list[dict]:
    """Scan a directory and return file information."""
    files = []
    path = Path(folder_path)
    
    if not path.exists():
        return []
    
    for item in path.rglob("*"):
        if item.is_file():
            files.append({
                "name": item.name,
                "path": str(item),
                "extension": item.suffix.lower(),
                "size": item.stat().st_size,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
            })
    
    return files


def classify_file(extension: str) -> str:
    """Classify a file based on its extension."""
    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category
    return "other"


def get_organization_plan(files: list[dict]) -> dict:
    """Create an organization plan for the files."""
    plan = {
        "code": [],
        "documents": [],
        "images": [],
        "data": [],
        "archives": [],
        "other": [],
    }
    
    for file in files:
        category = classify_file(file["extension"])
        plan[category].append(file)
    
    return plan


def ask_claude_for_analysis(files: list[dict]) -> str:
    """Ask Claude to analyze the files and suggest organization."""
    file_summary = "\n".join([f"- {f['name']} ({f['extension']})" for f in files[:50]])  # Limit to 50 files
    
    prompt = f"""Analyze these files and provide a brief organization recommendation:

Files found:
{file_summary}

Provide:
1. A summary of what types of files are present
2. Any patterns you notice (project files, related files, etc.)
3. Suggestions for organization beyond just file type (e.g., by project, by date)

Keep your response concise (under 200 words).
"""
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def execute_organization(source_folder: str, plan: dict, dry_run: bool = True) -> list[str]:
    """Execute the organization plan. Returns list of actions taken."""
    actions = []
    source_path = Path(source_folder)
    
    for category, files in plan.items():
        if not files:
            continue
            
        # Create category folder
        category_folder = source_path / category
        
        if not dry_run:
            category_folder.mkdir(exist_ok=True)
        
        for file in files:
            file_path = Path(file["path"])
            new_path = category_folder / file["name"]
            
            action = f"{'[DRY RUN] ' if dry_run else ''}Move: {file['name']} → {category}/"
            actions.append(action)
            
            if not dry_run and file_path.exists():
                shutil.move(str(file_path), str(new_path))
    
    return actions


def generate_report(plan: dict, actions: list[str], source_folder: str) -> str:
    """Generate a markdown report of the organization."""
    report = f"""# File Organization Report

**Source Folder:** `{source_folder}`  
**Organized On:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

| Category | File Count |
|----------|------------|
"""
    
    total = 0
    for category, files in plan.items():
        count = len(files)
        total += count
        if count > 0:
            report += f"| {category.capitalize()} | {count} |\n"
    
    report += f"| **Total** | **{total}** |\n"
    
    report += "\n## Actions Taken\n\n"
    for action in actions:
        report += f"- {action}\n"
    
    report += "\n## Files by Category\n\n"
    for category, files in plan.items():
        if files:
            report += f"### {category.capitalize()}\n"
            for f in files:
                report += f"- `{f['name']}`\n"
            report += "\n"
    
    return report


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="File Organizer Agent",
    page_icon="📁",
    layout="wide"
)

st.title("📁 File Organizer Agent")
st.markdown("*Powered by Claude AI*")

# Sidebar for folder selection
with st.sidebar:
    st.header("⚙️ Settings")
    
    folder_path = st.text_input(
        "Folder Path",
        value="./test-mess",
        help="Path to the folder you want to organize"
    )
    
    scan_button = st.button("🔍 Scan Folder", use_container_width=True)
    
    st.divider()
    
    st.markdown("### Categories")
    for cat, exts in FILE_CATEGORIES.items():
        with st.expander(f"📂 {cat.capitalize()}"):
            st.code(", ".join(exts))

# Main content area
if scan_button or "files" in st.session_state:
    
    if scan_button:
        with st.spinner("Scanning folder..."):
            files = scan_directory(folder_path)
            st.session_state["files"] = files
            st.session_state["plan"] = get_organization_plan(files)
            st.session_state["folder_path"] = folder_path
    
    files = st.session_state.get("files", [])
    plan = st.session_state.get("plan", {})
    
    if not files:
        st.warning(f"No files found in `{folder_path}`. Check the path and try again.")
    else:
        # Display scan results
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📊 Found {len(files)} files")
            
            # Show plan as a table
            plan_data = []
            for category, category_files in plan.items():
                for f in category_files:
                    plan_data.append({
                        "File": f["name"],
                        "Type": f["extension"],
                        "Category": category.capitalize(),
                        "Size": f"{f['size']} bytes"
                    })
            
            if plan_data:
                st.dataframe(plan_data, use_container_width=True)
        
        with col2:
            st.subheader("📈 Category Summary")
            for category, category_files in plan.items():
                if category_files:
                    st.metric(
                        label=category.capitalize(),
                        value=len(category_files)
                    )
        
        st.divider()
        
        # Claude Analysis
        st.subheader("🤖 Claude's Analysis")
        
        if st.button("Ask Claude for Recommendations"):
            with st.spinner("Claude is analyzing..."):
                try:
                    analysis = ask_claude_for_analysis(files)
                    st.session_state["analysis"] = analysis
                except Exception as e:
                    st.error(f"Error calling Claude API: {e}")
        
        if "analysis" in st.session_state:
            st.markdown(st.session_state["analysis"])
        
        st.divider()
        
        # Action buttons
        st.subheader("🚀 Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👁️ Preview Changes (Dry Run)", use_container_width=True):
                actions = execute_organization(
                    st.session_state["folder_path"],
                    plan,
                    dry_run=True
                )
                st.session_state["actions"] = actions
                st.session_state["executed"] = False
        
        with col2:
            if st.button("✅ Execute Organization", type="primary", use_container_width=True):
                actions = execute_organization(
                    st.session_state["folder_path"],
                    plan,
                    dry_run=False
                )
                st.session_state["actions"] = actions
                st.session_state["executed"] = True
                st.success("Files organized successfully!")
        
        # Show actions
        if "actions" in st.session_state and st.session_state["actions"]:
            st.subheader("📋 Action Log")
            
            if not st.session_state.get("executed", False):
                st.info("This is a preview. Click 'Execute Organization' to apply changes.")
            
            for action in st.session_state["actions"]:
                st.text(action)
        
        st.divider()
        
        # Generate Report
        if st.button("📝 Generate Report"):
            actions = st.session_state.get("actions", [])
            report = generate_report(plan, actions, st.session_state["folder_path"])
            st.session_state["report"] = report
        
        if "report" in st.session_state:
            st.subheader("📄 Organization Report")
            st.markdown(st.session_state["report"])
            
            st.download_button(
                label="⬇️ Download Report",
                data=st.session_state["report"],
                file_name="organization_report.md",
                mime="text/markdown"
            )

else:
    # Welcome screen
    st.info("👈 Enter a folder path in the sidebar and click 'Scan Folder' to begin.")
    
    st.markdown("""
    ### How it works
    
    1. **Scan** - Point to any folder on your Mac
    2. **Preview** - See how files will be organized
    3. **Analyze** - Get Claude's recommendations
    4. **Execute** - Organize with one click
    5. **Report** - Download a summary
    
    ### Categories
    
    Files are automatically sorted into:
    - 📝 **Code** - Python, JavaScript, HTML, CSS, etc.
    - 📄 **Documents** - PDFs, Word docs, spreadsheets
    - 🖼️ **Images** - PNG, JPG, SVG, etc.
    - 📊 **Data** - JSON, CSV, SQL
    - 📦 **Archives** - ZIP, TAR, etc.
    - 📁 **Other** - Everything else
    """)

# Footer
st.divider()
st.caption("Project 1.1 - File Organizer Agent | learn-agentic-stack")