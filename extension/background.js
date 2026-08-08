// Scenera — Background Service Worker
// Handles extension icon click → tells content script to toggle the side panel

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.url || !tab.url.includes("youtube.com")) {
    // Not on YouTube — nothing to do
    return;
  }

  try {
    await chrome.tabs.sendMessage(tab.id, { type: "TOGGLE_PANEL" });
  } catch (e) {
    // Content script not loaded yet — inject it
    console.log("Content script not ready, injecting...");
  }
});
