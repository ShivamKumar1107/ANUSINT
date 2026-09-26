# ANUSINT

**A**utomated **N**etwork **U**sername **S**poofing **I**nvestigation &
**N**otification **T**ool

[![Tests](https://github.com/YOUR-USERNAME/anusint/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR-USERNAME/anusint/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

A small, dependency-light toolkit for **brand/account owners** to find
and evidence impersonation accounts. It only uses publicly accessible
data — no login, no scraping past auth walls, no bulk harvesting.

> Replace `YOUR-USERNAME` above and in `pyproject.toml` with your actual
> GitHub username/org once you've created the repo.

```
you@machine:~/anusint$ python3 main.py compare mybrand mybrand_official

@mybrand (genuine) vs @mybrand_official (candidate)
  Risk score: 82.4/100  (HIGH)
  Username similarity (raw / core): 70.0% / 63.6%
  Display name similarity: 91.0%
  Bio similarity:          88.0%
  Profile pic similarity:  97.0%
  Flags:
    - username contains impersonation-pattern word(s): ['official']
    - display name almost identical to genuine account
    - bio text closely matches genuine account
    - profile picture appears visually identical or near-identical
```

---

## 1. Setup

Requires Python 3.9+.

```bash
git clone https://github.com/YOUR-USERNAME/anusint.git
cd anusint

python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

pip install -r requirements.txt
```

That's it — two dependencies (`requests`, `Pillow`), no compiled
image-hashing library required (the perceptual hash is implemented from
scratch in `impersonation_check.py`).

### Alternative: install as a command

```bash
pip install .
anusint --help              # now available as a plain command, anywhere
```

This uses the `pyproject.toml` in this repo to install ANUSINT (and its
two dependencies) into your environment with an `anusint` console
command, instead of running `python3 main.py` from inside the folder.

### Verify your install

```bash
python3 tests.py
```

This runs an offline test suite (no network calls) covering text
similarity, username normalization, the dHash image-hashing algorithm,
and risk scoring. You should see `All tests passed.`

Then confirm the CLI itself works:

```bash
python3 main.py --help
```

---

## 2. What it does

| Command | Purpose |
|---|---|
| `check-username <name>` | Checks whether a username exists across Instagram, X/Twitter, TikTok, YouTube, Facebook, Threads, GitHub, Reddit, Pinterest, Telegram |
| `snapshot <name>` | Pulls public Instagram profile fields: bio, display name, follower/following/post counts, verified/private status, profile picture, external link, and public business contact info (email/phone/address) if the account owner opted in to show a "Contact" button |
| `compare <genuine> <candidates...>` | Scores each candidate against your real account — username similarity, name/bio text similarity, profile-picture visual similarity — and produces a weighted 0–100 risk score with a LOW/MEDIUM/HIGH label and specific flags |

## 3. Usage

```bash
# Has your handle been squatted on other platforms?
python3 main.py check-username mybrandname

# Restrict to specific platforms, save results
python3 main.py check-username mybrandname --platforms Instagram,TikTok --output results.csv

# What does a specific Instagram profile publicly show?
python3 main.py snapshot suspected_fake_account

# Batch snapshot from a file (one username per line, '#' comments allowed, '@' prefix optional)
python3 main.py snapshot --input suspects.txt --output snapshots.csv --delay 2

# Compare your real account against one or more suspects
python3 main.py compare mybrandname mybrandname_official fan.page.mybrandname

# Same, but read candidates from a file and export a full report
python3 main.py compare mybrandname --input suspects.txt --output impersonation_report.csv
```

Every subcommand also runs standalone (useful for scripting or importing
as a library):

```bash
python3 username_checker.py mybrandname
python3 profile_snapshot.py mybrandname --output snapshot.json
python3 impersonation_check.py mybrandname suspect1 suspect2
```

Run `python3 main.py <command> --help` for the full flag list of any
subcommand (`--output`, `--input`, `--delay`, `--platforms`, `--no-color`).

### Output formats

`--output` accepts either a `.json` or `.csv` path — format is inferred
from the extension. CSV output flattens nested fields (e.g.
`username_similarity.core_similarity`) into columns, so you can open a
comparison report directly in a spreadsheet.

### Rate limiting & retries

- All HTTP requests go through a shared session (`net.py`) that
  automatically retries transient failures (timeouts, connection
  errors, HTTP 429/500/502/503/504) with exponential backoff — a flaky
  network won't silently produce a false "not found."
- `--delay` adds a politeness pause between requests in batch runs
  (`snapshot` and `compare` default to 1 second; `check-username`
  defaults to 0 since it fans out across *different* platforms
  concurrently, not repeated hits to one). Turn `--delay` up if you're
  checking many accounts back-to-back — Instagram in particular will
  return `rate_limited_try_again_later` if you go too fast.

---

## 4. What it deliberately does NOT do

- **No login, no session tokens, no auth-wall bypass.** Everything uses
  endpoints reachable while logged out.
- **No bulk/high-frequency scraping.** Built for occasional-to-modest
  lookups (a handful to a few dozen suspect accounts), not mass
  harvesting. Hammering these endpoints will get you rate-limited or
  IP-blocked, and at volume crosses into a Terms of Service violation.
- **No private data extraction.** This tool *does* surface public
  business-contact info when an account owner has opted in to show a
  "Contact" button (business email/phone/address — the same thing any
  visitor sees by tapping "Contact" on the profile). It does **not**
  and cannot get anything the owner hasn't chosen to publish: no
  private email/phone, no IP address, no username-change history, no
  DMs — none of that is exposed by any public Instagram interface.
- **No automated verdict.** `compare` scores *similarity* and surfaces
  flags to help you triage. A human still decides whether an account
  is actually impersonating and what to do about it.

If you need data beyond what's public (e.g. for a serious harassment or
fraud case), the legitimate paths are:
1. **Instagram's own impersonation report flow** (Settings → Report a
   Problem → "Someone is pretending to be me/my business") — it
   specifically asks for the kind of side-by-side comparison this tool
   generates as evidence.
2. **Law enforcement report**, for cases involving fraud or harassment —
   Meta releases subscriber data (email/phone/IP) to law enforcement
   only via valid legal process.

---

## 5. Project layout

```
anusint/
├── .github/workflows/tests.yml   # CI: runs tests.py + CLI smoke tests on every push/PR
├── main.py                       # unified CLI entry point
├── config.py                     # platforms, thresholds, weights, tunables
├── net.py                        # shared HTTP session (retry/backoff), rate limiter, color output
├── export.py                     # JSON/CSV writers
├── username_checker.py           # cross-platform username existence check
├── profile_snapshot.py           # public Instagram profile fetcher
├── impersonation_check.py        # similarity scoring + risk report
├── tests.py                      # offline test suite (no network required)
├── requirements.txt
├── pyproject.toml                # packaging metadata (pip install .)
├── LICENSE                       # MIT
├── CONTRIBUTING.md
├── .gitignore
└── README.md
```

## 6. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `rate_limited_try_again_later` | You're hitting Instagram too fast — raise `--delay`, or wait a bit before retrying. |
| `unexpected_response_format_endpoint_may_have_changed` | Instagram changed their internal response format (this isn't an official public API). Run the URL in `config.WEB_PROFILE_URL` manually and update the field mapping in `profile_snapshot.fetch_public_profile()`. |
| `connection_error` / `timeout` on every request | Check your network, or a proxy/firewall may be blocking outbound HTTPS. |
| Colors look like garbled `\033[...]` text | Your terminal doesn't support ANSI color, or output is being piped/redirected — add `--no-color`. |
| `ModuleNotFoundError` | You forgot to `pip install -r requirements.txt`, or you're not in the venv you installed it in. |

## 7. Suggested workflow for a real case

1. `check-username` your brand/handle across platforms to see where
   else it's been squatted.
2. `snapshot` (or batch-`snapshot --input`) each suspicious account to
   capture its current public state — timestamp this, since accounts
   often get edited or deleted once someone realizes they're being
   investigated.
3. `compare` each suspect against your genuine account to get a
   risk-scored report, sorted highest-risk first.
4. Save the JSON/CSV output plus screenshots as your evidence package.
5. Report through Instagram's impersonation flow, attaching that
   evidence. Escalate to legal/law enforcement if it involves fraud,
   harassment, or extortion.

---

## 8. Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup,
what's in and out of scope for this project, and what to check before
opening a pull request. In short: this stays a public-data-only tool,
so anything that adds login-based scraping, rate-limit bypassing, or
private-data extraction won't be merged.

## 9. License

[MIT](LICENSE) — use it, fork it, ship it in your own tooling. No
warranty; see the license text for the standard disclaimer.
