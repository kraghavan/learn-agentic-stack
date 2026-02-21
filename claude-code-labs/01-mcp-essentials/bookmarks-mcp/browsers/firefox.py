"""
Firefox Bookmark Parser
Reads bookmarks from Firefox's places.sqlite on macOS.
"""

import sqlite3
import shutil
import tempfile
from pathlib import Path
from datetime import datetime


def get_firefox_profile_path() -> Path | None:
    """Get the path to Firefox's default profile on macOS."""
    home = Path.home()
    profiles_dir = home / "Library/Application Support/Firefox/Profiles"
    
    if not profiles_dir.exists():
        return None
    
    # Find default profile (usually ends with .default or .default-release)
    for profile in profiles_dir.iterdir():
        if profile.is_dir() and ("default" in profile.name.lower()):
            return profile
    
    # If no default found, return first profile
    profiles = [p for p in profiles_dir.iterdir() if p.is_dir()]
    return profiles[0] if profiles else None


def parse_firefox_bookmarks(profile_path: Path = None) -> list[dict]:
    """
    Parse Firefox bookmarks from places.sqlite.
    Returns list of bookmark dictionaries.
    
    Note: Firefox locks the database while running, so we copy it first.
    """
    if profile_path is None:
        profile_path = get_firefox_profile_path()
    
    if profile_path is None:
        return []
    
    db_path = profile_path / "places.sqlite"
    
    if not db_path.exists():
        return []
    
    # Copy database to temp location (Firefox locks it while running)
    bookmarks = []
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
            tmp_path = tmp.name
        
        shutil.copy2(db_path, tmp_path)
        
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        
        # Query bookmarks with their folder structure
        query = """
        SELECT 
            b.id,
            b.title,
            p.url,
            b.dateAdded,
            parent.title as folder
        FROM moz_bookmarks b
        LEFT JOIN moz_places p ON b.fk = p.id
        LEFT JOIN moz_bookmarks parent ON b.parent = parent.id
        WHERE b.type = 1  -- type 1 = bookmark
        AND p.url IS NOT NULL
        AND p.url NOT LIKE 'place:%'  -- Exclude internal URLs
        ORDER BY b.dateAdded DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            bm_id, title, url, date_added, folder = row
            
            # Convert Firefox timestamp (microseconds since epoch)
            try:
                if date_added:
                    timestamp = date_added / 1000000
                    date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                else:
                    date_str = ""
            except (ValueError, OSError):
                date_str = ""
            
            bookmarks.append({
                "id": str(bm_id),
                "title": title or "Untitled",
                "url": url or "",
                "folder": folder or "Unfiled",
                "date_added": date_str,
                "browser": "firefox",
            })
        
        conn.close()
        
    except Exception as e:
        print(f"Error reading Firefox bookmarks: {e}")
    
    finally:
        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except:
            pass
    
    return bookmarks


def get_firefox_folders(bookmarks: list[dict] = None) -> list[str]:
    """Get unique folder names from bookmarks."""
    if bookmarks is None:
        bookmarks = parse_firefox_bookmarks()
    
    folders = set()
    for bm in bookmarks:
        if bm.get("folder"):
            folders.add(bm["folder"])
    
    return sorted(list(folders))


def search_firefox_bookmarks(
    query: str,
    bookmarks: list[dict] = None,
    search_titles: bool = True,
    search_urls: bool = True,
    folder_filter: str = None
) -> list[dict]:
    """
    Search Firefox bookmarks by title and/or URL.
    """
    if bookmarks is None:
        bookmarks = parse_firefox_bookmarks()
    
    query = query.lower()
    results = []
    
    for bm in bookmarks:
        # Apply folder filter
        if folder_filter and bm.get("folder") != folder_filter:
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
    bookmarks = parse_firefox_bookmarks()
    print(f"Found {len(bookmarks)} Firefox bookmarks")
    
    for bm in bookmarks[:5]:
        print(f"  - {bm['title'][:50]} | {bm['folder']}")
