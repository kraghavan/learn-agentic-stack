"""
Chrome Bookmark Parser
Reads bookmarks from Chrome's JSON file on macOS.
"""

import json
from pathlib import Path
from datetime import datetime


def get_chrome_bookmarks_path() -> Path:
    """Get the path to Chrome's bookmarks file on macOS."""
    home = Path.home()
    return home / "Library/Application Support/Google/Chrome/Default/Bookmarks"


def parse_chrome_bookmarks(bookmarks_path: Path = None) -> list[dict]:
    """
    Parse Chrome bookmarks from the JSON file.
    Returns list of bookmark dictionaries.
    """
    if bookmarks_path is None:
        bookmarks_path = get_chrome_bookmarks_path()
    
    if not bookmarks_path.exists():
        return []
    
    try:
        with open(bookmarks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    
    bookmarks = []
    
    def process_node(node: dict, folder_path: str = ""):
        """Recursively process bookmark nodes."""
        node_type = node.get("type", "")
        
        if node_type == "url":
            # This is a bookmark
            # Chrome stores timestamps as microseconds since Jan 1, 1601
            date_added = node.get("date_added", "0")
            try:
                # Convert Chrome timestamp to datetime
                timestamp = (int(date_added) - 11644473600000000) / 1000000
                if timestamp > 0:
                    date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                else:
                    date_str = ""
            except (ValueError, OSError):
                date_str = ""
            
            bookmarks.append({
                "id": node.get("id", ""),
                "title": node.get("name", "Untitled"),
                "url": node.get("url", ""),
                "folder": folder_path,
                "date_added": date_str,
                "browser": "chrome",
            })
        
        elif node_type == "folder":
            # This is a folder - process children
            folder_name = node.get("name", "")
            new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
            
            for child in node.get("children", []):
                process_node(child, new_path)
    
    # Process bookmark bar and other bookmarks
    roots = data.get("roots", {})
    
    if "bookmark_bar" in roots:
        process_node(roots["bookmark_bar"], "")
    
    if "other" in roots:
        process_node(roots["other"], "Other Bookmarks")
    
    if "synced" in roots:
        process_node(roots["synced"], "Mobile Bookmarks")
    
    return bookmarks


def get_chrome_folders(bookmarks: list[dict] = None) -> list[str]:
    """Get unique folder paths from bookmarks."""
    if bookmarks is None:
        bookmarks = parse_chrome_bookmarks()
    
    folders = set()
    for bm in bookmarks:
        if bm.get("folder"):
            folders.add(bm["folder"])
    
    return sorted(list(folders))


def search_chrome_bookmarks(
    query: str,
    bookmarks: list[dict] = None,
    search_titles: bool = True,
    search_urls: bool = True,
    folder_filter: str = None
) -> list[dict]:
    """
    Search Chrome bookmarks by title and/or URL.
    """
    if bookmarks is None:
        bookmarks = parse_chrome_bookmarks()
    
    query = query.lower()
    results = []
    
    for bm in bookmarks:
        # Apply folder filter
        if folder_filter and not bm.get("folder", "").startswith(folder_filter):
            continue
        
        # Search
        match = False
        if search_titles and query in bm.get("title", "").lower():
            match = True
        if search_urls and query in bm.get("url", "").lower():
            match = True
        
        if match:
            results.append(bm)
    
    return results


if __name__ == "__main__":
    # Test
    bookmarks = parse_chrome_bookmarks()
    print(f"Found {len(bookmarks)} Chrome bookmarks")
    
    for bm in bookmarks[:5]:
        print(f"  - {bm['title'][:50]} | {bm['folder']}")
