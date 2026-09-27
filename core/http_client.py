import time
import random
import requests
from typing import Dict, Any

from core.cache import get_cached_profile, save_to_cache

class InstagramRateLimitError(Exception):
    """Raised when rate limits cannot be bypassed after max retries."""
    pass

class InstagramAuthError(Exception):
    """Raised when hitting a hard HTTP 401 Login-Gating block."""
    pass

def fetch_profile_data(username: str, max_retries: int = 4, ttl_hours: int = 24) -> Dict[str, Any]:
    """
    Fetches profile data implementing caching, backoff, jitter, and throttling.
    """
    # 1. Cache Check: Return instantly if we have recent data
    cached_data = get_cached_profile(username, ttl_hours=ttl_hours)
    if cached_data:
        return cached_data

    # 2. Session Consistency: Reuse TCP connection and headers
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-IG-App-ID": "936619743392459",  # Standard Instagram Web App ID
    })

    base_delay = 2.0

    for attempt in range(max_retries):
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        try:
            # 3. Request Throttling: Mandatory delay mimics human browsing
            throttle_delay = random.uniform(5.0, 12.0)
            time.sleep(throttle_delay)

            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                save_to_cache(username, data)
                return data
                
            elif response.status_code == 429:
                # 4. Respect Retry-After Headers or fallback to Backoff + Jitter
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait_time = int(retry_after)
                else:
                    wait_time = (base_delay ** attempt) + random.uniform(1.0, 4.0)
                
                time.sleep(wait_time)
                continue
                
            elif response.status_code == 401:
                # 5. Handle undocumented login-gating
                raise InstagramAuthError("HTTP 401: Login-gating triggered. Endpoint requires authentication.")
            
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Network failure after {max_retries} attempts: {e}")
            # Slight jitter on standard network failures as well
            time.sleep(base_delay + random.uniform(0.5, 2.0))

    raise InstagramRateLimitError("Rate limit block persists after maximum retries. IP might be temporarily flagged.")