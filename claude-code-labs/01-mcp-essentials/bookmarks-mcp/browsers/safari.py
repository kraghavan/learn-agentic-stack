"""
Safari Bookmark Parser
Reads bookmarks from Safari's Bookmarks.plist on macOS.
"""

import plistlib
from pathlib import Path
from datetime import datetime


def get_safari_bookmarks_path() -> Path:
    """Get the path to Safari's bookmarks file on macOS."""
    home = Path.home()
    return home / "Library/Safari/Bookmarks.plist"


def parse_safari_bookmarks(bookmarks_path: Path = None) -> list[dict]:
    """
    Parse Safari bookmarks from the plist file.
    Returns list of bookmark dictionaries.
    
    Note: Safari's Bookmarks.plist is a binary plist file.
    """
    if bookmarks_path is None:
        bookmarks_path = get_safari_bookmarks_path()
    
    if not bookmarks_path.exists():
        return []
    
    try:
        with open(bookmarks_path, 'rb') as f:
            plist = plistlib.load(f)
    except Exception as e:
        print(f"Error reading Safari bookmarks: {e}")
        return []
    
    bookmarks = []
    
    def process_node(node: dict, folder_path: str = ""):
        """Recursively process bookmark nodes."""
        node_type = node.get("WebBookmarkType", "")
        
        if node_type == "WebBookmarkTypeLeaf":
            # This is a bookmark
            uri_dict = node.get("URIDictionary", {})
            
            bookmarks.append({
                "id": node.get("WebBookmarkUUID", ""),
                "title": uri_dict.get("title", node.get("Title", "Untitled")),
                "url": node.get("URLString", ""),
                "folder": folder_path,
                "date_added": "",  # Safari doesn't easily expose this
                "browser": "safari",
            })
        
        elif node_type == "WebBookmarkTypeList":
            # This is a folder
            folder_name = node.get("Title", "")
            
            # Skip special folders but process their children
            if folder_name in ["BookmarksBar", "BookmarksMenu"]:
                new_path = folder_name.replace("Bookmarks", "")
            elif folder_name:
                new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
            else:
                new_path = folder_path
            
            for child in node.get("Children", []):
                process_node(child, new_path)
        
        elif node_type == "WebBookmarkTypeProxy":
            # Reading list or other special items - skip
            pass
    
    # Start processing from root
    for child in plist.get("Children", []):
        process_node(child, "")
    
    return bookmarks


def get_safari_folders(bookmarks: list[dict] = None) -> list[str]:
    """Get unique folder paths from bookmarks."""
    if bookmarks is None:
        bookmarks = parse_safari_bookmarks()
    
    folders = set()
    for bm in bookmarks:
        if bm.get("folder"):
            folders.add(bm["folder"])
    
    return sorted(list(folders))


def search_safari_bookmarks(
    query: str,
    bookmarks: list[dict] = None,
    search_titles: bool = True,
    search_urls: bool = True,
    folder_filter: str = None
) -> list[dict]:
    """
    Search Safari bookmarks by title and/or URL.
    """
    if bookmarks is None:
        bookmarks = parse_safari_bookmarks()
    
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
    bookmarks = parse_safari_bookmarks()
    print(f"Found {len(bookmarks)} Safari bookmarks")
    
    for bm in bookmarks[:5]:
        print(f"  - {bm['title'][:50]} | {bm['folder']}")
