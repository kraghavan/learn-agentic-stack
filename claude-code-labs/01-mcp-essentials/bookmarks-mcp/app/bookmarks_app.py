"""
Bookmarks Manager UI - Project 2.1
Streamlit interface for the Bookmarks MCP Server.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from browsers.chrome import parse_chrome_bookmarks, search_chrome_bookmarks, get_chrome_folders
from browsers.firefox import parse_firefox_bookmarks, search_firefox_bookmarks, get_firefox_folders
from browsers.safari import parse_safari_bookmarks, search_safari_bookmarks, get_safari_folders

import json
import streamlit as st


# ============== BOOKMARK FUNCTIONS ==============

def get_all_bookmarks(browser: str = "all") -> list[dict]:
    """Get bookmarks from specified browser(s)."""
    bookmarks = []
    
    if browser in ["chrome", "all"]:
        bookmarks.extend(parse_chrome_bookmarks())
    
    if browser in ["firefox", "all"]:
        bookmarks.extend(parse_firefox_bookmarks())
    
    if browser in ["safari", "all"]:
        bookmarks.extend(parse_safari_bookmarks())
    
    return bookmarks


def search_all_bookmarks(
    query: str,
    browser: str = "all",
    search_titles: bool = True,
    search_urls: bool = True
) -> list[dict]:
    """Search bookmarks across browser(s)."""
    results = []
    
    if browser in ["chrome", "all"]:
        results.extend(search_chrome_bookmarks(
            query, search_titles=search_titles, search_urls=search_urls
        ))
    
    if browser in ["firefox", "all"]:
        results.extend(search_firefox_bookmarks(
            query, search_titles=search_titles, search_urls=search_urls
        ))
    
    if browser in ["safari", "all"]:
        results.extend(search_safari_bookmarks(
            query, search_titles=search_titles, search_urls=search_urls
        ))
    
    return results


def get_all_folders(browser: str = "all") -> list[dict]:
    """Get folder list from browser(s)."""
    folders = []
    
    if browser in ["chrome", "all"]:
        for f in get_chrome_folders():
            folders.append({"folder": f, "browser": "chrome"})
    
    if browser in ["firefox", "all"]:
        for f in get_firefox_folders():
            folders.append({"folder": f, "browser": "firefox"})
    
    if browser in ["safari", "all"]:
        for f in get_safari_folders():
            folders.append({"folder": f, "browser": "safari"})
    
    return folders


def export_bookmarks(bookmarks: list[dict], format: str = "json") -> str:
    """Export bookmarks to specified format."""
    if format == "json":
        return json.dumps(bookmarks, indent=2)
    
    elif format == "html":
        html = ['<!DOCTYPE NETSCAPE-Bookmark-file-1>']
        html.append('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">')
        html.append('<TITLE>Bookmarks</TITLE>')
        html.append('<H1>Bookmarks</H1>')
        html.append('<DL><p>')
        
        for bm in bookmarks:
            title = bm.get("title", "").replace('"', '&quot;')
            url = bm.get("url", "")
            html.append(f'  <DT><A HREF="{url}">{title}</A>')
        
        html.append('</DL><p>')
        return '\n'.join(html)
    
    elif format == "markdown":
        md = ['# Bookmarks\n']
        
        # Group by folder
        by_folder = {}
        for bm in bookmarks:
            folder = bm.get("folder", "Unfiled") or "Unfiled"
            if folder not in by_folder:
                by_folder[folder] = []
            by_folder[folder].append(bm)
        
        for folder, bms in sorted(by_folder.items()):
            md.append(f'\n## {folder}\n')
            for bm in bms:
                title = bm.get("title", "Untitled")
                url = bm.get("url", "")
                md.append(f'- [{title}]({url})')
        
        return '\n'.join(md)
    
    return ""


def get_stats(bookmarks: list[dict]) -> dict:
    """Get bookmark statistics."""
    stats = {
        "total": len(bookmarks),
        "by_browser": {},
        "by_folder": {},
        "top_domains": {}
    }
    
    for bm in bookmarks:
        # Count by browser
        b = bm.get("browser", "unknown")
        stats["by_browser"][b] = stats["by_browser"].get(b, 0) + 1
        
        # Count by folder
        f = bm.get("folder", "Unfiled") or "Unfiled"
        stats["by_folder"][f] = stats["by_folder"].get(f, 0) + 1
        
        # Extract domain
        url = bm.get("url", "")
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain:
                stats["top_domains"][domain] = stats["top_domains"].get(domain, 0) + 1
        except:
            pass
    
    # Keep only top 10 domains
    stats["top_domains"] = dict(
        sorted(stats["top_domains"].items(), key=lambda x: x[1], reverse=True)[:10]
    )
    
    return stats


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Bookmarks Manager",
    page_icon="🔖",
    layout="wide"
)

st.title("🔖 Bookmarks Manager")
st.markdown("*Unified browser bookmark management*")

# Initialize session state
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []
if "selected_browser" not in st.session_state:
    st.session_state.selected_browser = "all"

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Browser selection
    browser = st.selectbox(
        "Browser",
        ["all", "chrome", "firefox", "safari"],
        format_func=lambda x: x.title() if x != "all" else "All Browsers"
    )
    st.session_state.selected_browser = browser
    
    # Load bookmarks button
    if st.button("🔄 Load Bookmarks", type="primary", use_container_width=True):
        with st.spinner(f"Loading bookmarks from {browser}..."):
            st.session_state.bookmarks = get_all_bookmarks(browser)
        st.success(f"Loaded {len(st.session_state.bookmarks)} bookmarks")
    
    st.divider()
    
    # Search
    st.subheader("🔍 Search")
    search_query = st.text_input("Search bookmarks", placeholder="Enter search term...")
    search_titles = st.checkbox("Search titles", value=True)
    search_urls = st.checkbox("Search URLs", value=True)
    
    if search_query:
        with st.spinner("Searching..."):
            st.session_state.search_results = search_all_bookmarks(
                search_query,
                browser,
                search_titles,
                search_urls
            )
    
    st.divider()
    
    # Stats summary
    if st.session_state.bookmarks:
        st.subheader("📊 Summary")
        stats = get_stats(st.session_state.bookmarks)
        st.metric("Total Bookmarks", stats["total"])
        
        for b, count in stats["by_browser"].items():
            st.caption(f"{b.title()}: {count}")

# Main content
if not st.session_state.bookmarks:
    st.info("👈 Click 'Load Bookmarks' in the sidebar to get started.")
    
    st.markdown("""
    ### Supported Browsers
    
    | Browser | Location | Format |
    |---------|----------|--------|
    | **Chrome** | `~/Library/Application Support/Google/Chrome/Default/Bookmarks` | JSON |
    | **Firefox** | `~/Library/Application Support/Firefox/Profiles/*/places.sqlite` | SQLite |
    | **Safari** | `~/Library/Safari/Bookmarks.plist` | Binary Plist |
    
    ### Features
    
    - 📚 **Browse** - View all bookmarks from any browser
    - 🔍 **Search** - Find bookmarks by title or URL
    - 📁 **Folders** - Navigate bookmark folder structure
    - 📊 **Stats** - See bookmark statistics and top domains
    - 📤 **Export** - Export to JSON, HTML, or Markdown
    """)

else:
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Browse", "📁 Folders", "📊 Stats", "📤 Export"])
    
    with tab1:
        st.subheader("All Bookmarks")
        
        # Display bookmarks or search results
        if search_query and "search_results" in st.session_state:
            bookmarks_to_show = st.session_state.search_results
            st.caption(f"Found {len(bookmarks_to_show)} results for '{search_query}'")
        else:
            bookmarks_to_show = st.session_state.bookmarks
        
        # Pagination
        page_size = 20
        total_pages = (len(bookmarks_to_show) - 1) // page_size + 1 if bookmarks_to_show else 1
        page = st.selectbox("Page", range(1, total_pages + 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Display bookmarks
        for bm in bookmarks_to_show[start_idx:end_idx]:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                title = bm.get("title", "Untitled")[:50]
                url = bm.get("url", "")
                st.markdown(f"**[{title}]({url})**")
                st.caption(url[:60] + "..." if len(url) > 60 else url)
            
            with col2:
                folder = bm.get("folder", "Unfiled")
                st.caption(f"📁 {folder}")
            
            with col3:
                browser_icon = {"chrome": "🌐", "firefox": "🦊", "safari": "🧭"}.get(bm.get("browser", ""), "📑")
                st.caption(f"{browser_icon} {bm.get('browser', 'unknown').title()}")
            
            st.divider()
        
        st.caption(f"Showing {start_idx + 1}-{min(end_idx, len(bookmarks_to_show))} of {len(bookmarks_to_show)}")
    
    with tab2:
        st.subheader("Bookmark Folders")
        
        folders = get_all_folders(st.session_state.selected_browser)
        
        # Group by browser
        by_browser = {}
        for f in folders:
            b = f["browser"]
            if b not in by_browser:
                by_browser[b] = []
            by_browser[b].append(f["folder"])
        
        for browser_name, folder_list in by_browser.items():
            with st.expander(f"{browser_name.title()} ({len(folder_list)} folders)", expanded=True):
                for folder in folder_list:
                    # Count bookmarks in folder
                    count = len([b for b in st.session_state.bookmarks 
                                if b.get("folder", "").startswith(folder) and b.get("browser") == browser_name])
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"📁 {folder}")
                    with col2:
                        st.caption(f"{count} items")
    
    with tab3:
        st.subheader("Bookmark Statistics")
        
        stats = get_stats(st.session_state.bookmarks)
        
        # Overview metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Bookmarks", stats["total"])
        with col2:
            st.metric("Browsers", len(stats["by_browser"]))
        with col3:
            st.metric("Folders", len(stats["by_folder"]))
        
        st.divider()
        
        # Browser breakdown
        st.subheader("By Browser")
        for browser_name, count in sorted(stats["by_browser"].items(), key=lambda x: x[1], reverse=True):
            pct = count / stats["total"] * 100 if stats["total"] > 0 else 0
            st.progress(pct / 100, text=f"{browser_name.title()}: {count} ({pct:.1f}%)")
        
        st.divider()
        
        # Top domains
        st.subheader("Top Domains")
        for domain, count in stats["top_domains"].items():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"🌐 {domain}")
            with col2:
                st.write(count)
        
        st.divider()
        
        # Folder distribution
        st.subheader("Top Folders")
        sorted_folders = sorted(stats["by_folder"].items(), key=lambda x: x[1], reverse=True)[:10]
        for folder, count in sorted_folders:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📁 {folder[:40]}...")
            with col2:
                st.write(count)
    
    with tab4:
        st.subheader("Export Bookmarks")
        
        export_format = st.selectbox(
            "Export Format",
            ["json", "html", "markdown"],
            format_func=lambda x: {"json": "JSON", "html": "HTML (Netscape)", "markdown": "Markdown"}.get(x)
        )
        
        if st.button("📤 Generate Export", type="primary"):
            with st.spinner("Generating export..."):
                export_data = export_bookmarks(st.session_state.bookmarks, export_format)
            
            st.session_state.export_data = export_data
            st.session_state.export_format = export_format
        
        if "export_data" in st.session_state:
            st.divider()
            
            # Preview
            with st.expander("Preview", expanded=True):
                st.code(st.session_state.export_data[:2000] + "..." if len(st.session_state.export_data) > 2000 else st.session_state.export_data)
            
            # Download
            ext = {"json": "json", "html": "html", "markdown": "md"}.get(st.session_state.export_format, "txt")
            
            st.download_button(
                f"⬇️ Download bookmarks.{ext}",
                st.session_state.export_data,
                f"bookmarks.{ext}",
                "text/plain"
            )

# Footer
st.divider()
st.caption("Project 2.1 - Bookmarks MCP Server | learn-agentic-stack")
