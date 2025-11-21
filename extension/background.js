// Background service worker for Visual AI Assistant
const API_BASE_URL = 'http://localhost:8000';

// State
let backendHealthy = false;

// Check backend health periodically
async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.ok) {
      backendHealthy = true;
      // Update icon to show connected state
      chrome.action.setIcon({
        path: {
          "16": "icons/icon16.png",
          "48": "icons/icon48.png",
          "128": "icons/icon128.png"
        }
      });
      chrome.action.setBadgeText({ text: '' });
    } else {
      setDisconnected();
    }
  } catch (error) {
    setDisconnected();
  }
}

function setDisconnected() {
  backendHealthy = false;
  // Could set a different icon or badge to show disconnected state
  chrome.action.setBadgeText({ text: '!' });
  chrome.action.setBadgeBackgroundColor({ color: '#ff4444' });
}

// Initialize health check on install
chrome.runtime.onInstalled.addListener(() => {
  console.log('Visual AI Assistant installed');
  checkBackendHealth();
});

// Start periodic health checks (every 30 seconds)
setInterval(checkBackendHealth, 30000);

// Initial health check
checkBackendHealth();

// Message handler for communication with content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkHealth') {
    checkBackendHealth().then(() => {
      sendResponse({ healthy: backendHealthy });
    });
    return true; // Keep channel open for async response
  }

  if (request.action === 'captureScreen') {
    // Capture visible tab screenshot
    chrome.tabs.captureVisibleTab(null, { format: 'png' }, (dataUrl) => {
      if (chrome.runtime.lastError) {
        sendResponse({ error: chrome.runtime.lastError.message });
      } else {
        sendResponse({ dataUrl: dataUrl });
      }
    });
    return true; // Keep channel open for async response
  }

  if (request.action === 'analyzeImage') {
    // Forward analysis request to backend
    fetch(`${API_BASE_URL}/api/analyze/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request.data),
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data: data }))
      .catch(error => sendResponse({ success: false, error: error.message }));

    return true; // Keep channel open for async response
  }

  if (request.action === 'fillFields') {
    // Send message to content script to fill fields
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, {
          action: 'fillFields',
          fields: request.fields
        }, (response) => {
          sendResponse(response);
        });
      }
    });
    return true;
  }
});

// Handle extension icon click (optional custom behavior)
chrome.action.onClicked.addListener((tab) => {
  // Default behavior is to open popup, so this is optional
  console.log('Extension icon clicked on tab:', tab.id);
});

// Log backend status changes
let lastHealthStatus = null;
setInterval(() => {
  if (lastHealthStatus !== backendHealthy) {
    console.log(`Backend status changed: ${backendHealthy ? 'Connected' : 'Disconnected'}`);
    lastHealthStatus = backendHealthy;
  }
}, 5000);
