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
      btn.title = "Find where this was filmed";
      btn.innerHTML = `<svg viewBox="0 0 24 24" width="28" height="28"><path d="M12,2C8.1,2,5,5.1,5,9c0,5.3,7,13,7,13s7-7.8,7-13C19,5.1,15.9,2,12,2z" fill="#F76D57"/><circle cx="12" cy="9" r="3" fill="#1a1a1a"/></svg>`;
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
      btn.title = "Find where this was filmed";
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
    { id: "llm", label: "Triangulating location", duration: 50000, details: [
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
    const oldPanel = document.getElementById(PANEL_ID);
    if (oldPanel) oldPanel.remove();

    const panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.className = "scenepoint-side-panel";
    panel.innerHTML = `
      <div class="scenepoint-sp-header">
        <div class="scenepoint-sp-brand">
          <svg viewBox="0 0 64 64" width="26" height="26" xmlns="http://www.w3.org/2000/svg"><path d="m18.68 10.74a26.63 26.63 0 0 1 11.25-3.53c4.25-.21 8.15.79 13.56 3.38s8.4 5.06 10.69 9.31 3.53 7.38 2.28 12.91-1.63 11.09-3.85 14.93-5.93 6.5-11.43 7.88-13.32 2.28-20.07-1.44-11.5-9.25-13.25-16.9-.31-11.63 1-15.22a23.64 23.64 0 0 1 9.82-11.32z" fill="#1d1d1b"/><path d="m20.55 11.31a22.85 22.85 0 0 1 7.69-2.6c4-.47 10.47 1.32 11.15 1.63s1.25.5 1 .69-2.53 2.18-3.34 2.31-3.62-.56-5.75-.47-3.56.5-4.59.5-2.5-1.13-3.5-1.22-3.13-.59-2.66-.84z" fill="#4eae4d"/><path d="m18.58 12.87a5.82 5.82 0 0 1 4.16.34c1.62.88 1.44 1.25 3.65 1.22s3.29-.4 3.94-.25 3.41 1.35 5.85.88a10.42 10.42 0 0 0 4.28-1.75c.72-.47 1.15-1.25 1.59-1.19s4.41 2.41 4.34 2.66a4.52 4.52 0 0 1-1.71 1.5 7.43 7.43 0 0 0-2.79 3.46c-.5 1.47-.78 5.88-.12 6.32s2.34-.19 3 .31.81 2.06 1.91 2.19 1.56-.69 2.56 0 1 1.21 2.56 1.25 3-.32 3.09 0a2.47 2.47 0 0 1-.12 1.43c-.16.1-5.44.72-6.69.79s-1 .34-1.69 0-1.78-1.63-3.39-1.88-6.53-.56-7.5-.56-1.25 0-1.35.47.1 5.18-.4 6.72-.16 4.06 1.65 4.78 3.69 1.09 3.94 1.75 1.13 5 1.91 6.47 1.87 3.15 1.5 3.46a20.31 20.31 0 0 1-6 1.54 23.64 23.64 0 0 1-5.78 0s-1.16-6-1.47-6.54a4.67 4.67 0 0 1-.41-2.34c.13-.41 2.34-4.87 2.06-6s-.72-2.28-1.75-2.56-2.75 0-5.53 0a27.84 27.84 0 0 1-5.34-.44c-.56-.12-.88 0-1.13-.28s-2.28-4-2-4.34 3.13-1.16 3.25-1.82-.06-2.25.66-2.31 3.87.38 4.87-.15 1.13-1.75 1.16-2.82-.37-3.4-.84-3.84-5-1.81-6.72-2.72-3.17-1.62-2.98-2.22a12.45 12.45 0 0 1 3.78-3.53z" fill="#85bfe9"/><path d="m24.36 17.87a20.8 20.8 0 0 1 7.25.31c3.19.63 3.69 1.16 3.6 1.94s-1.28 4-1.72 3.84a41.78 41.78 0 0 1-5.31-2.18c-.22-.32-.29-1.88-1.22-2.16s-2.88-.88-3.53-1.13-.5-.5-.35-.5 1.28-.12 1.28-.12z" fill="#4eae4d"/><path d="m47.58 15.21c.21-.07 2.94 1.07 4.81 4.63s2.47 7.94 2.25 8.34-.9.44-1.53.25-3.11-1.56-3.65-1.56-1.41.47-1.78 0-1.5-1.87-2.63-1.87-1.37.19-1.56-.06-.81-5.53.37-6.5 2.22-1.59 2.69-2 .75-1.13 1.03-1.23z" fill="#4eae4d"/><path d="m35.71 31c.36 0 5.72-.4 6.78.63s1.94 2.15 2.84 2.12 9.19-.75 9.19-.43-.94 7.5-2.38 11.15a15.91 15.91 0 0 1-5.53 7.06c-1.15.66-2.34.91-2.43.72a21.82 21.82 0 0 1-2.29-5.93c-.68-3.22-.87-4.72-1.93-5s-3.69-.9-4.19-1.53a4 4 0 0 1-.56-1.87s.28-3.88.28-4.72.03-2.2.22-2.2z" fill="#4eae4d"/><path d="m17.43 38.21a12.74 12.74 0 0 0 4.84.91c3.31.06 6.56-.31 6.91.09s.28 1.78-.44 3.1a21.38 21.38 0 0 0-1.19 2.59c-.37-.06-.62.85-.5 1s3.53 2.5 4 2.91a6.06 6.06 0 0 1 .84 2.53c-.09 0-3.9-3.09-4.12-3.13s-.28 1-.28 1 4.5 3.19 4.65 3.44a6.49 6.49 0 0 1 .44 1.88 32.57 32.57 0 0 1-3.59-.91c-1.25-.47-2.35-.72-2.35-.81s-1.17-3.78-2.81-5.38a12.91 12.91 0 0 1-2.36-2.65 31.09 31.09 0 0 1-.35-3.72c-.04-.85-.41-2.88-.22-2.88z" fill="#4eae4d"/><path d="m10.52 38.4c.19-.37 2.56.25 3.69.69s1.5 1 1.53 1.87-.13 4.66.65 5.35a10.71 10.71 0 0 1 3.07 3.28 7.26 7.26 0 0 1 1 2.19 20.15 20.15 0 0 1-5.91-5.5c-3.19-4.13-4.12-7.69-4.03-7.88z" fill="#85bfe9"/><path d="m9.61 36.18a17.66 17.66 0 0 1-.12-9.65c1.37-5.69 4-8.72 4.22-8.69s5.4 3 7.5 4 2.22 1 2.37 1.44a10.13 10.13 0 0 1-.19 3.34c-.18.09-3.93-.09-5 0s-1.39 1.59-1.31 2.19.13.87-.12 1.06-3.6 1.09-3.78 2 2.37 5.37 2 5.5-4.57-.16-5.57-1.19z" fill="#4eae4d"/></svg>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin:0 -1px;opacity:0.35"><path d="M9 12H15" stroke="#e8ddd3" stroke-width="2" stroke-linecap="round"/><path d="M12 9L12 15" stroke="#e8ddd3" stroke-width="2" stroke-linecap="round"/></svg>
          <svg viewBox="0 0 256 256" width="28" height="28" xmlns="http://www.w3.org/2000/svg"><path d="M226.59,71.81A15.92,15.92,0,0,0,217,60.92C183.48,48.05,128,48.41,128,48.41S72.52,48.05,39.04,60.92a15.92,15.92,0,0,0-9.63,10.89C27.07,80.79,24,98.24,24,128s3.07,47.21,5.41,56.19A15.92,15.92,0,0,0,39.04,195.08C72.52,207.95,128,207.59,128,207.59s55.48.35,89-12.51a15.92,15.92,0,0,0,9.63-10.89C228.93,175.21,232,157.76,232,128S228.93,80.79,226.59,71.81ZM112,160V96l48,32Z" fill="#FF0000"/><path d="M164.44,121.34l-48-32A8,8,0,0,0,104,96v64a8,8,0,0,0,12.44,6.66l48-32a8,8,0,0,0,0-13.31Z" fill="white"/></svg>
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
    panelMode = 'lookup';
  }

  function removePanel() {
    const panel = document.getElementById(PANEL_ID);
    if (panel) panel.remove();
    const glow = document.getElementById("scenepoint-page-glow");
    if (glow) glow.remove();
    if (currentAbortController) {
      currentAbortController.abort();
      currentAbortController = null;
    }
    if (progressIntervalId) {
      clearInterval(progressIntervalId);
      progressIntervalId = null;
    }
    progressAborted = true;
    panelMode = 'closed';
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

  // ─── State Machine ───
  // Modes: 'closed' | 'lookup' | 'result' | 'history' | 'history-detail'
  let panelMode = 'closed';
  let progressAborted = false;
  let currentAbortController = null;
  let progressIntervalId = null;

  // ─── Persistence helpers (save to chrome.storage for popup) ───

  async function saveResultToHistory(result) {
    try {
      const data = await chrome.storage.local.get("scenepoint_history");
      const history = data.scenepoint_history || [];

      if (history.some(h => h.id === result.id)) return false;

      const videoId = result.video_id || getVideoId();
      const locParts = [result.location_name, result.region, result.country].filter(Boolean);
      const dedupedLoc = [...new Set(locParts)].join(", ") || "Unknown";

      history.unshift({
        id: result.id,
        videoId: videoId,
        timestamp: result.timestamp_seconds,
        location: dedupedLoc,
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
      return true;
    } catch (e) {
      console.log("[ScenePoint] Could not save history:", e.message);
      return true;
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

  async function submitFeedbackDirect(lookupId, vote, correction) {
    try {
      const body = { lookup_id: lookupId, vote: vote };
      if (correction) body.correct_location = correction;
      await fetch("https://vshnlucky-scenera-api.hf.space/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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
      // Keep adding reassuring messages every 12s
      progressIntervalId = setInterval(() => {
        if (progressAborted) { clearInterval(progressIntervalId); progressIntervalId = null; return; }
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
    if (panelMode !== 'lookup') return;
    panelMode = 'result';
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

    attachFeedbackListeners(area.querySelector(".scenepoint-sp-feedback"));
  }

  function attachFeedbackListeners(container) {
    if (!container) return;
    container.querySelectorAll(".scenepoint-fb-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.dataset.vote === "up") {
          submitFeedbackDirect(btn.dataset.id, "up");
          container.innerHTML = `<span class="scenepoint-fb-thanks">Thanks! Glad it was correct.</span>`;
        } else {
          const lookupId = btn.dataset.id;
          container.innerHTML = `
            <div style="display:flex;gap:8px;align-items:center;width:100%">
              <input type="text" id="scenepoint-correction" placeholder="Share your feedback..." style="flex:1;background:#222;border:1px solid #333;border-radius:6px;padding:8px 12px;color:#e8ddd3;font-size:13px;outline:none"/>
              <button id="scenepoint-submit-correction" style="background:#d4a574;color:#1a1a1a;border:none;border-radius:6px;padding:8px 14px;cursor:pointer;font-size:13px;font-weight:500;white-space:nowrap">Submit</button>
              <button id="scenepoint-cancel-correction" style="background:none;border:none;color:#666;cursor:pointer;font-size:18px;padding:0 4px;line-height:1">✕</button>
            </div>`;
          document.getElementById("scenepoint-submit-correction").addEventListener("click", () => {
            const correction = document.getElementById("scenepoint-correction").value.trim();
            submitFeedbackDirect(lookupId, "down", correction || null);
            container.innerHTML = `<span class="scenepoint-fb-thanks">Thanks! Your feedback helps us improve.</span>`;
          });
          document.getElementById("scenepoint-cancel-correction").addEventListener("click", () => {
            container.innerHTML = `
              <span>Was this correct?</span>
              <button class="scenepoint-fb-btn" data-vote="up" data-id="${lookupId}">👍 Yes</button>
              <button class="scenepoint-fb-btn" data-vote="down" data-id="${lookupId}">👎 No</button>`;
            attachFeedbackListeners(container);
          });
        }
      });
    });
  }

  function showErrorInPanel(message) {
    if (panelMode !== 'lookup') return;
    panelMode = 'result';
    progressAborted = true;
    STEPS.forEach((s) => updateStep(s.id, "error"));
    const area = document.getElementById("scenepoint-result-area");
    if (area) {
      area.innerHTML = `<div class="scenepoint-sp-error">⚠ ${message}</div>`;
    }
  }

  // ─── Main Click Handler ───

  async function onButtonClick() {
    if (panelMode === 'lookup') return;
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

      // Save to local storage for popup history (skip count for cached/duplicate results)
      const isNew = await saveResultToHistory(result);
      if (isNew) await incrementLocalLookupCount();

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
      const loc = item.location || "Unknown";
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
          <svg viewBox="0 0 64 64" width="26" height="26" xmlns="http://www.w3.org/2000/svg"><path d="m18.68 10.74a26.63 26.63 0 0 1 11.25-3.53c4.25-.21 8.15.79 13.56 3.38s8.4 5.06 10.69 9.31 3.53 7.38 2.28 12.91-1.63 11.09-3.85 14.93-5.93 6.5-11.43 7.88-13.32 2.28-20.07-1.44-11.5-9.25-13.25-16.9-.31-11.63 1-15.22a23.64 23.64 0 0 1 9.82-11.32z" fill="#1d1d1b"/><path d="m20.55 11.31a22.85 22.85 0 0 1 7.69-2.6c4-.47 10.47 1.32 11.15 1.63s1.25.5 1 .69-2.53 2.18-3.34 2.31-3.62-.56-5.75-.47-3.56.5-4.59.5-2.5-1.13-3.5-1.22-3.13-.59-2.66-.84z" fill="#4eae4d"/><path d="m18.58 12.87a5.82 5.82 0 0 1 4.16.34c1.62.88 1.44 1.25 3.65 1.22s3.29-.4 3.94-.25 3.41 1.35 5.85.88a10.42 10.42 0 0 0 4.28-1.75c.72-.47 1.15-1.25 1.59-1.19s4.41 2.41 4.34 2.66a4.52 4.52 0 0 1-1.71 1.5 7.43 7.43 0 0 0-2.79 3.46c-.5 1.47-.78 5.88-.12 6.32s2.34-.19 3 .31.81 2.06 1.91 2.19 1.56-.69 2.56 0 1 1.21 2.56 1.25 3-.32 3.09 0a2.47 2.47 0 0 1-.12 1.43c-.16.1-5.44.72-6.69.79s-1 .34-1.69 0-1.78-1.63-3.39-1.88-6.53-.56-7.5-.56-1.25 0-1.35.47.1 5.18-.4 6.72-.16 4.06 1.65 4.78 3.69 1.09 3.94 1.75 1.13 5 1.91 6.47 1.87 3.15 1.5 3.46a20.31 20.31 0 0 1-6 1.54 23.64 23.64 0 0 1-5.78 0s-1.16-6-1.47-6.54a4.67 4.67 0 0 1-.41-2.34c.13-.41 2.34-4.87 2.06-6s-.72-2.28-1.75-2.56-2.75 0-5.53 0a27.84 27.84 0 0 1-5.34-.44c-.56-.12-.88 0-1.13-.28s-2.28-4-2-4.34 3.13-1.16 3.25-1.82-.06-2.25.66-2.31 3.87.38 4.87-.15 1.13-1.75 1.16-2.82-.37-3.4-.84-3.84-5-1.81-6.72-2.72-3.17-1.62-2.98-2.22a12.45 12.45 0 0 1 3.78-3.53z" fill="#85bfe9"/><path d="m24.36 17.87a20.8 20.8 0 0 1 7.25.31c3.19.63 3.69 1.16 3.6 1.94s-1.28 4-1.72 3.84a41.78 41.78 0 0 1-5.31-2.18c-.22-.32-.29-1.88-1.22-2.16s-2.88-.88-3.53-1.13-.5-.5-.35-.5 1.28-.12 1.28-.12z" fill="#4eae4d"/><path d="m47.58 15.21c.21-.07 2.94 1.07 4.81 4.63s2.47 7.94 2.25 8.34-.9.44-1.53.25-3.11-1.56-3.65-1.56-1.41.47-1.78 0-1.5-1.87-2.63-1.87-1.37.19-1.56-.06-.81-5.53.37-6.5 2.22-1.59 2.69-2 .75-1.13 1.03-1.23z" fill="#4eae4d"/><path d="m35.71 31c.36 0 5.72-.4 6.78.63s1.94 2.15 2.84 2.12 9.19-.75 9.19-.43-.94 7.5-2.38 11.15a15.91 15.91 0 0 1-5.53 7.06c-1.15.66-2.34.91-2.43.72a21.82 21.82 0 0 1-2.29-5.93c-.68-3.22-.87-4.72-1.93-5s-3.69-.9-4.19-1.53a4 4 0 0 1-.56-1.87s.28-3.88.28-4.72.03-2.2.22-2.2z" fill="#4eae4d"/><path d="m17.43 38.21a12.74 12.74 0 0 0 4.84.91c3.31.06 6.56-.31 6.91.09s.28 1.78-.44 3.1a21.38 21.38 0 0 0-1.19 2.59c-.37-.06-.62.85-.5 1s3.53 2.5 4 2.91a6.06 6.06 0 0 1 .84 2.53c-.09 0-3.9-3.09-4.12-3.13s-.28 1-.28 1 4.5 3.19 4.65 3.44a6.49 6.49 0 0 1 .44 1.88 32.57 32.57 0 0 1-3.59-.91c-1.25-.47-2.35-.72-2.35-.81s-1.17-3.78-2.81-5.38a12.91 12.91 0 0 1-2.36-2.65 31.09 31.09 0 0 1-.35-3.72c-.04-.85-.41-2.88-.22-2.88z" fill="#4eae4d"/><path d="m10.52 38.4c.19-.37 2.56.25 3.69.69s1.5 1 1.53 1.87-.13 4.66.65 5.35a10.71 10.71 0 0 1 3.07 3.28 7.26 7.26 0 0 1 1 2.19 20.15 20.15 0 0 1-5.91-5.5c-3.19-4.13-4.12-7.69-4.03-7.88z" fill="#85bfe9"/><path d="m9.61 36.18a17.66 17.66 0 0 1-.12-9.65c1.37-5.69 4-8.72 4.22-8.69s5.4 3 7.5 4 2.22 1 2.37 1.44a10.13 10.13 0 0 1-.19 3.34c-.18.09-3.93-.09-5 0s-1.39 1.59-1.31 2.19.13.87-.12 1.06-3.6 1.09-3.78 2 2.37 5.37 2 5.5-4.57-.16-5.57-1.19z" fill="#4eae4d"/></svg>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin:0 -1px;opacity:0.35"><path d="M9 12H15" stroke="#e8ddd3" stroke-width="2" stroke-linecap="round"/><path d="M12 9L12 15" stroke="#e8ddd3" stroke-width="2" stroke-linecap="round"/></svg>
          <svg viewBox="0 0 256 256" width="28" height="28" xmlns="http://www.w3.org/2000/svg"><path d="M226.59,71.81A15.92,15.92,0,0,0,217,60.92C183.48,48.05,128,48.41,128,48.41S72.52,48.05,39.04,60.92a15.92,15.92,0,0,0-9.63,10.89C27.07,80.79,24,98.24,24,128s3.07,47.21,5.41,56.19A15.92,15.92,0,0,0,39.04,195.08C72.52,207.95,128,207.59,128,207.59s55.48.35,89-12.51a15.92,15.92,0,0,0,9.63-10.89C228.93,175.21,232,157.76,232,128S228.93,80.79,226.59,71.81ZM112,160V96l48,32Z" fill="#FF0000"/><path d="M164.44,121.34l-48-32A8,8,0,0,0,104,96v64a8,8,0,0,0,12.44,6.66l48-32a8,8,0,0,0,0-13.31Z" fill="white"/></svg>
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
    panelMode = 'history';
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
    panelMode = 'history-detail';
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

    const searchBox = panel.querySelector(".scenepoint-search-box");
    const contentArea = panel.querySelector(".scenepoint-history-title");
    const listArea = panel.querySelector(".scenepoint-history-list");

    if (searchBox) searchBox.remove();
    if (contentArea) contentArea.remove();
    if (listArea) {
      listArea.innerHTML = `
        <div class="scenepoint-detail-view">
          <button class="scenepoint-back-btn" id="scenepoint-back"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#d4a574" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px"><polyline points="15 18 9 12 15 6"/></svg>Back</button>

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
      if (panelMode === 'closed') {
        openHistoryPanel();
      } else {
        removePanel();
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
    setTimeout(injectButton, 1000);
  });

  // Initial inject
  if (document.readyState === "complete") {
    init();
  } else {
    window.addEventListener("load", init);
  }
})();
