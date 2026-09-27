# Contributing to ANUSINT

Thanks for considering a contribution. A few ground rules keep this
project useful and out of trouble:

## Scope this project stays inside

ANUSINT only ever touches **publicly accessible data**, without
logging in or bypassing any platform's auth wall or rate limiting. PRs
that add any of the following will be closed, regardless of the
justification given:

- Login/session-token/cookie-based scraping of any platform
- Bypassing rate limits, CAPTCHAs, or anti-bot protections
- Extraction of private data (DMs, private email/phone not opted into
  public display, IP addresses, location history, follower/following
  graphs beyond public counts)
- Anything whose primary use case is tracking or profiling a specific
  private individual rather than verifying/comparing named accounts

If you're unsure whether a change fits, open an issue describing the
use case before writing code.

## Setting up a dev environment

```bash
git clone https://github.com/ShivamKumar1107/anusint.git
cd anusint
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 tests.py   # should print "All tests passed."
```

## Before opening a PR

1. Run `python3 tests.py` — all tests must pass.
2. If you touched a public endpoint's response parsing (e.g.
   `profile_snapshot.fetch_public_profile`), note in your PR description
   that you tested it against a real, live account, since CI can't do
   this (see below).
3. Add tests to `tests.py` for any new pure-logic function (text
   similarity, scoring, parsing) — these run offline in CI.
4. Keep new platform integrations in `config.PLATFORMS` /
   `config.PLATFORM_*` rather than hardcoding URLs inside functions.

## Why CI can't test live network calls

GitHub Actions runs `tests.py`, which is deliberately offline-only (no
requests to Instagram or any other platform) — a shared CI runner
hammering live endpoints on every push would (a) be exactly the kind of
bulk/automated traffic this project's own rules say not to do, and
(b) get flagged/blocked, breaking CI for everyone. So: pure-logic
changes are covered automatically; anything that talks to a live
endpoint needs manual verification by the PR author.

## Reporting a bug

Open an issue with:
- The command you ran (redact usernames if you'd rather not share them)
- The full error output
- Whether it reproduces consistently or intermittently (intermittent
  often just means you got rate-limited — try `--delay` first)
