import time
import random
import sqlite3
import json
import requests
from datetime import datetime, timedelta

def init_db():
    """Initialize a persistent SQLite cache for profile data."""
    conn = sqlite3.connect('anusint_cache.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile_cache (
            username TEXT PRIMARY KEY,
            data TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_cached_profile(username: str, ttl_hours: int = 24):
    """Retrieve profile from cache if it is newer than the TTL."""
    conn = sqlite3.connect('anusint_cache.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data, timestamp FROM profile_cache WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        cached_time = datetime.fromisoformat(row[1])
        if datetime.now() - cached_time < timedelta(hours=ttl_hours):
            return json.loads(row[0])
    return None

def save_to_cache(username: str, data: dict):
    """Save fresh profile data to the SQLite cache."""
    conn = sqlite3.connect('anusint_cache.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO profile_cache (username, data, timestamp)
        VALUES (?, ?, ?)
    ''', (username, json.dumps(data), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def fetch_profile_data(username: str, max_retries: int = 4) -> dict:
    """Fetches profile data implementing caching, backoff, jitter, and throttling."""
    
    cached_data = get_cached_profile(username)
    if cached_data:
        # Returns immediately if valid cache exists, saving API calls
        return cached_data

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    })

    base_delay = 2

    for attempt in range(max_retries):
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        try:
            # Mandatory throttling to mimic human browsing behavior
            throttle_delay = random.uniform(5.0, 15.0)
            time.sleep(throttle_delay)

            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                save_to_cache(username, data)
                return data
                
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait_time = int(retry_after)
                else:
                    # Double the base delay and add jitter
                    wait_time = (base_delay ** attempt) + random.uniform(1.0, 4.0)
                
                time.sleep(wait_time)
                continue
                
            elif response.status_code == 401:
                raise Exception("HTTP 401: Login-gating triggered. Instagram requires authentication for this endpoint.")
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Network failure after {max_retries} attempts: {e}")
            time.sleep(base_delay)

    raise Exception("Rate limit block persists after maximum retries.")