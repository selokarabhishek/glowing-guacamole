// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentAnalysis = null;
let currentUrl = null;
let backendStatus = 'disconnected';

// DOM Elements
const statusEl = document.getElementById('status');
const providerSelectEl = document.getElementById('provider-select');
const promptEl = document.getElementById('prompt');
const analyzeBtn = document.getElementById('analyze-btn');
const extractBtn = document.getElementById('extract-btn');
const useMemoryEl = document.getElementById('use-memory');
const loadingEl = document.getElementById('loading');
const resultsEl = document.getElementById('results');
const closeResultsBtn = document.getElementById('close-results');
const analysisContentEl = document.getElementById('analysis-content');
const fieldsSectionEl = document.getElementById('fields-section');
const fieldsListEl = document.getElementById('fields-list');
const saveMemoryBtn = document.getElementById('save-memory-btn');
const metadataEl = document.getElementById('metadata');
const memoryStatsEl = document.getElementById('memory-stats');
const clearMemoryBtn = document.getElementById('clear-memory-btn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await checkBackendHealth();
  await loadProviders();
  await loadMemoryStats();
  await loadCurrentUrl();
  loadSavedProvider();

  // Set up event listeners
  analyzeBtn.addEventListener('click', () => analyzeCurrentPage());
  extractBtn.addEventListener('click', () => extractFormFields());
  closeResultsBtn.addEventListener('click', hideResults);
  saveMemoryBtn.addEventListener('click', saveToMemory);
  clearMemoryBtn.addEventListener('click', clearMemory);
  providerSelectEl.addEventListener('change', saveSelectedProvider);
});

// Check backend health
async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      backendStatus = 'connected';
      statusEl.textContent = 'Connected';
      statusEl.classList.remove('disconnected');
      statusEl.classList.add('connected');
    } else {
      setDisconnected();
    }
  } catch (error) {
    setDisconnected();
  }
}

function setDisconnected() {
  backendStatus = 'disconnected';
  statusEl.textContent = 'Disconnected';
  statusEl.classList.remove('connected');
  statusEl.classList.add('disconnected');
}

// Load available providers
async function loadProviders() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/settings/providers`);
    if (!response.ok) throw new Error('Failed to load providers');

    const providers = await response.json();
    providerSelectEl.innerHTML = '';

    for (const [name, info] of Object.entries(providers)) {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = `${name.charAt(0).toUpperCase() + name.slice(1)} ${info.available ? '✓' : '✗'}`;
      option.disabled = !info.available;
      providerSelectEl.appendChild(option);
    }
  } catch (error) {
    console.error('Failed to load providers:', error);
    providerSelectEl.innerHTML = '<option>Error loading providers</option>';
  }
}

// Load memory statistics
async function loadMemoryStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/memory/stats`);
    if (!response.ok) throw new Error('Failed to load memory stats');

    const stats = await response.json();
    memoryStatsEl.textContent = `Memory: ${stats.total_entries} entries`;
  } catch (error) {
    console.error('Failed to load memory stats:', error);
  }
}

// Load current URL
async function loadCurrentUrl() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentUrl = tab.url;
  } catch (error) {
    console.error('Failed to get current URL:', error);
  }
}

// Save/Load provider preference
function saveSelectedProvider() {
  chrome.storage.local.set({ selectedProvider: providerSelectEl.value });
}

function loadSavedProvider() {
  chrome.storage.local.get(['selectedProvider'], (result) => {
    if (result.selectedProvider) {
      providerSelectEl.value = result.selectedProvider;
    }
  });
}

// Check if page is sensitive
function isSensitivePage(url) {
  const sensitivePatterns = [
    /banking|bank|chase|wellsfargo|bofa|citibank/i,
    /paypal|venmo|cashapp|stripe|square/i,
    /login|signin|password|auth|sso/i,
    /checkout|payment|credit-card|billing/i,
    /medical|health|patient|prescription/i,
    /ssn|tax|irs|w2|w9|legal/i,
    /mail\.google|outlook|yahoo\.mail|proton/i,
  ];

  return sensitivePatterns.some(pattern => pattern.test(url));
}

// Capture screenshot
async function captureScreenshot() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const dataUrl = await chrome.tabs.captureVisibleTab(null, {
      format: 'png',
      quality: 90
    });

    // Extract base64 data
    const base64Data = dataUrl.split(',')[1];
    return base64Data;
  } catch (error) {
    console.error('Screenshot capture failed:', error);
    throw new Error('Failed to capture screenshot. Make sure you have an active tab.');
  }
}

// Analyze current page
async function analyzeCurrentPage() {
  if (backendStatus !== 'connected') {
    alert('Backend is not connected. Please start the backend server.');
    return;
  }

  // Security check: Warn about sensitive pages
  if (isSensitivePage(currentUrl)) {
    const provider = providerSelectEl.value || 'cloud provider';
    const warningMessage = `⚠️ SECURITY WARNING\n\n` +
      `This page may contain sensitive information (login, banking, payment, etc.).\n\n` +
      `Screenshots will be:\n` +
      `• Sent to ${provider === 'ollama' ? 'your local Ollama server' : provider + ' cloud service'}\n` +
      `• May be logged by the AI provider\n` +
      `${useMemoryEl.checked ? '• Stored in local memory database\n' : ''}` +
      `\nRECOMMENDATIONS:\n` +
      `• Use Ollama (local) for sensitive pages\n` +
      `• Disable "Use memory context" below\n` +
      `• Avoid pages with visible passwords\n\n` +
      `Continue analysis anyway?`;

    if (!confirm(warningMessage)) {
      return;
    }
  }

  const prompt = promptEl.value.trim() || 'Analyze this page and identify all form fields with their details.';

  try {
    showLoading();
    hideResults();

    // Capture screenshot
    const imageBase64 = await captureScreenshot();

    // Get selected provider
    const provider = providerSelectEl.value || null;
    const useMemory = useMemoryEl.checked;

    // Send analysis request
    const response = await fetch(`${API_BASE_URL}/api/analyze/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_base64: imageBase64,
        prompt: prompt,
        url: currentUrl,
        use_memory: useMemory,
        provider: provider
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Analysis failed');
    }

    const result = await response.json();
    currentAnalysis = result;

    displayResults(result);
    hideLoading();

  } catch (error) {
    hideLoading();
    alert(`Error: ${error.message}`);
    console.error('Analysis error:', error);
  }
}

// Extract form fields only
async function extractFormFields() {
  if (backendStatus !== 'connected') {
    alert('Backend is not connected. Please start the backend server.');
    return;
  }

  try {
    showLoading();
    hideResults();

    // Capture screenshot
    const imageBase64 = await captureScreenshot();

    // Get selected provider
    const provider = providerSelectEl.value || null;

    // Send extraction request
    const response = await fetch(`${API_BASE_URL}/api/analyze/extract-fields`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_base64: imageBase64,
        prompt: 'Extract form fields',
        url: currentUrl,
        use_memory: false,
        provider: provider
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Extraction failed');
    }

    const fields = await response.json();

    // Display as simplified result
    displayResults({
      analysis: `Found ${fields.length} form fields on this page.`,
      form_fields: fields,
      provider: provider || 'default',
      model: 'N/A',
      tokens_used: null,
      memory_context_used: false
    });

    hideLoading();

  } catch (error) {
    hideLoading();
    alert(`Error: ${error.message}`);
    console.error('Extraction error:', error);
  }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Display results
function displayResults(result) {
  // Show analysis (safe - using textContent)
  analysisContentEl.textContent = result.analysis;

  // Show form fields if any (with XSS protection)
  if (result.form_fields && result.form_fields.length > 0) {
    fieldsListEl.innerHTML = '';
    result.form_fields.forEach(field => {
      const fieldEl = document.createElement('div');
      fieldEl.className = 'field-item';

      // Create label element safely
      const labelEl = document.createElement('strong');
      labelEl.textContent = field.label;

      // Create meta element safely
      const metaEl = document.createElement('div');
      metaEl.className = 'field-meta';
      metaEl.textContent = `Type: ${field.field_type} | Selector: ${field.selector} | Required: ${field.required ? 'Yes' : 'No'}`;

      if (field.suggested_value) {
        metaEl.textContent += ` | Suggested: ${field.suggested_value}`;
      }

      fieldEl.appendChild(labelEl);
      fieldEl.appendChild(metaEl);
      fieldsListEl.appendChild(fieldEl);
    });
    fieldsSectionEl.classList.remove('hidden');
  } else {
    fieldsSectionEl.classList.add('hidden');
  }

  // Show metadata (safe - using textContent)
  metadataEl.textContent = `Provider: ${result.provider} | Model: ${result.model} | ${result.tokens_used ? `Tokens: ${result.tokens_used}` : ''} | Memory used: ${result.memory_context_used ? 'Yes' : 'No'}`;

  resultsEl.classList.remove('hidden');
}

// Hide results
function hideResults() {
  resultsEl.classList.add('hidden');
}

// Show/Hide loading
function showLoading() {
  loadingEl.classList.remove('hidden');
  analyzeBtn.disabled = true;
  extractBtn.disabled = true;
}

function hideLoading() {
  loadingEl.classList.add('hidden');
  analyzeBtn.disabled = false;
  extractBtn.disabled = false;
}

// Save to memory
async function saveToMemory() {
  if (!currentAnalysis) {
    alert('No analysis to save');
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/memory/store`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: currentUrl,
        analysis: currentAnalysis.analysis,
        instruction: promptEl.value.trim() || 'Analyze page',
        metadata: {
          provider: currentAnalysis.provider,
          model: currentAnalysis.model,
          timestamp: new Date().toISOString()
        }
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to save to memory');
    }

    alert('Saved to memory successfully!');
    await loadMemoryStats();

  } catch (error) {
    alert(`Error saving to memory: ${error.message}`);
    console.error('Save error:', error);
  }
}

// Clear memory
async function clearMemory() {
  if (!confirm('Are you sure you want to clear all memory? This cannot be undone.')) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/memory/clear`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to clear memory');
    }

    alert('Memory cleared successfully!');
    await loadMemoryStats();

  } catch (error) {
    alert(`Error clearing memory: ${error.message}`);
    console.error('Clear error:', error);
  }
}
