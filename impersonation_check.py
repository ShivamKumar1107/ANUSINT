"""
impersonation_check.py
-----------------------
Compares a known/genuine profile against one or more suspected
impersonator profiles and produces:
  - individual similarity scores (username, display name, bio, profile
    picture)
  - a weighted 0-100 overall risk score + LOW/MEDIUM/HIGH label
  - specific human-readable flags explaining what drove the score

This is a PRIORITIZATION AID for a human reviewer, not an automated
verdict. Always eyeball flagged accounts yourself before reporting them.

Profile picture similarity uses a difference-hash (dHash) implemented
from scratch (no external image-hashing library needed) — robust to
recompression/resizing, not to heavy edits or a completely different photo.

Standalone usage:
    python3 impersonation_check.py mybrand suspect1 suspect2
    python3 impersonation_check.py mybrand --input suspects.txt --output report.csv

Or via the main CLI:
    python3 main.py compare mybrand suspect1 suspect2
"""

import argparse
import difflib
import io
import re

from PIL import Image

import config
from net import safe_get, RateLimiter, red, yellow, green, dim, bold
from export import save_results
from profile_snapshot import fetch_public_profile


# ---------- Perceptual hash (dHash) ----------

def compute_dhash(image_bytes, hash_size=8):
    """
    Difference hash: resize to (hash_size+1) x hash_size grayscale,
    compare adjacent pixels left->right, build a bit string. Robust to
    resizing/recompression, not to heavy edits or unrelated images.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = img.resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels = list(img.getdata())

    bits = []
    for row in range(hash_size):
        row_pixels = pixels[row * (hash_size + 1):(row + 1) * (hash_size + 1)]
        for col in range(hash_size):
            bits.append(1 if row_pixels[col] > row_pixels[col + 1] else 0)
    return bits


def hamming_distance(bits_a, bits_b):
    return sum(a != b for a, b in zip(bits_a, bits_b))


def image_similarity(url_a, url_b):
    """Returns a 0-100 similarity score (100 = identical), or None on failure."""
    resp_a, err_a = safe_get(url_a)
    if err_a or resp_a.status_code != 200:
        return None
    resp_b, err_b = safe_get(url_b)
    if err_b or resp_b.status_code != 200:
        return None

    try:
        hash_a = compute_dhash(resp_a.content)
        hash_b = compute_dhash(resp_b.content)
    except Exception:
        return None

    dist = hamming_distance(hash_a, hash_b)
    return round((1 - dist / len(hash_a)) * 100, 1)


# ---------- Text / username similarity ----------

def normalize_username(u):
    return re.sub(r"[._\d]", "", u.lower())


def text_similarity(a, b):
    if not a or not b:
        return 0.0
    return round(difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100, 1)


def username_similarity(genuine_username, candidate_username):
    core_similarity = text_similarity(
        normalize_username(genuine_username), normalize_username(candidate_username)
    )
    raw_similarity = text_similarity(genuine_username, candidate_username)
    suspicious_words = [
        w for w in config.IMPERSONATION_PATTERN_WORDS
        if w in candidate_username.lower() and w not in genuine_username.lower()
    ]
    return {
        "raw_similarity": raw_similarity,
        "core_similarity": core_similarity,
        "suspicious_pattern_words": suspicious_words,
    }


# ---------- Risk scoring ----------

def compute_risk_score(uname_sim, name_sim, bio_sim, pic_sim):
    """Weighted combination of available similarity scores, renormalized
    over whichever components we actually have data for (e.g. pic_sim
    may be None if a fetch failed)."""
    components = {
        "username_core_similarity": uname_sim["core_similarity"],
        "display_name_similarity": name_sim,
        "bio_similarity": bio_sim,
        "profile_pic_similarity": pic_sim,
    }
    available = {k: v for k, v in components.items() if v is not None}
    if not available:
        return 0.0

    total_weight = sum(config.RISK_WEIGHTS[k] for k in available)
    score = sum(config.RISK_WEIGHTS[k] * v for k, v in available.items()) / total_weight
    return round(score, 1)


def build_flags(genuine, candidate, uname_sim, name_sim, bio_sim, pic_sim):
    t = config.THRESHOLDS
    flags = []
    if uname_sim["core_similarity"] > t["username_core_similarity_high"]:
        flags.append("username is a close variant of the genuine account (ignoring dots/underscores/digits)")
    if uname_sim["suspicious_pattern_words"]:
        flags.append(f"username contains impersonation-pattern word(s): {uname_sim['suspicious_pattern_words']}")
    if name_sim > t["display_name_similarity_high"]:
        flags.append("display name almost identical to genuine account")
    if bio_sim > t["bio_similarity_high"]:
        flags.append("bio text closely matches genuine account")
    if pic_sim is not None and pic_sim > t["profile_pic_similarity_high"]:
        flags.append("profile picture appears visually identical or near-identical")
    if candidate.get("is_verified"):
        flags.append("NOTE: candidate account IS verified -- unlikely to be an impersonator")
    gf, cf = genuine.get("follower_count"), candidate.get("follower_count")
    if gf is not None and cf is not None and gf > 0 and cf < gf * t["follower_ratio_suspicious"]:
        flags.append("candidate has dramatically fewer followers than the genuine account (common in fakes)")
    return flags


def compare_profiles(genuine_username, candidate_username, genuine_cache=None):
    """
    genuine_cache: optional pre-fetched profile dict for the genuine
    account, so a batch run doesn't refetch it for every candidate.
    """
    genuine = genuine_cache or fetch_public_profile(genuine_username)
    candidate = fetch_public_profile(candidate_username)

    report = {
        "genuine_username": genuine_username,
        "candidate_username": candidate_username,
        "genuine_fetch_error": genuine.get("error"),
        "candidate_fetch_error": candidate.get("error"),
    }

    if genuine.get("error") or candidate.get("error"):
        report["risk_score"] = None
        report["risk_level"] = "UNKNOWN"
        report["flags"] = ["could not fully compare -- see fetch errors above"]
        return report

    uname_sim = username_similarity(genuine_username, candidate_username)
    name_sim = text_similarity(genuine.get("full_name"), candidate.get("full_name"))
    bio_sim = text_similarity(genuine.get("biography"), candidate.get("biography"))

    pic_sim = None
    if genuine.get("profile_pic_url") and candidate.get("profile_pic_url"):
        pic_sim = image_similarity(genuine["profile_pic_url"], candidate["profile_pic_url"])

    risk_score = compute_risk_score(uname_sim, name_sim, bio_sim, pic_sim)
    flags = build_flags(genuine, candidate, uname_sim, name_sim, bio_sim, pic_sim)

    report.update({
        "username_similarity": uname_sim,
        "display_name_similarity_pct": name_sim,
        "bio_similarity_pct": bio_sim,
        "profile_pic_similarity_pct": pic_sim,
        "risk_score": risk_score,
        "risk_level": config.risk_level_for_score(risk_score),
        "flags": flags,
        "genuine_snapshot": genuine,
        "candidate_snapshot": candidate,
    })
    return report


def compare_many(genuine_username, candidate_usernames, delay=config.DEFAULT_DELAY_BETWEEN_REQUESTS):
    """Fetches the genuine profile once, then compares it against each
    candidate with a politeness delay between requests."""
    genuine_profile = fetch_public_profile(genuine_username)
    limiter = RateLimiter(delay)
    reports = []
    for cand in candidate_usernames:
        limiter.wait()
        reports.append(compare_profiles(genuine_username, cand, genuine_cache=genuine_profile))
    return reports


def print_report(report):
    header = f"@{report['genuine_username']} (genuine) vs @{report['candidate_username']} (candidate)"
    print(f"\n{bold(header)}")

    if report["risk_level"] == "UNKNOWN":
        print(red(f"  Genuine fetch error:   {report['genuine_fetch_error']}"))
        print(red(f"  Candidate fetch error: {report['candidate_fetch_error']}"))
        return

    level_colorer = {"HIGH": red, "MEDIUM": yellow, "LOW": green}[report["risk_level"]]
    print(f"  Risk score: {bold(str(report['risk_score']))}/100  "
          f"({level_colorer(report['risk_level'])})")
    print(f"  Username similarity (raw / core): "
          f"{report['username_similarity']['raw_similarity']}% / "
          f"{report['username_similarity']['core_similarity']}%")
    print(f"  Display name similarity: {report['display_name_similarity_pct']}%")
    print(f"  Bio similarity:          {report['bio_similarity_pct']}%")
    pic = report["profile_pic_similarity_pct"]
    print(f"  Profile pic similarity:  {pic if pic is not None else 'N/A (fetch failed)'}%")

    print("  Flags:")
    if report["flags"]:
        for f in report["flags"]:
            print(f"    - {f}")
    else:
        print(dim("    (none -- low similarity across the board)"))


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Compare a genuine account against suspected impersonators."
    )
    parser.add_argument("genuine_username", help="Your real/verified account's username")
    parser.add_argument("candidates", nargs="*", help="Suspected impersonator username(s)")
    parser.add_argument("--input", help="Text file with one candidate username per line")
    parser.add_argument("--output", help="Save results to a .json or .csv file")
    parser.add_argument(
        "--delay", type=float, default=config.DEFAULT_DELAY_BETWEEN_REQUESTS,
        help=f"Seconds between requests (default: {config.DEFAULT_DELAY_BETWEEN_REQUESTS})"
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    return parser


def main(argv=None):
    from net import set_color_enabled
    from profile_snapshot import load_usernames_from_file

    args = build_arg_parser().parse_args(argv)
    if args.no_color:
        set_color_enabled(False)

    candidates = list(args.candidates)
    if args.input:
        candidates += load_usernames_from_file(args.input)

    if not candidates:
        print(yellow("No candidate usernames given. Pass them as arguments or via --input <file>."))
        return

    reports = compare_many(args.genuine_username, candidates, delay=args.delay)
    # Show highest-risk first so the worst offenders are easy to spot.
    reports.sort(key=lambda r: (r["risk_score"] is None, -(r["risk_score"] or 0)))
    for r in reports:
        print_report(r)

    if args.output:
        save_results(args.output, reports)
        print(dim(f"\nSaved results to {args.output}"))


if __name__ == "__main__":
    main()
