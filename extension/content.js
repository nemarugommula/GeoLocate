// ScenePoint — YouTube Content Script
// Injects "Find Location" button and results panel into YouTube pages.

(function () {
  if (window.__scenepoint_loaded) return;
  window.__scenepoint_loaded = true;

  const BUTTON_ID = "scenepoint-btn";
  const PANEL_ID = "scenepoint-panel";

  // ─── Frame Capture ───

  function captureFrame() {
    const video = document.querySelector("video");
    if (!video) {
      console.log("[ScenePoint] No video element found");
      return null;
    }
    if (video.readyState < 2) {
      console.log("[ScenePoint] Video not ready, readyState:", video.readyState);
      return null;
    }

    console.log("[ScenePoint] Capturing frame:", video.videoWidth, "x", video.videoHeight);

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 360;

    try {
      canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
      return dataUrl.split(",")[1];
    } catch (e) {
      console.error("[ScenePoint] Canvas capture failed (cross-origin?):", e);
      // Fallback: try capturing at a smaller size
      try {
        canvas.width = 320;
        canvas.height = 180;
        canvas.getContext("2d").drawImage(video, 0, 0, 320, 180);
        const dataUrl = canvas.toDataURL("image/jpeg", 0.7);
        return dataUrl.split(",")[1];
      } catch (e2) {
        console.error("[ScenePoint] Fallback capture also failed:", e2);
        return null;
      }
    }
  }

  // ─── Metadata Scraping ───

  function getVideoId() {
    const params = new URLSearchParams(window.location.search);
    return params.get("v") || "";
  }

  function getTimestamp() {
    const video = document.querySelector("video");
    return video ? video.currentTime : 0;
  }

  function getVideoTitle() {
    const el =
      document.querySelector("h1.ytd-watch-metadata yt-formatted-string") ||
      document.querySelector("h1.ytd-video-primary-info-renderer") ||
      document.querySelector("#title h1");
    return el ? el.textContent.trim() : document.title.replace(" - YouTube", "").trim();
  }

  function getVideoDescription() {
    const el =
      document.querySelector("#description-inline-expander .content") ||
      document.querySelector("ytd-text-inline-expander #plain-snippet-text") ||
      document.querySelector("#description ytd-text-inline-expander");
    return el ? el.textContent.trim().slice(0, 1000) : "";
  }

  function getChannelName() {
    const el =
      document.querySelector("#channel-name a") ||
      document.querySelector("ytd-channel-name a");
    return el ? el.textContent.trim() : "";
  }

  function getUserId() {
    // Try to get YouTube user ID from page config
    try {
      if (window.ytcfg) {
        const id = window.ytcfg.get("DELEGATED_SESSION_ID") || window.ytcfg.get("DATASYNC_ID");
        if (id) return "yt_" + id;
      }
    } catch {}
    return null; // fallback handled by background.js
  }

  // ─── UI: Button ───

  function injectButton() {
    if (document.getElementById(BUTTON_ID)) return;

    // Try 1: inject into YouTube player controls (the pin icon you saw earlier)
    const controls = document.querySelector(".ytp-right-controls");
    if (controls) {
      const btn = document.createElement("button");
      btn.id = BUTTON_ID;
      btn.className = "ytp-button scenepoint-player-btn";
      btn.title = "Find Location (ScenePoint)";
      btn.textContent = "📍";
      btn.addEventListener("click", onButtonClick);
      controls.prepend(btn);
      console.log("[ScenePoint] Button injected into player controls");
      return;
    }

    // Try 2: insert below the video player as a standalone button
    const player = document.querySelector("#movie_player") || document.querySelector("#player");
    if (player) {
      const btn = document.createElement("button");
      btn.id = BUTTON_ID;
      btn.title = "Find Location (ScenePoint)";
      btn.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="#4fc3f7" style="vertical-align:middle;margin-right:6px;">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg> Find Location`;
      btn.addEventListener("click", onButtonClick);
      const below = document.querySelector("#below") || player.parentElement;
      below.prepend(btn);
      console.log("[ScenePoint] Button injected below player");
      return;
    }

    // Retry if nothing found yet
    console.log("[ScenePoint] No injection point found, retrying in 2s...");
    setTimeout(injectButton, 2000);
  }

  // ─── UI: Side Panel ───

  const STEPS = [
    { id: "capture", label: "Capturing frame", duration: 1000, details: [
      "Extracting current video frame...",
      "Frame captured at {resolution}",
    ]},
    { id: "clip", label: "Analyzing scene type", duration: 4000, details: [
      "Running CLIP visual classifier...",
      "Comparing against 14 scene categories...",
      "Scene type: {clip_result}",
    ]},
    { id: "geoclip", label: "Predicting GPS coordinates", duration: 15000, details: [
      "Running GeoCLIP geolocation model...",
      "Generating top 5 coordinate predictions...",
      "Reverse-geocoding predictions...",
      "Best match: {geoclip_place}",
    ]},
    { id: "metadata", label: "Reading video metadata", duration: 3000, details: [
      "Parsing video title and description...",
      "Detecting language scripts...",
      "Extracting place names and country references...",
      "{metadata_result}",
    ]},
    { id: "llm", label: "AI triangulating location", duration: 50000, details: [
      "Combining all evidence signals...",
      "Analyzing terrain, vegetation, and architecture...",
      "Cross-referencing GPS predictions with metadata...",
      "Weighing confidence of each signal...",
      "Generating location hypothesis...",
      "Validating against geographic databases...",
      "Formatting evidence chain...",
    ]},
    { id: "geocode", label: "Resolving final coordinates", duration: 8000, details: [
      "Forward-geocoding best location match...",
      "Resolving place name to coordinates...",
      "Generating map reference...",
    ]},
  ];

  // ─── Map Tile Builder ───

  function latLonToTile(lat, lon, zoom) {
    const n = Math.pow(2, zoom);
    const latClamped = Math.max(-85, Math.min(85, lat));
    const x = Math.floor((lon + 180) / 360 * n);
    const latRad = latClamped * Math.PI / 180;
    const y = Math.floor((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * n);
    return { x: ((x % n) + n) % n, y: Math.max(0, Math.min(n - 1, y)) };
  }

  function buildMapTile(lat, lon, mapsUrl) {
    if (!lat || !lon || isNaN(lat) || isNaN(lon)) return "";

    const zoom = 10;
    const tile = latLonToTile(lat, lon, zoom);
    const n = Math.pow(2, zoom);
    const baseUrl = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile";

    const tiles = [];
    for (let dy = -1; dy <= 0; dy++) {
      for (let dx = -1; dx <= 1; dx++) {
        const tx = ((tile.x + dx) % n + n) % n;
        const ty = Math.max(0, Math.min(n - 1, tile.y + dy));
        tiles.push(`${baseUrl}/${zoom}/${ty}/${tx}`);
      }
    }

    return `
      <a class="scenepoint-map-tile" href="${mapsUrl || '#'}" target="_blank" title="View on Google Maps">
        <div class="scenepoint-map-grid">
          ${tiles.map(url => `<img src="${url}" alt="" onerror="this.style.background='#222'" />`).join("")}
        </div>
        <div class="scenepoint-map-pin">
          <svg viewBox="0 0 24 24" width="28" height="28">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="#d4a574" stroke="#1a1a1a" stroke-width="1.5"/>
            <circle cx="12" cy="9" r="2.5" fill="#1a1a1a"/>
          </svg>
        </div>
        <div class="scenepoint-map-label">View on Google Maps ↗</div>
      </a>
    `;
  }

  // ─── Glow System ───

  function showPageGlow() {
    let glow = document.getElementById("scenepoint-page-glow");
    if (!glow) {
      glow = document.createElement("div");
      glow.id = "scenepoint-page-glow";
      glow.className = "scenepoint-page-glow";
      document.body.appendChild(glow);
    }
    requestAnimationFrame(() => glow.classList.add("active"));
  }

  function migrateGlowToPanel() {
    const glow = document.getElementById("scenepoint-page-glow");
    if (glow) glow.classList.add("migrating");
    setTimeout(() => { if (glow) glow.remove(); }, 1000);
  }

  function glowFoundPulse(confidence) {
    // No panel glow — handled by scan beam stopping
  }

  function stopScanBeam() {
    const beam = document.querySelector(".scenepoint-scan-beam");
    if (beam) beam.classList.replace("active", "done");
  }

  // ─── Side Panel ───

  function openSidePanel(frameThumbnail) {
    removePanel();

    const panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.className = "scenepoint-side-panel";
    panel.innerHTML = `
      <div class="scenepoint-sp-header">
        <div class="scenepoint-sp-brand">
          <svg class="scenepoint-logo" viewBox="0 0 20 20" width="18" height="18" fill="none">
            <circle cx="10" cy="8" r="6" stroke="#d4a574" stroke-width="1.3"/>
            <circle cx="10" cy="8" r="2" fill="#d4a574"/>
            <path d="M10 14 L10 18" stroke="#d4a574" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <span class="scenepoint-sp-title">ScenePoint</span>
        </div>
        <button class="scenepoint-sp-close" id="scenepoint-close">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="1" y1="1" x2="13" y2="13"/><line x1="13" y1="1" x2="1" y2="13"/></svg>
        </button>
      </div>
      <div class="scenepoint-sp-thumbnail">
        <img src="data:image/jpeg;base64,${frameThumbnail}" alt="Captured frame" />
        <div class="scenepoint-scan-beam active"></div>
      </div>
      <div class="scenepoint-sp-steps" id="scenepoint-steps">
        ${STEPS.map(
          (s) => `
          <div class="scenepoint-step" id="scenepoint-step-${s.id}" data-status="pending">
            <div class="scenepoint-step-header">
              <span class="scenepoint-step-dot"></span>
              <span class="scenepoint-step-label">${s.label}</span>
              <span class="scenepoint-step-status"></span>
            </div>
            <div class="scenepoint-step-details" id="scenepoint-details-${s.id}"></div>
          </div>`
        ).join("")}
      </div>
      <div class="scenepoint-sp-result" id="scenepoint-result-area"></div>
    `;

    document.body.appendChild(panel);
    document.getElementById("scenepoint-close").addEventListener("click", removePanel);

    // Drag-to-resize from left edge
    const handle = document.createElement("div");
    handle.className = "scenepoint-resize-handle";
    panel.appendChild(handle);

    let startX, startWidth;
    handle.addEventListener("mousedown", (e) => {
      startX = e.clientX;
      startWidth = panel.offsetWidth;
      const onMove = (e) => {
        const diff = startX - e.clientX;
        panel.style.width = Math.max(320, Math.min(700, startWidth + diff)) + "px";
      };
      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      };
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });

    // Migrate the page glow to the panel glow
    setTimeout(migrateGlowToPanel, 200);
  }

  function removePanel() {
    const panel = document.getElementById(PANEL_ID);
    if (panel) panel.remove();
    const glow = document.getElementById("scenepoint-page-glow");
    if (glow) glow.remove();
  }

  function updateStep(stepId, status) {
    const el = document.getElementById(`scenepoint-step-${stepId}`);
    if (!el) return;
    el.dataset.status = status;
  }

  function addDetail(stepId, text) {
    const container = document.getElementById(`scenepoint-details-${stepId}`);
    if (!container) return;
    const line = document.createElement("div");
    line.className = "scenepoint-detail-line";
    line.textContent = text;
    container.appendChild(line);
    // Auto-scroll the panel to keep latest detail visible
    const panel = document.getElementById(PANEL_ID);
    if (panel) panel.scrollTop = panel.scrollHeight;
  }

  // State management
  let progressAborted = false;
  let currentAbortController = null;

  // ─── Persistence helpers (save to chrome.storage for popup) ───

  async function saveResultToHistory(result) {
    try {
      const data = await chrome.storage.local.get("scenepoint_history");
      const history = data.scenepoint_history || [];
      const videoId = result.video_id || getVideoId();
      history.unshift({
        id: result.id,
        videoId: videoId,
        timestamp: result.timestamp_seconds,
        location: result.location_name || result.country || "Unknown",
        region: result.region || "",
        country: result.country || "",
        confidence: result.confidence,
        lat: result.lat,
        lon: result.lon,
        mapsUrl: result.maps_url,
        thumb: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
        videoTitle: getVideoTitle().slice(0, 60),
        evidence: result.evidence || [],
        date: new Date().toISOString(),
      });
      await chrome.storage.local.set({ scenepoint_history: history.slice(0, 50) });
    } catch (e) {
      console.log("[ScenePoint] Could not save history:", e.message);
    }
  }

  async function incrementLocalLookupCount() {
    try {
      const data = await chrome.storage.local.get(["scenepoint_count", "scenepoint_date"]);
      const today = new Date().toISOString().slice(0, 10);
      const count = data.scenepoint_date === today ? (data.scenepoint_count || 0) + 1 : 1;
      await chrome.storage.local.set({ scenepoint_count: count, scenepoint_date: today });
    } catch (e) {
      console.log("[ScenePoint] Could not update count:", e.message);
    }
  }

  async function submitFeedbackDirect(lookupId, vote) {
    try {
      await fetch("https://vshnlucky-scenera-api.hf.space/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lookup_id: lookupId, vote: vote }),
      });
    } catch (e) {
      console.log("[ScenePoint] Feedback submit failed:", e.message);
    }
  }

  async function animateProgress() {
    progressAborted = false;

    for (let i = 0; i < STEPS.length; i++) {
      if (progressAborted) return;

      const step = STEPS[i];
      updateStep(step.id, "running");

      // Show each sub-detail one by one
      const detailDelay = step.duration / (step.details.length + 1);
      for (let d = 0; d < step.details.length; d++) {
        if (progressAborted) return;

        let text = step.details[d];
        // Replace placeholders with scraped info
        text = text.replace("{resolution}", `${document.querySelector("video")?.videoWidth || 640}×${document.querySelector("video")?.videoHeight || 360}px`);
        text = text.replace("{clip_result}", "evaluating...");
        text = text.replace("{geoclip_place}", "calculating...");
        text = text.replace("{metadata_result}", `Title: "${getVideoTitle().slice(0, 40)}..."`);

        addDetail(step.id, text);
        await new Promise((r) => setTimeout(r, detailDelay));
      }

      if (progressAborted) return;

      // Mark done (except last step — stays running until result)
      if (i < STEPS.length - 1) {
        updateStep(step.id, "done");
      }
    }

    // If we get here and no result yet, show a waiting message on last step
    if (!progressAborted) {
      addDetail(STEPS[STEPS.length - 1].id, "Almost there...");
      // Keep adding reassuring messages every 10s
      const interval = setInterval(() => {
        if (progressAborted) { clearInterval(interval); return; }
        const msgs = [
          "Still processing — complex scenes take longer...",
          "Cross-referencing geographic data...",
          "Running final validation checks...",
          "Refining coordinate precision...",
        ];
        addDetail(STEPS[STEPS.length - 1].id, msgs[Math.floor(Math.random() * msgs.length)]);
      }, 12000);
    }
  }

  function showResultInPanel(result) {
    // Stop the progress animation
    progressAborted = true;

    // Mark all steps done
    STEPS.forEach((s) => updateStep(s.id, "done"));

    // Stop scanning beam
    stopScanBeam();

    // Collapse the processing steps
    const stepsEl = document.getElementById("scenepoint-steps");
    if (stepsEl) stepsEl.classList.add("collapsed");

    const area = document.getElementById("scenepoint-result-area");
    if (!area) return;

    const conf = result.confidence || "NONE";
    const confClass = conf === "HIGH" ? "high" : conf === "MEDIUM" ? "medium" : "low";

    const locationParts = [result.location_name, result.region, result.country].filter(Boolean);
    const uniqueParts = [...new Set(locationParts)];
    const locationText = uniqueParts.join(", ") || "Could not determine location";

    const evidenceHtml = (result.evidence || [])
      .map(
        (e) => `
        <div class="scenepoint-ev-item">
          <div class="scenepoint-ev-source">${e.source}</div>
          <div class="scenepoint-ev-detail">${e.detail}</div>
        </div>`
      )
      .join("");

    const mapTileHtml = result.lat && result.lon ? buildMapTile(result.lat, result.lon, result.maps_url) : "";

    area.innerHTML = `
      <span class="scenepoint-sp-conf ${confClass}">${conf}</span>
      <div class="scenepoint-sp-location">${locationText}</div>
      ${
        result.lat && result.lon
          ? `<div class="scenepoint-sp-coords">${result.lat.toFixed(4)}°N, ${result.lon.toFixed(4)}°E</div>`
          : ""
      }
      ${mapTileHtml}
      <div class="scenepoint-sp-evidence">
        <div class="scenepoint-sp-ev-title">Evidence chain</div>
        ${evidenceHtml}
      </div>
      <div class="scenepoint-sp-feedback">
        <span>Was this correct?</span>
        <button class="scenepoint-fb-btn" data-vote="up" data-id="${result.id}">👍 Yes</button>
        <button class="scenepoint-fb-btn" data-vote="down" data-id="${result.id}">👎 No</button>
      </div>
    `;

    // Animate result into view
    requestAnimationFrame(() => {
      setTimeout(() => area.classList.add("visible"), 50);
    });

    area.querySelectorAll(".scenepoint-fb-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        submitFeedbackDirect(btn.dataset.id, btn.dataset.vote);
        btn.closest(".scenepoint-sp-feedback").innerHTML = `<span class="scenepoint-fb-thanks">Thanks for the feedback!</span>`;
      });
    });
  }

  function showErrorInPanel(message) {
    progressAborted = true;
    STEPS.forEach((s) => updateStep(s.id, "error"));
    const area = document.getElementById("scenepoint-result-area");
    if (area) {
      area.innerHTML = `<div class="scenepoint-sp-error">⚠ ${message}</div>`;
    }
  }

  // ─── Main Click Handler ───

  async function onButtonClick() {
    console.log("[ScenePoint] Button clicked");

    // Capture frame FIRST (for thumbnail)
    let frameB64;
    try {
      frameB64 = captureFrame();
    } catch (e) {
      console.error("[ScenePoint] Frame capture error:", e);
    }

    if (!frameB64) {
      // Can't open panel without a frame — show a quick alert
      console.warn("[ScenePoint] Couldn't capture frame. Video might not be playing.");
      return;
    }

    // Step 1: Page glow ignites
    showPageGlow();

    // Step 2: After brief glow, open side panel (glow migrates)
    await new Promise((r) => setTimeout(r, 500));
    openSidePanel(frameB64);

    // Animate progress steps (runs in parallel with the actual API call)
    const progressPromise = animateProgress();

    // Get user ID — persist it so rate limiting works
    let userId = getUserId();
    if (!userId) {
      try {
        const stored = await chrome.storage.local.get("scenepoint_user_id");
        if (stored.scenepoint_user_id) {
          userId = stored.scenepoint_user_id;
        } else {
          userId = "anon_" + Math.random().toString(36).slice(2, 10);
          await chrome.storage.local.set({ scenepoint_user_id: userId });
        }
      } catch (e) {
        userId = "anon_fallback";
      }
    }

    // Build payload
    const payload = {
      image_b64: frameB64,
      video_id: getVideoId(),
      timestamp_seconds: getTimestamp(),
      video_title: getVideoTitle(),
      video_description: getVideoDescription(),
      channel_name: getChannelName(),
      user_id: userId,
    };
    console.log("[ScenePoint] Sending lookup:", payload.video_id, payload.channel_name);

    // Abort any previous in-flight request
    if (currentAbortController) currentAbortController.abort();
    currentAbortController = new AbortController();

    // Call backend directly via fetch
    try {
      const API_URL = "https://vshnlucky-scenera-api.hf.space";
      const resp = await fetch(`${API_URL}/lookup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: currentAbortController.signal,
      });

      if (resp.status === 429) {
        showErrorInPanel("You've used all free lookups today. Come back tomorrow!");
        return;
      }

      if (!resp.ok) {
        showErrorInPanel(`Server error (${resp.status}). Is the backend running?`);
        return;
      }

      const result = await resp.json();

      // Save to local storage for popup history
      await saveResultToHistory(result);
      await incrementLocalLookupCount();

      showResultInPanel(result);

    } catch (e) {
      if (e.name === "AbortError") {
        console.log("[ScenePoint] Request aborted (navigation or new lookup)");
        return;
      }
      console.error("[ScenePoint] Fetch error:", e);
      showErrorInPanel("Cannot reach ScenePoint server. Please try again in a moment.");
    } finally {
      currentAbortController = null;
    }
  }

  // ─── History Panel ───

  async function openHistoryPanel() {
    removePanel();

    let items = [];
    try {
      const data = await chrome.storage.local.get("scenepoint_history");
      items = data.scenepoint_history || [];
    } catch (e) {
      console.log("[ScenePoint] Could not load history:", e.message);
    }

    const panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.className = "scenepoint-side-panel";
    panel.style.animationDelay = "0s";

    const emptyHtml = `<div class="scenepoint-history-empty">No lookups yet.<br>Click the pin icon on any YouTube video.</div>`;

    const listHtml = items.length === 0 ? emptyHtml : items.map((item, i) => {
      const confClass = (item.confidence || "").toLowerCase();
      const loc = [item.location, item.country].filter(Boolean).join(", ");
      const date = new Date(item.date).toLocaleDateString();
      return `
        <div class="scenepoint-history-card" data-index="${i}">
          <img class="scenepoint-history-thumb" src="${item.thumb}" alt="" />
          <div class="scenepoint-history-info">
            <div class="scenepoint-history-loc">
              <span class="scenepoint-sp-conf ${confClass}" style="font-size:9px;padding:2px 6px;margin:0">${item.confidence || "?"}</span>
              ${loc || "Unknown"}
            </div>
            <div class="scenepoint-history-meta">${item.videoTitle || ""}</div>
            <div class="scenepoint-history-date">${date}</div>
          </div>
        </div>`;
    }).join("");

    panel.innerHTML = `
      <div class="scenepoint-sp-header">
        <div class="scenepoint-sp-brand">
          <svg class="scenepoint-logo" viewBox="0 0 20 20" width="18" height="18" fill="none">
            <circle cx="10" cy="8" r="6" stroke="#d4a574" stroke-width="1.3"/>
            <circle cx="10" cy="8" r="2" fill="#d4a574"/>
            <path d="M10 14 L10 18" stroke="#d4a574" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <span class="scenepoint-sp-title">ScenePoint</span>
        </div>
        <button class="scenepoint-sp-close" id="scenepoint-close">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="1" y1="1" x2="13" y2="13"/><line x1="13" y1="1" x2="1" y2="13"/></svg>
        </button>
      </div>
      <div class="scenepoint-search-box">
        <input type="text" id="scenepoint-search" placeholder="Search locations..." autocomplete="off" />
      </div>
      <div class="scenepoint-history-title">Recent Lookups</div>
      <div class="scenepoint-history-list">${listHtml}</div>
    `;

    document.body.appendChild(panel);
    document.getElementById("scenepoint-close").addEventListener("click", removePanel);

    // Search filter
    document.getElementById("scenepoint-search").addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase();
      panel.querySelectorAll(".scenepoint-history-card").forEach((card) => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(q) ? "" : "none";
      });
    });

    // Click on history card → show detail view inside the panel
    panel.querySelectorAll(".scenepoint-history-card").forEach((card) => {
      card.addEventListener("click", () => {
        const idx = parseInt(card.dataset.index);
        const item = items[idx];
        if (item) showHistoryDetail(item, panel);
      });
    });
  }

  function showHistoryDetail(item, panel) {
    const conf = (item.confidence || "NONE").toUpperCase();
    const confClass = conf === "HIGH" ? "high" : conf === "MEDIUM" ? "medium" : "low";
    const locParts = [item.location, item.region, item.country].filter(Boolean);
    const loc = [...new Set(locParts)].join(", ") || "Unknown";
    const mapTileHtml = item.lat && item.lon ? buildMapTile(item.lat, item.lon, item.mapsUrl) : "";

    const evidenceHtml = (item.evidence || []).map(e => `
      <div class="scenepoint-ev-item">
        <div class="scenepoint-ev-source">${e.source}</div>
        <div class="scenepoint-ev-detail">${e.detail}</div>
      </div>
    `).join("");

    const contentArea = panel.querySelector(".scenepoint-history-title");
    const listArea = panel.querySelector(".scenepoint-history-list");

    if (contentArea) contentArea.remove();
    if (listArea) {
      listArea.innerHTML = `
        <div class="scenepoint-detail-view">
          <button class="scenepoint-back-btn" id="scenepoint-back">← Back to list</button>

          <div class="scenepoint-sp-thumbnail" style="padding:12px 0 8px">
            <img src="${item.thumb}" alt="Video thumbnail" />
          </div>
          <div class="scenepoint-detail-video-title">${item.videoTitle || ""}</div>

          <span class="scenepoint-sp-conf ${confClass}">${conf}</span>
          <div class="scenepoint-sp-location">${loc}</div>

          ${item.lat && item.lon
            ? `<div class="scenepoint-sp-coords">${item.lat.toFixed(4)}°N, ${item.lon.toFixed(4)}°E</div>`
            : ""}

          ${mapTileHtml}

          ${evidenceHtml ? `
            <div class="scenepoint-sp-evidence">
              <div class="scenepoint-sp-ev-title">Evidence chain</div>
              ${evidenceHtml}
            </div>
          ` : ""}

          <a class="scenepoint-detail-yt-link" href="https://www.youtube.com/watch?v=${item.videoId}&t=${Math.floor(item.timestamp || 0)}s" target="_blank">
            Watch on YouTube at ${Math.floor((item.timestamp || 0) / 60)}:${String(Math.floor((item.timestamp || 0) % 60)).padStart(2, "0")} ↗
          </a>
        </div>
      `;

      document.getElementById("scenepoint-back").addEventListener("click", () => {
        removePanel();
        openHistoryPanel();
      });
    }
  }

  // Listen for messages from background script (extension icon click)
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "TOGGLE_PANEL") {
      const panel = document.getElementById(PANEL_ID);
      if (panel) {
        removePanel();
      } else {
        openHistoryPanel();
      }
    }
  });

  // ─── Initialize ───

  function init() {
    injectButton();
  }

  // YouTube is a SPA — re-inject on navigation
  const observer = new MutationObserver(() => {
    if (window.location.pathname === "/watch") {
      setTimeout(injectButton, 1000);
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });

  // YouTube SPA navigation — close panel, abort request, re-inject button
  window.addEventListener("yt-navigate-finish", () => {
    removePanel();
    if (currentAbortController) currentAbortController.abort();
    progressAborted = true;
    setTimeout(injectButton, 1000);
  });

  // Initial inject
  if (document.readyState === "complete") {
    init();
  } else {
    window.addEventListener("load", init);
  }
})();
