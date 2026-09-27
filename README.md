# ANUSINT (Advanced Anti-Impersonation OSINT)

A powerful, CLI-driven OSINT tool designed to bypass strict rate limits, securely fetch profile data, and analyze potential Instagram impersonation risks using fuzzy string matching and follower disparity heuristics.

## Features
- **Resilient Network Engine:** Implements exponential backoff, jitter, and dynamic `Retry-After` parsing to navigate strict 429 and 401 blocks.
- **Persistent Local Caching:** SQLite-backed 24-hour cache minimizes API calls and protects your IP reputation.
- **Heuristic Analysis Engine:** Calculates a 0-100 risk score by comparing bio, full name, and username similarities alongside suspicious follower ratios.
- **Modern Terminal UI:** Uses `click` and `rich` to provide color-coded data tables and risk reports natively in the terminal.
- **Evidence Export:** Save snapshot and analysis reports to formatted JSON files for record-keeping.

## Installation

```bash
git clone https://github.com/ShivamKumar1107/anusint.git
cd anusint

# Create and activate a fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the tool globally within this environment using the new pyproject.toml
pip install -e .