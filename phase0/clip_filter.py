import os
import sys
import subprocess
import json
import shutil
import numpy as np
from pathlib import Path
from PIL import Image

import open_clip
import torch

VIDEO_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Downloads/Santol Fruit Pickle Welithalapa Egg Hoppers and Fiery Sauce from My Sri Lankan Village Kitchen.mp4"
)
FRAME_INTERVAL = 3
BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "clip-raw-frames"
OUT_DIR = BASE_DIR / "clip-high-signal"
RAW_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)
for f in OUT_DIR.glob("*.jpg"):
    f.unlink()

# ─── GEO-RELEVANT CATEGORIES ───
# High signal = frames worth sending to a vision LLM for geolocation
# Low signal = frames to skip (no geo info)

HIGH_SIGNAL = [
    "an aerial drone shot looking down at landscape from above",
    "a panoramic landscape with mountains, hills, or valleys",
    "a road, highway, or path with visible markings or signs",
    "a building, temple, church, mosque, or distinctive architecture",
    "text, signage, or writing visible in the scene",
    "a coastline, beach, river, lake, or waterfall",
    "a village, town, or city street view",
    "a railway, bridge, or infrastructure",
]

LOW_SIGNAL = [
    "a close-up of food, fruits, or a meal on a plate",
    "hands cooking, cutting, or preparing food",
    "a person talking to camera, a face portrait",
    "an indoor kitchen scene with pots and utensils",
    "a dark or blurry frame with no clear content",
    "a close-up of a single plant, flower, or fruit on a tree",
]

ALL_CATEGORIES = HIGH_SIGNAL + LOW_SIGNAL


def get_duration(video_path):
    result = subprocess.run(["ffmpeg", "-i", video_path], capture_output=True, text=True)
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0


def extract_frame(video_path, timestamp, output_path):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
         "-frames:v", "1", "-q:v", "2", output_path],
        capture_output=True
    )


def dhash(img_pil, hash_size=16):
    gray = img_pil.convert("L").resize((hash_size + 1, hash_size))
    pixels = list(gray.getdata())
    w = hash_size + 1
    diff = [pixels[r * w + c] > pixels[r * w + c + 1]
            for r in range(hash_size) for c in range(hash_size)]
    return sum(2 ** i for i, v in enumerate(diff) if v)


def hamming(h1, h2):
    return bin(h1 ^ h2).count("1")


# ─── LOAD CLIP ───

print("Loading CLIP model (ViT-B/32)...")
model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
tokenizer = open_clip.get_tokenizer("ViT-B-32")
model.eval()
print("CLIP loaded.\n")

text_tokens = tokenizer(ALL_CATEGORIES)
with torch.no_grad():
    text_features = model.encode_text(text_tokens)
    text_features /= text_features.norm(dim=-1, keepdim=True)


def classify_frame(img_path):
    img = Image.open(img_path).convert("RGB")
    img_tensor = preprocess(img).unsqueeze(0)

    with torch.no_grad():
        img_features = model.encode_image(img_tensor)
        img_features /= img_features.norm(dim=-1, keepdim=True)
        similarities = (img_features @ text_features.T).squeeze(0).numpy()

    results = {}
    for cat, sim in zip(ALL_CATEGORIES, similarities):
        results[cat] = round(float(sim), 4)

    high_scores = {c: results[c] for c in HIGH_SIGNAL}
    low_scores = {c: results[c] for c in LOW_SIGNAL}

    best_high = max(high_scores, key=high_scores.get)
    best_high_score = high_scores[best_high]
    best_low = max(low_scores, key=low_scores.get)
    best_low_score = low_scores[best_low]

    best_overall = max(results, key=results.get)
    is_high_signal = best_overall in HIGH_SIGNAL or best_high_score > best_low_score + 0.02

    geo_score = best_high_score - best_low_score

    return {
        "all_scores": results,
        "best_high": best_high,
        "best_high_score": best_high_score,
        "best_low": best_low,
        "best_low_score": best_low_score,
        "best_overall": best_overall,
        "is_high_signal": is_high_signal,
        "geo_score": round(geo_score, 4),
    }


# ─── MAIN ───

print(f"Video: {os.path.basename(VIDEO_PATH)}")
duration = get_duration(VIDEO_PATH)
total_frames = int(duration / FRAME_INTERVAL)
print(f"Duration: {duration:.0f}s ({duration / 60:.1f} min)")
print(f"Frames to scan: {total_frames} (every {FRAME_INTERVAL}s)")
print("=" * 100)

results = []
hashes = {}
dup_count = 0

for i in range(total_frames):
    ts = i * FRAME_INTERVAL
    mins, secs = divmod(ts, 60)
    time_str = f"{int(mins):02d}:{int(secs):02d}"
    frame_path = str(RAW_DIR / f"frame_{ts:04d}.jpg")

    extract_frame(VIDEO_PATH, ts, frame_path)
    if not os.path.exists(frame_path):
        continue

    img = Image.open(frame_path)
    h = dhash(img)
    is_dup = any(hamming(h, ph) < 18 for ph in hashes.values())
    if is_dup:
        dup_count += 1
        continue
    hashes[ts] = h

    clip_result = classify_frame(frame_path)

    entry = {
        "timestamp": ts,
        "time": time_str,
        "frame_path": frame_path,
        **clip_result,
    }
    results.append(entry)

    if clip_result["is_high_signal"]:
        short_cat = clip_result["best_high"].split(",")[0].replace("an ", "").replace("a ", "")[:35]
        geo = clip_result["geo_score"]
        print(f"  ★ [{time_str}] geo={geo:+.3f}  → {short_cat} ({clip_result['best_high_score']:.3f})")
    else:
        sys.stdout.write(f"\r    [{time_str}] scanning...")
        sys.stdout.flush()

print("\r" + " " * 80)

# ─── RESULTS ───

results.sort(key=lambda x: x["geo_score"], reverse=True)
high = [r for r in results if r["is_high_signal"]]

print(f"\n{'=' * 100}")
print("  RESULTS")
print(f"{'=' * 100}")
print(f"  Total frames:         {total_frames}")
print(f"  Duplicates skipped:   {dup_count}")
print(f"  Unique analyzed:      {len(results)}")
print(f"  High-signal:          {len(high)}")
print(f"  Filtered out:         {len(results) - len(high)}")
print(f"  Keep ratio:           {len(high)}/{len(results)} ({len(high)/max(len(results),1)*100:.0f}%)")
print(f"  LLM cost savings:     ~{(1 - len(high)/max(len(results),1))*100:.0f}%")

# Category breakdown for high-signal frames
print(f"\n{'=' * 100}")
print("  TOP CATEGORIES (high-signal frames)")
print(f"{'=' * 100}")
cat_counts = {}
for r in high:
    short = r["best_high"].split(",")[0].replace("an ", "").replace("a ", "")[:40]
    cat_counts[short] = cat_counts.get(short, 0) + 1
for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
    bar = "█" * min(count, 40)
    print(f"  {cat:42s}: {count:3d} {bar}")

# Save high-signal frames
print(f"\n{'=' * 100}")
print("  TOP 30 HIGH-SIGNAL FRAMES")
print(f"{'=' * 100}")

for idx, r in enumerate(high[:30]):
    short_high = r["best_high"].split(",")[0].replace("an ", "").replace("a ", "")[:25]
    short_low = r["best_low"].split(",")[0].replace("an ", "").replace("a ", "")[:25]
    slug = short_high.replace(" ", "-")[:30]
    out_name = f"{idx+1:02d}_geo{r['geo_score']:+.3f}_{r['time'].replace(':','m')}s_{slug}.jpg"
    shutil.copy2(r["frame_path"], str(OUT_DIR / out_name))

    print(f"\n  {idx+1:2d}. [{r['time']}]  geo_score={r['geo_score']:+.4f}")
    print(f"      HIGH: {short_high} ({r['best_high_score']:.3f})")
    print(f"      LOW:  {short_low} ({r['best_low_score']:.3f})")

# Also save rejected frames summary
print(f"\n{'=' * 100}")
print("  BOTTOM 10 (correctly filtered out?)")
print(f"{'=' * 100}")
rejected = [r for r in results if not r["is_high_signal"]]
rejected.sort(key=lambda x: x["geo_score"])
for r in rejected[:10]:
    short_low = r["best_low"].split(",")[0].replace("an ", "").replace("a ", "")[:30]
    print(f"  ✗ [{r['time']}] geo={r['geo_score']:+.3f}  → {short_low}")

print(f"\n  High-signal frames saved to: {OUT_DIR}/")
print(f"  Open: open \"{OUT_DIR}\"")

out_json = BASE_DIR / "clip_results.json"
serializable = [{k: v for k, v in r.items() if k not in ("frame_path", "all_scores")} for r in results]
with open(out_json, "w") as f:
    json.dump(serializable, f, indent=2)
print(f"  JSON: {out_json}")
