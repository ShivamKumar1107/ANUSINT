"""
profile_snapshot.py
--------------------
Fetches PUBLICLY VISIBLE Instagram profile data for a given username,
without logging in. Uses the same endpoint Instagram's own logged-out
web client uses to render a profile page / power link previews.

IMPORTANT LIMITATIONS:
- Instagram rate-limits and blocks unauthenticated/automated traffic.
  This is built for occasional, one-off-to-modest lookups (checking a
  handful of suspect accounts), NOT bulk/high-frequency scraping — doing
  that violates Instagram's Terms of Service and will get your IP
  blocked. Use --delay for batch runs (see below).
- It cannot and does not attempt to retrieve anything the account owner
  hasn't chosen to make public: no private email/phone, no IP address,
  no username-change history, no DMs. The only contact info retrievable
  is a business account's public "Contact" button info (email/phone/
  address), if the owner opted in to show it — same as any visitor
  tapping "Contact" on the profile.
- This isn't an official public API, so the response format can change
  without notice; if that happens you'll get
  `unexpected_response_format_endpoint_may_have_changed` and should check
  the raw JSON and update the field mapping in fetch_public_profile().

Standalone usage:
    python3 profile_snapshot.py somebrand
    python3 profile_snapshot.py somebrand suspect1 suspect2
    python3 profile_snapshot.py --input usernames.txt --output snapshots.csv --delay 3

Or via the main CLI:
    python3 main.py snapshot somebrand
"""

import argparse
import json

import config
from net import safe_get, RateLimiter, green, red, yellow, dim, bold
from export import save_results

HEADERS = {"X-IG-App-ID": config.IG_APP_ID}


def fetch_public_profile(username):
    """
    Fetch public profile info for `username`.
    Returns a dict with normalized fields; sets 'error' to None on success
    or to a short machine-readable reason string on failure.
    """
    url = config.WEB_PROFILE_URL.format(u=username)
    resp, err = safe_get(url, headers=HEADERS)

    if err:
        return {"username": username, "error": err}
    if resp.status_code == 404:
        return {"username": username, "error": "not_found"}
    if resp.status_code == 429:
        return {"username": username, "error": "rate_limited_try_again_later"}
    if resp.status_code != 200:
        return {"username": username, "error": f"http_{resp.status_code}"}

    try:
        data = resp.json()
        user = data["data"]["user"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return {"username": username, "error": "unexpected_response_format_endpoint_may_have_changed"}

    if user is None:
        return {"username": username, "error": "not_found"}

    return {
        "username": username,
        "full_name": user.get("full_name"),
        "biography": user.get("biography"),
        "is_verified": user.get("is_verified"),
        "is_private": user.get("is_private"),
        "follower_count": user.get("edge_followed_by", {}).get("count"),
        "following_count": user.get("edge_follow", {}).get("count"),
        "post_count": user.get("edge_owner_to_timeline_media", {}).get("count"),
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url"),
        "external_url": user.get("external_url"),
        "is_business_account": user.get("is_business_account"),
        "category_name": user.get("category_name"),
        "public_email": user.get("public_email") or None,
        "public_phone_number": user.get("public_phone_number") or None,
        "public_phone_country_code": user.get("public_phone_country_code") or None,
        "business_address": user.get("business_address_json"),
        "error": None,
    }


def fetch_many(usernames, delay=config.DEFAULT_DELAY_BETWEEN_REQUESTS):
    """Sequential batch fetch with a politeness delay between requests."""
    limiter = RateLimiter(delay)
    results = []
    for uname in usernames:
        limiter.wait()
        results.append(fetch_public_profile(uname))
    return results


def print_profile(profile):
    if profile.get("error"):
        print(red(f"\n[!] @{profile['username']}: {profile['error']}"))
        return

    print(f"\n{bold('@' + profile['username'])}")
    print(f"  Name:        {profile.get('full_name')}")
    print(f"  Verified:    {profile.get('is_verified')}")
    print(f"  Private:     {profile.get('is_private')}")
    print(f"  Followers:   {profile.get('follower_count')}")
    print(f"  Following:   {profile.get('following_count')}")
    print(f"  Posts:       {profile.get('post_count')}")
    print(f"  Bio:         {profile.get('biography')}")
    print(f"  Link:        {profile.get('external_url')}")
    print(f"  Business:    {profile.get('is_business_account')} ({profile.get('category_name')})")
    print(f"  Profile pic: {profile.get('profile_pic_url')}")

    contact_bits = []
    if profile.get("public_email"):
        contact_bits.append(f"email={profile['public_email']}")
    if profile.get("public_phone_number"):
        cc = profile.get("public_phone_country_code") or ""
        contact_bits.append(f"phone=+{cc}{profile['public_phone_number']}")
    if profile.get("business_address"):
        contact_bits.append(f"address={profile['business_address']}")
    contact_line = ", ".join(contact_bits) if contact_bits else "none published"
    print(f"  Public contact: {green(contact_line) if contact_bits else dim(contact_line)}")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Fetch public Instagram profile data for one or more usernames."
    )
    parser.add_argument("usernames", nargs="*", help="Usernames to fetch")
    parser.add_argument("--input", help="Text file with one username per line (for batch runs)")
    parser.add_argument("--output", help="Save results to a .json or .csv file")
    parser.add_argument(
        "--delay", type=float, default=config.DEFAULT_DELAY_BETWEEN_REQUESTS,
        help=f"Seconds between requests in batch runs (default: {config.DEFAULT_DELAY_BETWEEN_REQUESTS})"
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    return parser


def load_usernames_from_file(path):
    with open(path) as f:
        return [line.strip().lstrip("@") for line in f if line.strip() and not line.startswith("#")]


def main(argv=None):
    from net import set_color_enabled

    args = build_arg_parser().parse_args(argv)
    if args.no_color:
        set_color_enabled(False)

    usernames = list(args.usernames)
    if args.input:
        usernames += load_usernames_from_file(args.input)

    if not usernames:
        print(yellow("No usernames given. Pass them as arguments or via --input <file>."))
        return

    profiles = fetch_many(usernames, delay=args.delay)
    for p in profiles:
        print_profile(p)

    if args.output:
        save_results(args.output, profiles)
        print(dim(f"\nSaved results to {args.output}"))


if __name__ == "__main__":
    main()
