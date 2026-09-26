"""
config.py — all the tunable constants live here, so nothing else in the
codebase has magic numbers scattered through it.
"""

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 10          # seconds, per request
DEFAULT_RETRIES = 3           # retry attempts on transient failures
DEFAULT_BACKOFF = 0.75        # seconds, exponential backoff base
DEFAULT_DELAY_BETWEEN_REQUESTS = 1.0  # seconds, politeness delay for batch runs
DEFAULT_MAX_WORKERS = 8       # concurrency for the multi-platform username check

# Instagram's public web app-id constant (not a secret — embedded in
# Instagram's own public JS bundle, used for logged-out profile lookups).
IG_APP_ID = "936619743392459"

WEB_PROFILE_URL = "https://i.instagram.com/api/v1/users/web_profile_info/?username={u}"

# Platforms checked by username_checker.py.
# not_found_markers = strings that appear in a platform's "soft 404" page
# body even though it returns HTTP 200.
PLATFORMS = {
    "Instagram": {
        "url": "https://www.instagram.com/{u}/",
        "not_found_markers": ["Sorry, this page"],
    },
    "Twitter/X": {
        "url": "https://x.com/{u}",
        "not_found_markers": ["This account doesn\u2019t exist", "page doesn\u2019t exist"],
    },
    "TikTok": {
        "url": "https://www.tiktok.com/@{u}",
        "not_found_markers": ["Couldn't find this account"],
    },
    "YouTube": {
        "url": "https://www.youtube.com/@{u}",
        "not_found_markers": ["This page isn't available"],
    },
    "Facebook": {
        "url": "https://www.facebook.com/{u}",
        "not_found_markers": ["This content isn't available", "isn't available right now"],
    },
    "Threads": {
        "url": "https://www.threads.net/@{u}",
        "not_found_markers": ["Sorry, this page"],
    },
    "GitHub": {
        "url": "https://github.com/{u}",
        "not_found_markers": ["Not Found"],
    },
    "Reddit": {
        "url": "https://www.reddit.com/user/{u}/",
        "not_found_markers": ["Sorry, nobody on Reddit goes by that name"],
    },
    "Pinterest": {
        "url": "https://www.pinterest.com/{u}/",
        "not_found_markers": ["Page not found"],
    },
    "Telegram": {
        "url": "https://t.me/{u}",
        "not_found_markers": ["If you have Telegram"],
    },
}

# Words that commonly show up in impersonating/parody/fan usernames.
IMPERSONATION_PATTERN_WORDS = [
    "official", "real", "backup", "support", "help", "fan", "page",
    "team", "recovery", "verify", "verified", "admin", "staff", "hq",
]

# Thresholds used to turn raw similarity percentages into flags/risk score.
THRESHOLDS = {
    "username_core_similarity_high": 60,
    "display_name_similarity_high": 80,
    "bio_similarity_high": 70,
    "profile_pic_similarity_high": 90,
    "follower_ratio_suspicious": 0.05,  # candidate < 5% of genuine's followers
}

# Weights used to combine individual similarity scores into one overall
# risk score (0-100). Purely a prioritization aid, not a verdict.
RISK_WEIGHTS = {
    "username_core_similarity": 0.30,
    "display_name_similarity": 0.20,
    "bio_similarity": 0.15,
    "profile_pic_similarity": 0.35,
}

RISK_LEVELS = [
    (75, "HIGH"),
    (45, "MEDIUM"),
    (0, "LOW"),
]


def risk_level_for_score(score):
    for threshold, label in RISK_LEVELS:
        if score >= threshold:
            return label
    return "LOW"
