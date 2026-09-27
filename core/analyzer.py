import difflib
from typing import Dict, Any
from core.scanner import ProfileSnapshot

def string_similarity(a: str, b: str) -> float:
    """Returns a similarity ratio between 0.0 and 1.0 for two strings."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    # Lowercase comparison to catch case-shifted impersonations (e.g., 'Target' vs 'target')
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

def analyze_impersonation(original: ProfileSnapshot, suspect: ProfileSnapshot) -> Dict[str, Any]:
    """
    Compares a suspect profile against an original profile to calculate an impersonation risk score.
    """
    name_sim = string_similarity(original.full_name, suspect.full_name)
    bio_sim = string_similarity(original.biography, suspect.biography)
    username_sim = string_similarity(original.username, suspect.username)
    
    # Flag: High follower count on original, very low on suspect
    follower_ratio_flag = (original.followers > 1000) and (suspect.followers < original.followers * 0.05)
    
    # Weighted risk calculation (0.0 to 100.0)
    risk_score = 0.0
    
    # Names carry heavy weight in impersonation
    if name_sim > 0.9:
        risk_score += 40.0
    else:
        risk_score += (name_sim * 30.0)
        
    # Copied bios are a massive red flag
    risk_score += (bio_sim * 40.0)
    
    # Similar usernames add to the score
    risk_score += (username_sim * 20.0)
    
    # Contextual penalty: If it looks like them but lacks the audience
    if follower_ratio_flag and risk_score > 30.0:
        risk_score += 10.0 

    # Cap score at 100
    risk_score = min(risk_score, 100.0)
    
    # Determine severity tier
    risk_level = "LOW"
    if risk_score > 75.0:
        risk_level = "CRITICAL"
    elif risk_score > 50.0:
        risk_level = "HIGH"
    elif risk_score > 30.0:
        risk_level = "MODERATE"

    return {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 2),
        "metrics": {
            "name_similarity": round(name_sim, 2),
            "bio_similarity": round(bio_sim, 2),
            "username_similarity": round(username_sim, 2),
            "follower_disparity_flag": follower_ratio_flag
        }
    }