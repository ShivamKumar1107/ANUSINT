"""
net.py — shared HTTP plumbing used by every module:
  - a requests.Session with automatic retry/backoff on transient errors
    (connection errors, timeouts, 429/500/502/503/504)
  - a tiny rate limiter for batch runs, so we don't hammer any platform
  - color helpers for terminal output (auto-disabled when not a TTY,
    or when NO_COLOR is set, or when --no-color is passed)
"""

import sys
import time
import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config


def build_session(retries=config.DEFAULT_RETRIES, backoff=config.DEFAULT_BACKOFF):
    """A requests.Session that automatically retries transient failures."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": config.USER_AGENT})
    return session


# One shared session per process — reuses connections, applies retry policy
# everywhere without every module re-implementing it.
SESSION = build_session()


class RateLimiter:
    """Simple thread-safe minimum-delay-between-calls limiter."""

    def __init__(self, delay_seconds):
        self.delay = delay_seconds
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self):
        if self.delay <= 0:
            return
        with self._lock:
            elapsed = time.monotonic() - self._last_call
            remaining = self.delay - elapsed
            if remaining > 0:
                time.sleep(remaining)
            self._last_call = time.monotonic()


def safe_get(url, session=None, timeout=config.DEFAULT_TIMEOUT, **kwargs):
    """
    GET a URL, returning (response_or_None, error_message_or_None).
    Never raises — callers get a clean tuple to branch on.
    """
    sess = session or SESSION
    try:
        resp = sess.get(url, timeout=timeout, **kwargs)
        return resp, None
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.ConnectionError as e:
        return None, f"connection_error: {e}"
    except requests.exceptions.RequestException as e:
        return None, f"request_error: {e}"


# ---------------------------------------------------------------------
# Color output — no external dependency, plain ANSI codes.
# ---------------------------------------------------------------------

_COLOR_ENABLED = sys.stdout.isatty()


def set_color_enabled(enabled):
    global _COLOR_ENABLED
    _COLOR_ENABLED = enabled


def _wrap(code, text):
    if not _COLOR_ENABLED:
        return text
    return f"\033[{code}m{text}\033[0m"


def green(text):
    return _wrap("32", text)


def red(text):
    return _wrap("31", text)


def yellow(text):
    return _wrap("33", text)


def cyan(text):
    return _wrap("36", text)


def bold(text):
    return _wrap("1", text)


def dim(text):
    return _wrap("2", text)
