"""
tests.py — offline sanity checks for the pieces of ANUSINT that don't
need network access: text/username similarity, risk scoring, and the
dHash perceptual-hash implementation. Run after any change to make sure
nothing's broken:

    python3 tests.py
"""

import io
import sys

from PIL import Image, ImageDraw

from impersonation_check import (
    compute_dhash, hamming_distance, text_similarity,
    normalize_username, username_similarity, compute_risk_score,
)
import config

failures = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        failures.append(label)


def to_png_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_structured_image(jitter=0):
    img = Image.new("RGB", (200, 200), (240, 220, 200))
    d = ImageDraw.Draw(img)
    d.ellipse([40 + jitter, 40, 160 + jitter, 160], fill=(200, 150, 120))
    d.ellipse([70 + jitter, 70, 90 + jitter, 90], fill=(20, 20, 20))
    d.ellipse([110 + jitter, 70, 130 + jitter, 90], fill=(20, 20, 20))
    d.rectangle([80 + jitter, 120, 120 + jitter, 135], fill=(150, 50, 50))
    return img


def make_noise_image():
    import random
    random.seed(42)
    img = Image.new("RGB", (200, 200))
    for x in range(200):
        for y in range(200):
            img.putpixel((x, y), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    return img


print("\n== Text similarity ==")
check("identical strings score 100", text_similarity("hello", "hello") == 100.0)
check("completely different strings score low", text_similarity("abcdef", "zzzzzz") < 20)
check("empty string scores 0", text_similarity("", "something") == 0.0)

print("\n== Username normalization ==")
check("strips dots/underscores/digits", normalize_username("john._.doe123") == "johndoe")
check("lowercases", normalize_username("JohnDoe") == "johndoe")

print("\n== Username similarity ==")
sim = username_similarity("mybrand", "mybrand_official")
sim2 = username_similarity("mybrand", "totallyunrelatedname")
check("detects 'official' as suspicious pattern word", "official" in sim["suspicious_pattern_words"])
check(
    f"near-variant username scores well above an unrelated one "
    f"(got {sim['core_similarity']}% vs {sim2['core_similarity']}%)",
    sim["core_similarity"] > sim2["core_similarity"] + 20,
)
check("unrelated usernames score low core similarity", sim2["core_similarity"] < 40)

print("\n== dHash perceptual hashing ==")
h_original = compute_dhash(to_png_bytes(make_structured_image(jitter=0)))
h_near_dup = compute_dhash(to_png_bytes(make_structured_image(jitter=2)))
h_noise = compute_dhash(to_png_bytes(make_noise_image()))

dist_near = hamming_distance(h_original, h_near_dup)
dist_noise = hamming_distance(h_original, h_noise)

check(f"near-duplicate image has low hamming distance (got {dist_near}/64)", dist_near <= 10)
check(f"unrelated/noise image has much higher distance (got {dist_noise}/64)", dist_noise > dist_near)
check("hash length is 64 bits for hash_size=8", len(h_original) == 64)

print("\n== Risk scoring ==")
high = compute_risk_score(
    {"core_similarity": 95, "suspicious_pattern_words": ["official"]},
    name_sim=95, bio_sim=90, pic_sim=98,
)
low = compute_risk_score(
    {"core_similarity": 5, "suspicious_pattern_words": []},
    name_sim=5, bio_sim=0, pic_sim=3,
)
check(f"near-identical profile scores HIGH risk (got {high})", config.risk_level_for_score(high) == "HIGH")
check(f"dissimilar profile scores LOW risk (got {low})", config.risk_level_for_score(low) == "LOW")

missing_pic = compute_risk_score(
    {"core_similarity": 95, "suspicious_pattern_words": ["official"]},
    name_sim=95, bio_sim=90, pic_sim=None,
)
check("risk score still computes when profile pic fetch failed (renormalizes weights)",
      missing_pic is not None and missing_pic > 0)

print()
if failures:
    print(f"{len(failures)} test(s) FAILED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All tests passed.")
