"""
export.py — shared JSON/CSV writers so every CLI supports --output the
same way, and flattening logic for nested report dicts lives in one place.
"""

import csv
import json


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _flatten(d, parent_key="", sep="."):
    """Flattens nested dicts/lists into dotted keys for CSV rows."""
    items = {}
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
            items.update(_flatten(v, new_key, sep))
    elif isinstance(d, list):
        items[parent_key] = "; ".join(str(x) for x in d) if d else ""
    else:
        items[parent_key] = d
    return items


def write_csv(path, rows):
    """
    rows: list of dicts (possibly nested — will be flattened).
    Writes a CSV with the union of all flattened keys as headers.
    """
    flat_rows = [_flatten(r) for r in rows]
    fieldnames = []
    seen = set()
    for row in flat_rows:
        for k in row:
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in flat_rows:
            writer.writerow(row)


def save_results(path, data, fmt=None):
    """
    Saves `data` (a list of dicts, or a single dict) to `path`.
    Format is inferred from the file extension unless `fmt` is given.
    """
    fmt = fmt or ("csv" if path.lower().endswith(".csv") else "json")
    rows = data if isinstance(data, list) else [data]

    if fmt == "csv":
        write_csv(path, rows)
    else:
        write_json(path, data)
