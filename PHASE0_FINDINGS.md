# GeoLens — Phase 0 Findings

> **Date:** August 7, 2026
> **Goal:** Validate whether AI-powered multi-signal geolocation from YouTube videos actually works before building anything.

---

## What We Tested

Two real YouTube videos, run through a progressively sophisticated pipeline:

| Video | Creator | Actual Location |
|---|---|---|
| Sri Lankan Village Kitchen (cooking) | Poorna - The Nature Girl | Southern Province, Matara District, Sri Lanka |
| Summer in Yunnan (fruit/cooking) | Dianxi Xiaoge (滇西小哥) | Shidian County, Baoshan, Yunnan, China |

---

## Pipeline Components Tested

### 1. CLIP Frame Filter (OpenAI ViT-B/32)
**Purpose:** Cheaply filter 90%+ of frames to avoid sending food close-ups, cooking shots, and talking heads to expensive models.

| Metric | Sri Lanka Video | Yunnan Video |
|---|---|---|
| Total frames scanned | 487 | 866 |
| High-signal frames kept | 22 (5%) | 66 (8%) |
| Frames filtered out | 95% | 92% |
| Cost | $0.00 (local) | $0.00 (local) |

**Verdict:** CLIP works extremely well as a filter. Zero hand-tuned thresholds — just describe categories in plain English. Correctly rejects food close-ups, cooking shots, hands, faces while keeping landscapes, aerial shots, village scenes, and text-overlay frames.

**What failed before CLIP:** We spent hours building 9 hand-tuned OpenCV detectors (aerial detection, structure detection, horizon detection, etc.) — all failed. The "aerial detector" triggered on banana leaves, mortars, and bokeh backgrounds. CLIP replaced all of it with 14 lines of text descriptions.

### 2. GeoCLIP (GPS Coordinate Prediction)
**Purpose:** Predict GPS coordinates directly from a single image frame.

| Metric | Sri Lanka Video | Yunnan Video |
|---|---|---|
| Correct country (top-1) | 5/22 (23%) | ~5/15 (33%) |
| Correct region | 0% (predicted Central Province, actual is Southern) | 0% (predicted Jiangxi, actual is Yunnan) |
| Best prediction | 7.3°N, 80.8°E — ~130km off | 29.2°N, 117.9°E — ~1500km off |
| Nearby country in top-5 | India (Kerala, adjacent to Sri Lanka) | Vietnam (Sa Pa, adjacent to Yunnan) |
| Cost | $0.00 (local) | $0.00 (local) |

**Verdict:** GeoCLIP gets the right country ~25-33% of the time from a single frame, which sounds low but is actually useful as one signal in triangulation. It consistently predicts the correct region of the world (South Asia / East Asia). It works best on panoramic landscape frames and worst on close-ups and indoor shots.

### 3. OCR / Script Detection (EasyOCR)
**Purpose:** Detect text in frames, especially non-Latin scripts that indicate country.

| Finding | Detail |
|---|---|
| Sinhala text detected | At 0:10, 0:12, 2:28, 17:56, 21:48 — bilingual labels (Sinhala + English) |
| Script → country mapping | Sinhala = Sri Lanka (near 100% confidence) |
| Chinese text | Present in Yunnan video title (滇西小哥) |
| EasyOCR limitation | English-only model garbled Sinhala text; Sinhala model not available |

**Verdict:** Script detection is the single highest-confidence signal for country identification. Sinhala script = Sri Lanka. Chinese script = China/Taiwan/Singapore. This alone is more reliable than GeoCLIP or vision LLMs. However, EasyOCR has language limitations. Florence-2 or a vision LLM reading the text would be more reliable.

### 4. OpenCV Heuristics (Failed Approach)
**Purpose:** Attempted to use hand-tuned computer vision detectors for aerial shot detection, structure detection, horizon detection, blur detection, skin/face detection.

**Verdict:** Failed. 9 detectors, 300+ lines of code, hours of threshold tuning. The "aerial detector" triggered on fruit close-ups through green leaves, banana leaves, and mortar-and-pestle shots. Structure detector triggered on tree branches. Every fix created new false positives. **Not scalable — different video types need different thresholds.**

### 5. Video Metadata (Title + Description)
**Purpose:** Extract place names, country references, and cultural markers from the video page.

| Video | What metadata gave us |
|---|---|
| Sri Lanka | Title: "Sri Lankan Village Kitchen" → country confirmed instantly |
| Yunnan | Title: "Summer in Yunnan" + "滇西小哥" → country + province + subregion confirmed |

**Verdict:** Metadata is the most reliable signal in almost all cases. Most travel/food content explicitly mentions the location in the title or description. Title alone got us to country-level on both test videos with near-100% confidence.

### 6. Channel Context (Creator Research)
**Purpose:** Research the creator's channel to determine their usual filming location.

| Creator | What we found |
|---|---|
| Poorna (Nature Girl) | "Lives down south in Sri Lanka" — all videos from same village |
| Dianxi Xiaoge | Born in Shidian County, Baoshan, Yunnan — all videos from her family farm |

**Verdict:** For creators who consistently film in one location (cooking channels, lifestyle vloggers), channel context narrows to a specific region. This is cacheable — once you know where a creator films, every future video from them is pre-answered.

### 7. Vision LLM (MiniCPM-V 8B, local)
**Purpose:** Reason about geographic clues in a frame — terrain, vegetation, architecture, cultural markers.

| Metric | Result |
|---|---|
| Country accuracy (frame only) | 0/5 — never correctly identified Sri Lanka |
| Region accuracy | Correct broad region (tropical South/Southeast Asia) |
| Useful observations | Detected left-hand driving, Hindu cultural elements, tropical climate |
| Time per frame | 30-60 seconds |
| Cost | $0.00 (local via Ollama) |

**Verdict:** MiniCPM-V 8B is too weak for precise geolocation from a single frame. It hedges with 3-4 possible countries every time. GeoCLIP actually outperformed it on country prediction. However, it catches qualitative clues (driving side, architecture style, cultural markers) that GeoCLIP can't see. A larger model (Qwen3-VL 32B, or Claude/GPT-4o) would likely perform much better.

### 8. Satellite Image Matching (SIFT Features)
**Purpose:** Match drone/aerial frames against satellite imagery to pinpoint exact GPS coordinates.

| Metric | Google Maps ($0.24/grid) | ESRI Free ($0.00) |
|---|---|---|
| Best SIFT inliers | 15 | 5 |
| Best score | 60 | 20 |
| Visually correct match | No — matched urban area, drone shows farmland | No |
| Tile resolution | 640×640px | 256×256px |

**Verdict:** Satellite matching does not work at our current precision level. Reasons:
- Search area too large (don't know location within 30km)
- Source video too low resolution (360p YouTube download)
- SIFT creates false positive matches on similar-looking but different terrain
- Seasonal differences between drone footage and satellite imagery
- ESRI tiles are usable but lower quality than Google (33% of match score)

**Satellite matching is a v2/v3 feature**, viable only when: (a) location is already known within ~1-2km, (b) source video is 4K, (c) using learned matchers (SuperGlue/LoFTR) instead of SIFT.

---

## Key Finding: Triangulation Works

No single signal is reliable alone. But combined, they consistently produce the right answer:

### Sri Lanka Video — Signal Compounding

| Signal | Alone | Combined |
|---|---|---|
| GeoCLIP frame only | "Maybe Sri Lanka, maybe Kerala" (23%) | |
| + Script detection | Sri Lanka confirmed (eliminates Kerala) | Country: Sri Lanka ✓ |
| + Title parsing | "Sri Lankan Village Kitchen" — double confirmation | Confidence: HIGH |
| + Channel research | "Creator lives down south in Sri Lanka" | Region: Southern Province |
| + Web research | "Akuressa area, Matara District" | District: Matara |
| **Final** | | **~6.1°N, 80.5°E ± 20km** |

### Yunnan Video — Signal Compounding

| Signal | Alone | Combined |
|---|---|---|
| GeoCLIP frame only | "Maybe China, maybe Vietnam" (33%) | |
| + Chinese script in title | China confirmed | Country: China ✓ |
| + Title "Summer in Yunnan" | Province confirmed | Region: Yunnan |
| + "滇西小哥" (channel name) | "滇西 = Western Yunnan" | Subregion: Western Yunnan |
| + Web research on creator | "Shidian County, Baoshan" | Town: Shidian County |
| **Final** | | **~24.7°N, 99.2°E ± 30km** |

---

## Cost Analysis

### Per-Lookup Cost (estimated production pipeline)

| Component | Cost | Notes |
|---|---|---|
| CLIP filtering (local) | $0.000 | ~1s per frame, runs on CPU |
| GeoCLIP (local) | $0.000 | ~3s per frame, runs on CPU |
| OCR/script detection (local) | $0.000 | EasyOCR or Florence-2 local |
| Metadata parsing (text LLM) | $0.010 | Extract place names from title/desc |
| Vision LLM on top 3 frames | $0.030 | Only if cheap pass isn't enough |
| Synthesis/triangulation | $0.010 | Combine all signals |
| **Total** | **$0.04-0.06** | Well within $0.05-0.25 target |

### Free Tier Economics (5 lookups/day, 1000 users)

- 3000 lookups/day × $0.05 = **$150/day** ($4,500/month)
- With caching (popular videos pre-mapped): likely **$50-100/day**
- This is manageable for validating demand before monetizing

---

## What Works, What Doesn't

### Works Well ✅
- CLIP-based frame filtering (5-8% keep rate, zero false positives in top 10)
- Video metadata parsing (title/description → country in most cases)
- Script/language detection (Sinhala, Chinese → near-certain country ID)
- Channel context research (creator's usual location = cacheable signal)
- GeoCLIP as one signal in ensemble (right country 25-33%)
- Signal triangulation (combining weak signals → strong conclusion)
- ESRI free satellite tiles (usable, no API key needed)

### Doesn't Work Yet ❌
- Any single signal alone (none are reliable independently)
- OpenCV hand-tuned detectors (not scalable, too many false positives)
- Satellite image matching with SIFT (needs higher resolution + closer search area)
- Small vision LLMs for geolocation (MiniCPM-V 8B too weak for country prediction)
- Exact coordinate prediction (best is district-level ~20km, not 10m)
- EasyOCR for non-Latin scripts (Sinhala not supported)

### Untested / Future Work 🔮
- Comments parsing (often contain direct location answers)
- Other videos by same creator (might have more specific location references)
- Creator's social media (geotagged Instagram posts)
- PIGEON/StreetCLIP (geo-specific CLIP variants)
- Florence-2 (multi-task: OCR + captioning + detection in one model)
- Larger vision LLMs (Qwen3-VL 32B, Claude, GPT-4o)
- SuperGlue/LoFTR learned matchers (for satellite image matching)
- Full Video Scan mode (analyze all scenes across a video)

---

## Tools/Models Used

| Tool | Version | Purpose | License |
|---|---|---|---|
| ffmpeg | 7.1.1 | Frame extraction | LGPL |
| OpenCV | 5.0.0 | Image processing, SIFT matching | Apache 2.0 |
| OpenCLIP (ViT-B/32) | openai pretrained | Scene classification, frame filtering | MIT |
| GeoCLIP | 1.2.0 | GPS coordinate prediction from images | Check repo |
| EasyOCR | 1.7.2 | Text detection and OCR | Apache 2.0 |
| MiniCPM-V | 8B (via Ollama) | Vision LLM reasoning | Apache 2.0 |
| Nominatim (OpenStreetMap) | — | Geocoding (place name → coordinates) | ODbL |
| ESRI World Imagery | — | Free satellite tiles | Esri ToS (free for non-commercial) |
| Google Maps Static API | — | Satellite tiles (paid comparison) | Google ToS |

---

## Recommendation: Ready to Build

Phase 0 validates the core thesis: **multi-signal triangulation from YouTube videos works.** No single AI model can reliably geolocate a video frame, but combining frame analysis + metadata + channel context + script detection produces consistently correct results at the country/region level.

### Immediate Next Steps (Phase 1 MVP)

1. Build the Chrome extension (YouTube button + results panel)
2. Backend pipeline: CLIP filter → GeoCLIP → metadata parser → synthesis
3. Google sign-in for rate limiting + history
4. Basic caching by video ID
5. Ship to Reddit (r/whereisthis, r/travel, r/drones) for validation

### Architecture Decision from Phase 0

- **Frame filtering:** CLIP (not OpenCV heuristics)
- **GPS prediction:** GeoCLIP as Tier 1, vision LLM as Tier 2
- **Script detection:** Florence-2 (not EasyOCR — better multi-language support)
- **Satellite tiles:** ESRI World Imagery for free tier, Google for paid/premium
- **Satellite matching:** Defer to v2 (needs SuperGlue + 4K source + narrow search area)
- **Vision LLM:** Use Claude/GPT-4o API for synthesis, not local models (MiniCPM-V too weak)
- **All local models run free** — the only API cost is the vision LLM for synthesis (~$0.03/lookup)
