import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Setup a global, cross-platform user directory for the cache
CACHE_DIR = Path.home() / ".anusint"
CACHE_FILE = CACHE_DIR / "profile_cache.db"

def init_db() -> None:
    """Initialize a persistent SQLite cache for profile data."""
    # Ensure the ~/.anusint directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Context manager automatically handles opening and closing the DB connection
    with sqlite3.connect(CACHE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_cache (
                username TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME
            )
        ''')
        conn.commit()

def get_cached_profile(username: str, ttl_hours: int = 24) -> Optional[Dict[str, Any]]:
    """Retrieve a profile from the cache if it is newer than the TTL."""
    init_db()
    with sqlite3.connect(CACHE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT data, timestamp FROM profile_cache WHERE username = ?', (username,))
        row = cursor.fetchone()

    if row:
        cached_data, timestamp_str = row
        cached_time = datetime.fromisoformat(timestamp_str)
        # Check if the cache has expired
        if datetime.now() - cached_time < timedelta(hours=ttl_hours):
            return json.loads(cached_data)
    
    return None

def save_to_cache(username: str, data: Dict[str, Any]) -> None:
    """Save fresh profile data to the SQLite cache."""
    init_db()
    with sqlite3.connect(CACHE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO profile_cache (username, data, timestamp)
            VALUES (?, ?, ?)
        ''', (username, json.dumps(data), datetime.now().isoformat()))
        conn.commit()