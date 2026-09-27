from dataclasses import dataclass
from typing import Optional, Dict, Any
from core.http_client import fetch_profile_data

@dataclass
class ProfileSnapshot:
    """Strictly typed representation of an Instagram profile."""
    username: str
    full_name: str
    biography: str
    followers: int
    following: int
    is_private: bool
    is_verified: bool
    profile_pic_url: str
    external_url: Optional[str]

def parse_profile_data(raw_data: Dict[str, Any]) -> ProfileSnapshot:
    """Extracts relevant fields from Instagram's raw JSON response."""
    try:
        # Instagram's web endpoint typically nests user data under data -> user
        user_info = raw_data.get("data", {}).get("user", {})
        
        # Fallback for alternative JSON structures if the GraphQL schema changes
        if not user_info:
            user_info = raw_data.get("graphql", {}).get("user", {})
            
        return ProfileSnapshot(
            username=user_info.get("username", ""),
            full_name=user_info.get("full_name", ""),
            biography=user_info.get("biography", ""),
            followers=user_info.get("edge_followed_by", {}).get("count", 0),
            following=user_info.get("edge_follow", {}).get("count", 0),
            is_private=user_info.get("is_private", False),
            is_verified=user_info.get("is_verified", False),
            profile_pic_url=user_info.get("profile_pic_url_hd", ""),
            external_url=user_info.get("external_url")
        )
    except Exception as e:
        raise ValueError(f"Failed to parse JSON structure from Instagram: {e}")

def get_snapshot(username: str) -> ProfileSnapshot:
    """Fetches and parses a profile into a structured snapshot."""
    raw_data = fetch_profile_data(username)
    return parse_profile_data(raw_data)