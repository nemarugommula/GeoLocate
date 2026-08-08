import os
import sys
import subprocess
import easyocr
import cv2
import json
import numpy as np
from pathlib import Path

VIDEO_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Downloads/Santol Fruit Pickle Welithalapa Egg Hoppers and Fiery Sauce from My Sri Lankan Village Kitchen.mp4"
)
FRAME_INTERVAL = 2
FRAMES_DIR = Path(__file__).parent / "ocr-frames"
FRAMES_DIR.mkdir(exist_ok=True)

print("Loading EasyOCR model (English — CRAFT detector finds text in any script)...")
reader = easyocr.Reader(["en"], gpu=False, verbose=False)
print("Model loaded.\n")


def get_duration(video_path):
    result = subprocess.run(["ffmpeg", "-i", video_path], capture_output=True, text=True)
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = time_str.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0


def extract_frame(video_path, timestamp, output_path):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
         "-frames:v", "1", "-q:v", "2", output_path],
        capture_output=True
    )


def classify_frame(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]

    green_mask = cv2.inRange(hsv, (25, 30, 30), (95, 255, 255))
    green_ratio = cv2.countNonZero(green_mask) / (h * w)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = cv2.countNonZero(edges) / (h * w)

    brightness = hsv[:, :, 2].mean()
    saturation = hsv[:, :, 1].mean()

    sky_mask = cv2.inRange(hsv, (90, 20, 150), (130, 255, 255))
    sky_ratio = cv2.countNonZero(sky_mask) / (h * w)

    if green_ratio > 0.4 and edge_ratio < 0.15:
        return "outdoor-landscape", {"green": green_ratio, "sky": sky_ratio, "brightness": brightness}
    elif green_ratio > 0.25 or sky_ratio > 0.15:
        return "outdoor-scene", {"green": green_ratio, "sky": sky_ratio, "brightness": brightness}
    elif brightness < 80:
        return "indoor-dark", {"green": green_ratio, "brightness": brightness}
    else:
        return "indoor-bright", {"green": green_ratio, "brightness": brightness}


def detect_text(image_path):
    results = reader.readtext(image_path, paragraph=False)

    detections = []
    for (bbox, text, conf) in results:
        text = text.strip()
        if len(text) < 2:
            continue

        is_non_latin = any(ord(ch) > 127 and not ch.isspace() for ch in text)

        script = "unknown"
        for ch in text:
            cp = ord(ch)
            if 0x0D80 <= cp <= 0x0DFF:
                script = "sinhala"
                break
            elif 0x0B80 <= cp <= 0x0BFF:
                script = "tamil"
                break
            elif 0x0900 <= cp <= 0x097F:
                script = "devanagari"
                break
            elif 0x0600 <= cp <= 0x06FF:
                script = "arabic"
                break
            elif 0x0E00 <= cp <= 0x0E7F:
                script = "thai"
                break
            elif 0x4E00 <= cp <= 0x9FFF:
                script = "chinese"
                break
            elif 0x3040 <= cp <= 0x30FF:
                script = "japanese"
                break
            elif 0xAC00 <= cp <= 0xD7AF:
                script = "korean"
                break
        if script == "unknown" and not is_non_latin:
            script = "latin"

        detections.append({
            "text": text,
            "confidence": round(conf, 3),
            "script": script,
            "is_non_latin": is_non_latin,
            "bbox": [[int(p[0]), int(p[1])] for p in bbox]
        })

    return detections


LOCATION_KEYWORDS = {
    "road", "street", "km", "mile", "station", "temple", "church",
    "mosque", "bridge", "river", "lake", "mountain", "hill", "village",
    "town", "city", "district", "province", "north", "south", "east", "west",
    "welcome", "entrance", "exit", "hotel", "resort", "beach", "falls",
    "national", "park", "reserve", "highway", "route", "airport", "harbor",
    "fort", "palace", "museum", "garden", "zoo", "dam", "waterfall",
    "island", "bay", "cape", "valley", "plateau", "forest", "jungle"
}

SCRIPT_TO_COUNTRY = {
    "sinhala": ["Sri Lanka"],
    "tamil": ["Sri Lanka", "India (Tamil Nadu)", "Singapore", "Malaysia"],
    "devanagari": ["India", "Nepal"],
    "thai": ["Thailand"],
    "arabic": ["Middle East / North Africa"],
    "chinese": ["China", "Taiwan", "Singapore"],
    "japanese": ["Japan"],
    "korean": ["South Korea", "North Korea"],
}


def score_frame(detections, frame_type):
    score = 0
    reasons = []
    country_hints = []

    for det in detections:
        if det["script"] != "latin" and det["script"] != "unknown":
            score += 50
            countries = SCRIPT_TO_COUNTRY.get(det["script"], ["Unknown"])
            country_hints.extend(countries)
            reasons.append(f"{det['script'].upper()} script detected: \"{det['text']}\" → {', '.join(countries)}")

        if det["script"] == "latin" and det["confidence"] > 0.3:
            words = [w for w in det["text"].split() if len(w) > 2]
            if len(words) >= 1:
                score += 15
                reasons.append(f"Latin text: \"{det['text']}\" (conf: {det['confidence']:.0%})")

            found_kw = [w for w in words if w.lower() in LOCATION_KEYWORDS]
            if found_kw:
                score += 25
                reasons.append(f"Location keywords: {', '.join(found_kw)}")

    if frame_type == "outdoor-landscape":
        score += 20
        reasons.append("Outdoor landscape (high geolocation value)")
    elif frame_type == "outdoor-scene":
        score += 10
        reasons.append("Outdoor scene")

    return score, reasons, list(set(country_hints))


print(f"Video: {os.path.basename(VIDEO_PATH)}")
duration = get_duration(VIDEO_PATH)
print(f"Duration: {duration:.0f}s ({duration / 60:.1f} min)")

total_frames = int(duration / FRAME_INTERVAL)
print(f"Scanning {total_frames} frames (every {FRAME_INTERVAL}s)...")
print("-" * 90)

results = []
for i in range(total_frames):
    ts = i * FRAME_INTERVAL
    mins, secs = divmod(ts, 60)
    frame_path = str(FRAMES_DIR / f"frame_{ts:04d}.jpg")

    extract_frame(VIDEO_PATH, ts, frame_path)
    if not os.path.exists(frame_path):
        continue

    img = cv2.imread(frame_path)
    if img is None:
        continue

    frame_type, frame_props = classify_frame(img)
    detections = detect_text(frame_path)
    score, reasons, country_hints = score_frame(detections, frame_type)

    results.append({
        "timestamp": ts,
        "time": f"{int(mins):02d}:{int(secs):02d}",
        "frame_path": frame_path,
        "frame_type": frame_type,
        "score": score,
        "reasons": reasons,
        "country_hints": country_hints,
        "detections": detections,
        "frame_props": {k: round(v, 3) if isinstance(v, float) else v for k, v in frame_props.items()}
    })

    status = f"  [{int(mins):02d}:{int(secs):02d}] {frame_type:18s}"
    if score > 0:
        flag = " ★★★" if score >= 50 else " ★★" if score >= 30 else " ★"
        print(f"{status} | score={score:3d}{flag} | {'; '.join(reasons)}")
    else:
        sys.stdout.write(f"\r  Scanning... {int(mins):02d}:{int(secs):02d} / {int(duration//60):02d}:{int(duration%60):02d}")
        sys.stdout.flush()

print("\r" + " " * 80)
results.sort(key=lambda x: x["score"], reverse=True)

print("\n" + "=" * 90)
print("  TOP HIGH-SIGNAL FRAMES")
print("=" * 90)

high_signal = [r for r in results if r["score"] >= 20]
for r in high_signal[:15]:
    print(f"\n  ★ [{r['time']}] Score: {r['score']}  |  Type: {r['frame_type']}")
    for reason in r["reasons"]:
        print(f"      → {reason}")
    if r["country_hints"]:
        print(f"      🌍 Country hints: {', '.join(r['country_hints'])}")
    for det in r["detections"]:
        print(f"      📝 \"{det['text']}\" ({det['script']}, conf: {det['confidence']:.0%})")

print("\n" + "=" * 90)
print("  FRAME TYPE DISTRIBUTION")
print("=" * 90)
type_counts = {}
for r in results:
    type_counts[r["frame_type"]] = type_counts.get(r["frame_type"], 0) + 1
for ft, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    bar = "█" * int(count / len(results) * 40)
    print(f"  {ft:20s}: {count:3d} ({count/len(results)*100:4.0f}%) {bar}")

all_scripts = {}
all_countries = {}
for r in results:
    for det in r.get("detections", []):
        s = det["script"]
        all_scripts[s] = all_scripts.get(s, 0) + 1
    for c in r.get("country_hints", []):
        all_countries[c] = all_countries.get(c, 0) + 1

if all_scripts:
    print("\n" + "=" * 90)
    print("  SCRIPTS DETECTED ACROSS VIDEO")
    print("=" * 90)
    for s, count in sorted(all_scripts.items(), key=lambda x: -x[1]):
        print(f"  {s:15s}: {count:3d} detections")

if all_countries:
    print("\n" + "=" * 90)
    print("  COUNTRY SIGNALS (from script detection)")
    print("=" * 90)
    for c, count in sorted(all_countries.items(), key=lambda x: -x[1]):
        print(f"  {c:30s}: {count:3d} signals")

print(f"\n{'=' * 90}")
print(f"  SUMMARY")
print(f"{'=' * 90}")
print(f"  Total frames scanned:  {len(results)}")
print(f"  High-signal frames:    {len(high_signal)}")
print(f"  Frames with text:      {sum(1 for r in results if r['detections'])}")
print(f"  Frames worth analyzing: {len(high_signal)}/{len(results)} ({len(high_signal)/len(results)*100:.0f}%)")
if all_countries:
    top_country = max(all_countries, key=all_countries.get)
    print(f"  Strongest country signal: {top_country} ({all_countries[top_country]} detections)")

output_path = Path(__file__).parent / "ocr_results.json"
with open(output_path, "w") as f:
    json.dump(results[:50], f, indent=2, default=str)
print(f"\n  Results saved to: {output_path}")
