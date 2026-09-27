```markdown
# ANUSINT

**A**utomated **N**etwork **U**sername & **S**ocial **I**mpersonation
**N**otification **T**ool

[![Tests](https://github.com/ShivamKumar1107/anusint/actions/workflows/tests.yml/badge.svg)](https://github.com/ShivamKumar1107/anusint/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

A small, dependency-light toolkit for **brand/account owners** to find
and evidence impersonation accounts. It only uses publicly accessible
data — no login, no scraping past auth walls, no bulk harvesting.

```text
you@machine:~/anusint$ anusint compare mybrand mybrand_official

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

Requires Python 3.8+.

```bash
git clone [https://github.com/ShivamKumar1107/anusint.git](https://github.com/ShivamKumar1107/anusint.git)
cd anusint

python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

pip install -e .

```

That's it — this uses the `pyproject.toml` in this repo to install ANUSINT (and its dependencies like `requests`, `click`, `rich`, `Pillow`) into your environment with a global `anusint` console command.

### Verify your install

```bash
python3 -m unittest discover tests

```

This runs an offline test suite (no network calls) covering text similarity, username normalization, caching, and risk scoring. You should see `OK`.

Then confirm the CLI itself works:

```bash
anusint --help

```

---

## 2. What it does

| Command | Purpose |
| --- | --- |
| `anusint snapshot <name>` | Pulls public Instagram profile fields: bio, display name, follower/following counts, verified/private status, and profile picture. Outputs a clean terminal table. |
| `anusint compare <genuine> <candidates...>` | Scores each candidate against your real account — username similarity, name/bio text similarity, profile-picture visual similarity — and produces a weighted 0–100 risk score with a LOW/MEDIUM/HIGH label and specific flags. |

## 3. Usage

```bash
# What does a specific Instagram profile publicly show?
anusint snapshot suspected_fake_account

# Compare your real account against one or more suspects
anusint compare mybrandname mybrandname_official fan.page.mybrandname

# Export a full report to a JSON file in the reports/ directory
anusint compare mybrandname suspected_fake_account --export

```

### Rate limiting, Caching & Retries

* **Smart Caching:** To protect your IP, the tool uses a local SQLite database (`~/.anusint/profile_cache.db`). If you query an account you've already checked in the last 24 hours, it loads from disk instantly instead of hitting Instagram.
* **Resilience:** All HTTP requests go through a shared session (`core/http_client.py`) that automatically retries transient failures (timeouts, HTTP 429) with exponential backoff and randomized jitter.
* **Politeness:** The tool enforces a mandatory 5-12 second randomized delay between live network calls to mimic human browsing and avoid HTTP 401 login-gating.

---

## 4. What it deliberately does NOT do

* **No login, no session tokens, no auth-wall bypass.** Everything uses endpoints reachable while logged out.
* **No bulk/high-frequency scraping.** Built for occasional-to-modest lookups (a handful to a few dozen suspect accounts), not mass harvesting. Hammering these endpoints will get you rate-limited or IP-blocked, and at volume crosses into a Terms of Service violation.
* **No private data extraction.** It does **not** and cannot get anything the owner hasn't chosen to publish: no private email/phone, no IP address, no username-change history, no DMs — none of that is exposed by any public Instagram interface.
* **No automated verdict.** `compare` scores *similarity* and surfaces flags to help you triage. A human still decides whether an account is actually impersonating and what to do about it.

If you need data beyond what's public (e.g. for a serious harassment or fraud case), the legitimate paths are:

1. **Instagram's own impersonation report flow** (Settings → Report a Problem → "Someone is pretending to be me/my business") — it specifically asks for the kind of side-by-side comparison this tool generates as evidence.
2. **Law enforcement report**, for cases involving fraud or harassment — Meta releases subscriber data (email/phone/IP) to law enforcement only via valid legal process.

---

## 5. Project layout

```text
anusint/
├── .github/workflows/tests.yml   # CI: runs test suite on every push/PR
├── core/
│   ├── __init__.py
│   ├── cli.py                    # click CLI entry point & rich UI
│   ├── http_client.py            # shared HTTP session (retry/backoff)
│   ├── cache.py                  # SQLite 24-hour persistent cache
│   ├── scanner.py                # JSON parsing and dataclasses
│   ├── analyzer.py               # similarity scoring + risk report
│   └── exporter.py               # JSON report writers
├── tests/
│   ├── __init__.py
│   ├── test_http.py              # network mocking tests
│   └── test_analyzer.py          # risk scoring tests
├── pyproject.toml                # packaging metadata (pip install -e .)
├── LICENSE                       # MIT
├── CONTRIBUTING.md
├── .gitignore
└── README.md

```

## 6. Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `InstagramRateLimitError (429)` | You're hitting Instagram too fast. Wait a bit before retrying. The local cache will protect you from re-querying the same accounts. |
| `InstagramAuthError (401)` | Instagram has temporarily flagged your IP and placed a login-wall in front of the public endpoint. Change your IP (VPN) or wait 24 hours. |
| `connection_error` / `timeout` on every request | Check your network, or a proxy/firewall may be blocking outbound HTTPS. |
| Command `anusint` not found | You forgot to run `pip install -e .` from the root directory, or you are not in your active virtual environment. |

## 7. Suggested workflow for a real case

1. `snapshot` each suspicious account to capture its current public state — timestamp this by using `--export`, since accounts often get edited or deleted once someone realizes they're being investigated.
2. `compare` each suspect against your genuine account to get a risk-scored report, sorted highest-risk first.
3. Save the JSON output plus screenshots as your evidence package.
4. Report through Instagram's impersonation flow, attaching that evidence. Escalate to legal/law enforcement if it involves fraud, harassment, or extortion.

---

## 8. Contributing

PRs welcome — see [CONTRIBUTING.md](https://www.google.com/search?q=CONTRIBUTING.md&utm_source=gemini) for the dev setup, what's in and out of scope for this project, and what to check before opening a pull request. In short: this stays a public-data-only tool, so anything that adds login-based scraping, rate-limit bypassing, or private-data extraction won't be merged.

## 9. License

[MIT](https://www.google.com/search?q=LICENSE&utm_source=gemini) — use it, fork it, ship it in your own tooling. No warranty; see the license text for the standard disclaimer.

```

```