"""
username_checker.py
--------------------
Checks whether a given username exists on several major platforms —
useful for finding out if an impersonator has claimed your handle/brand
name elsewhere. Only checks PUBLIC existence (does the profile URL
resolve, or does the platform show a "not found" page); no login, no
auth-wall bypass, no scraping of anything private.

Standalone usage:
    python3 username_checker.py alice
    python3 username_checker.py alice bob --platforms Instagram,TikTok
    python3 username_checker.py alice --output results.csv

Or via the main CLI:
    python3 main.py check-username alice
"""

import argparse
import concurrent.futures

import config
from net import safe_get, RateLimiter, red, yellow, dim, bold, green
from export import save_results


def check_platform(platform_name, platform_config, username, rate_limiter=None):
    if rate_limiter:
        rate_limiter.wait()

    url = platform_config["url"].format(u=username)
    result = {
        "platform": platform_name,
        "username": username,
        "url": url,
        "status": "unknown",
        "http_code": None,
        "error": None,
    }

    resp, err = safe_get(url, allow_redirects=True)
    if err:
        result["status"] = "error"
        result["error"] = err
        return result

    result["http_code"] = resp.status_code
    if resp.status_code == 404:
        result["status"] = "not_found"
    elif resp.status_code == 200:
        body = resp.text
        markers = platform_config["not_found_markers"]
        if any(marker.lower() in body.lower() for marker in markers):
            result["status"] = "not_found"
        else:
            result["status"] = "exists"
    elif resp.status_code in (301, 302):
        result["status"] = "redirected"
    else:
        result["status"] = f"http_{resp.status_code}"

    return result


def check_username_everywhere(username, platforms=None, max_workers=config.DEFAULT_MAX_WORKERS,
                               rate_limit_delay=0.0):
    """Check one username across all (or selected) platforms concurrently."""
    targets = platforms or config.PLATFORMS
    rate_limiter = RateLimiter(rate_limit_delay) if rate_limit_delay else None
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_platform, name, cfg, username, rate_limiter): name
            for name, cfg in targets.items()
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    order = {name: i for i, name in enumerate(targets)}
    results.sort(key=lambda r: order.get(r["platform"], 999))
    return results


def print_report(username, results):
    print(f"\n{bold('Username lookup: ' + username)}")
    found_count = sum(1 for r in results if r["status"] == "exists")

    for r in results:
        if r["status"] == "exists":
            symbol, colorer = "FOUND", red
        elif r["status"] == "not_found":
            symbol, colorer = " -- ", dim
        elif r["status"] == "error":
            symbol, colorer = "ERR ", yellow
        else:
            symbol, colorer = " ?? ", yellow

        line = f"  [{symbol}] {r['platform']:12} {r['url']}"
        if r["status"] == "error":
            line += f"  ({r['error']})"
        print(colorer(line))

    summary = f"  -> found on {found_count}/{len(results)} platforms checked"
    print(green(summary) if found_count else dim(summary))


def resolve_platforms(names_csv):
    """Turn a comma-separated --platforms arg into a filtered PLATFORMS dict."""
    if not names_csv:
        return config.PLATFORMS
    requested = {n.strip().lower() for n in names_csv.split(",")}
    matched = {name: cfg for name, cfg in config.PLATFORMS.items() if name.lower() in requested}
    unknown = requested - {name.lower() for name in matched}
    if unknown:
        print(yellow(f"Warning: unknown platform(s) ignored: {', '.join(sorted(unknown))}"))
        print(dim(f"Available platforms: {', '.join(config.PLATFORMS)}"))
    return matched or config.PLATFORMS


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Check whether usernames exist across major platforms."
    )
    parser.add_argument("usernames", nargs="+", help="One or more usernames to check")
    parser.add_argument(
        "--platforms", help=f"Comma-separated list to check (default: all). "
                             f"Options: {', '.join(config.PLATFORMS)}"
    )
    parser.add_argument("--output", help="Save results to a .json or .csv file")
    parser.add_argument(
        "--delay", type=float, default=0.0,
        help="Seconds to wait between requests to the same platform (politeness delay)"
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    return parser


def main(argv=None):
    from net import set_color_enabled

    args = build_arg_parser().parse_args(argv)
    if args.no_color:
        set_color_enabled(False)

    platforms = resolve_platforms(args.platforms)
    all_results = {}

    for uname in args.usernames:
        results = check_username_everywhere(uname, platforms=platforms, rate_limit_delay=args.delay)
        print_report(uname, results)
        all_results[uname] = results

    if args.output:
        flat = [r for results in all_results.values() for r in results]
        save_results(args.output, flat)
        print(dim(f"\nSaved results to {args.output}"))


if __name__ == "__main__":
    main()
