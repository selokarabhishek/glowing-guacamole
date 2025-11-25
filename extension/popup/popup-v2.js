// ========================================
// CONFIGURATION
// ========================================

const API_BASE_URL = 'http://localhost:8000';
const STORAGE_KEYS = {
  TIME_SAVED: 'totalTimeSaved',
  FORMS_FILLED: 'totalFormsFilled',
  LAST_RESET: 'lastWeekReset',
  TEMPLATES: 'formTemplates',
  ONBOARDING: 'onboardingComplete'
};

// ========================================
// STATE
// ========================================

const state = {
  connected: false,
  currentUrl: null,
  detectedFields: [],
  formType: 'Unknown Form',
  timeSaved: 0,
  formsFilled: 0,
  isFirstUse: false
};

// ========================================
// DOM ELEMENTS
// ========================================

const elements = {
  // States
  welcomeState: document.getElementById('welcome-state'),
  formDetectedState: document.getElementById('form-detected-state'),
  noFormsState: document.getElementById('no-forms-state'),
  loadingOverlay: document.getElementById('loading-overlay'),

  // Header
  statusIndicator: document.getElementById('status-indicator'),
  statusText: document.getElementById('status-text'),
  timeSavedBadge: document.getElementById('time-saved-badge'),
  timeSaved: document.getElementById('time-saved'),

  // Form detected
  formType: document.getElementById('form-type'),
  fieldCount: document.getElementById('field-count'),
  fieldsPreview: document.getElementById('fields-preview'),
  autoFillBtn: document.getElementById('auto-fill-btn'),
  customizeBtn: document.getElementById('customize-btn'),

  // Actions
  saveTemplateBtn: document.getElementById('save-template-btn'),
  learnMoreBtn: document.getElementById('learn-more-btn'),
  analyzeAnywayBtn: document.getElementById('analyze-anyway-btn'),

  // Loading
  loadingText: document.getElementById('loading-text')
};

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
  await initialize();
  setupEventListeners();
  setupKeyboardShortcuts();
});

async function initialize() {
  // Load stats
  await loadStats();

  // Check backend health
  await checkBackendHealth();

  // Get current tab URL
  await loadCurrentUrl();

  // Check if first use
  const result = await chrome.storage.local.get([STORAGE_KEYS.ONBOARDING]);
  state.isFirstUse = !result[STORAGE_KEYS.ONBOARDING];

  // Show appropriate state
  if (state.isFirstUse) {
    showWelcomeState();
  } else {
    // Auto-detect forms
    await detectForms();
  }
}

// ========================================
// BACKEND CONNECTION
// ========================================

async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.ok) {
      state.connected = true;
      updateConnectionStatus(true);
    } else {
      updateConnectionStatus(false);
    }
  } catch (error) {
    console.error('Backend connection failed:', error);
    updateConnectionStatus(false);
  }
}

function updateConnectionStatus(connected) {
  state.connected = connected;

  if (connected) {
    elements.statusIndicator.classList.add('connected');
    elements.statusText.textContent = 'Connected';
  } else {
    elements.statusIndicator.classList.remove('connected');
    elements.statusText.textContent = 'Offline';
  }
}

// ========================================
// STATS & METRICS
// ========================================

async function loadStats() {
  const result = await chrome.storage.local.get([
    STORAGE_KEYS.TIME_SAVED,
    STORAGE_KEYS.FORMS_FILLED,
    STORAGE_KEYS.LAST_RESET
  ]);

  // Check if we need to reset weekly stats
  const lastReset = result[STORAGE_KEYS.LAST_RESET] || 0;
  const now = Date.now();
  const weekInMs = 7 * 24 * 60 * 60 * 1000;

  if (now - lastReset > weekInMs) {
    // Reset weekly stats
    state.timeSaved = 0;
    state.formsFilled = 0;
    await chrome.storage.local.set({
      [STORAGE_KEYS.TIME_SAVED]: 0,
      [STORAGE_KEYS.FORMS_FILLED]: 0,
      [STORAGE_KEYS.LAST_RESET]: now
    });
  } else {
    state.timeSaved = result[STORAGE_KEYS.TIME_SAVED] || 0;
    state.formsFilled = result[STORAGE_KEYS.FORMS_FILLED] || 0;
  }

  updateStatsDisplay();
}

function updateStatsDisplay() {
  if (state.timeSaved > 0) {
    const hours = (state.timeSaved / 3600).toFixed(1);
    elements.timeSaved.textContent = `${hours} hours`;
    elements.timeSavedBadge.classList.remove('hidden');
  } else {
    elements.timeSavedBadge.classList.add('hidden');
  }
}

async function incrementStats(timeSeconds) {
  state.timeSaved += timeSeconds;
  state.formsFilled += 1;

  await chrome.storage.local.set({
    [STORAGE_KEYS.TIME_SAVED]: state.timeSaved,
    [STORAGE_KEYS.FORMS_FILLED]: state.formsFilled
  });

  updateStatsDisplay();
}

// ========================================
// FORM DETECTION
// ========================================

async function loadCurrentUrl() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    state.currentUrl = tab.url;
  } catch (error) {
    console.error('Failed to get current URL:', error);
  }
}

async function detectForms() {
  if (!state.connected) {
    showNoFormsState('Backend is offline. Please start the server.');
    return;
  }

  // Check for sensitive pages
  if (isSensitivePage(state.currentUrl)) {
    const proceed = confirm(
      '⚠️ SECURITY WARNING\n\n' +
      'This page may contain sensitive information.\n\n' +
      'Consider using local Ollama provider for privacy.\n\n' +
      'Continue anyway?'
    );

    if (!proceed) {
      showNoFormsState('Analysis cancelled for security');
      return;
    }
  }

  showLoading('Detecting forms...');

  try {
    // Capture screenshot
    const imageBase64 = await captureScreenshot();

    // Analyze with backend
    const response = await fetch(`${API_BASE_URL}/api/analyze/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: imageBase64,
        prompt: 'Detect and extract all form fields on this page. For each field, provide the type, label, CSS selector, and whether it is required.',
        url: state.currentUrl,
        use_memory: true,
        provider: null // Use default
      })
    });

    if (!response.ok) {
      throw new Error('Analysis failed');
    }

    const result = await response.json();

    hideLoading();

    // Check if forms were detected
    if (result.form_fields && result.form_fields.length > 0) {
      state.detectedFields = result.form_fields;
      state.formType = guessFormType(result.analysis, result.form_fields);
      showFormDetectedState();
    } else {
      showNoFormsState('No forms detected on this page');
    }

    // Mark onboarding as complete
    if (state.isFirstUse) {
      await chrome.storage.local.set({ [STORAGE_KEYS.ONBOARDING]: true });
      state.isFirstUse = false;
    }

  } catch (error) {
    hideLoading();
    console.error('Form detection failed:', error);
    showNoFormsState(`Error: ${error.message}`);
  }
}

async function captureScreenshot() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const dataUrl = await chrome.tabs.captureVisibleTab(null, {
    format: 'png',
    quality: 90
  });
  return dataUrl.split(',')[1];
}

function guessFormType(analysis, fields) {
  const analysisLower = analysis.toLowerCase();
  const fieldLabels = fields.map(f => f.label.toLowerCase()).join(' ');

  const combined = analysisLower + ' ' + fieldLabels;

  if (combined.includes('login') || combined.includes('sign in')) return 'Login Form';
  if (combined.includes('register') || combined.includes('sign up')) return 'Registration Form';
  if (combined.includes('contact')) return 'Contact Form';
  if (combined.includes('job') || combined.includes('application')) return 'Job Application';
  if (combined.includes('checkout') || combined.includes('payment')) return 'Checkout Form';
  if (combined.includes('shipping') || combined.includes('address')) return 'Shipping Form';
  if (combined.includes('profile')) return 'Profile Form';

  return `Form (${fields.length} fields)`;
}

function isSensitivePage(url) {
  const sensitivePatterns = [
    /banking|bank|chase|wellsfargo|bofa/i,
    /paypal|venmo|cashapp/i,
    /login|signin|password|auth/i,
    /checkout|payment|credit-card/i,
    /medical|health/i,
    /ssn|tax|irs/i
  ];

  return sensitivePatterns.some(pattern => pattern.test(url));
}

// ========================================
// AUTO-FILL
// ========================================

async function autoFillForm() {
  if (state.detectedFields.length === 0) {
    alert('No fields to fill');
    return;
  }

  showLoading('Filling form...');

  try {
    // Get values from memory/templates
    const fieldsWithValues = await enhanceFieldsWithValues(state.detectedFields);

    // Send to content script to fill
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    await chrome.tabs.sendMessage(tab.id, {
      action: 'fillFields',
      fields: fieldsWithValues
    });

    hideLoading();

    // Estimate time saved (assume 5 seconds per field manually)
    const timeSaved = state.detectedFields.length * 5;
    await incrementStats(timeSaved);

    // Show success
    alert(`✅ Form filled successfully!\n\nSaved ${timeSaved} seconds`);

  } catch (error) {
    hideLoading();
    console.error('Auto-fill failed:', error);
    alert(`Error filling form: ${error.message}`);
  }
}

async function enhanceFieldsWithValues(fields) {
  // For now, return fields as-is with suggested values
  // Future: Pull from templates or memory
  return fields.map(field => ({
    ...field,
    value: field.suggested_value || ''
  }));
}

// ========================================
// UI STATE MANAGEMENT
// ========================================

function showWelcomeState() {
  hideAllStates();
  elements.welcomeState.classList.remove('hidden');
}

function showFormDetectedState() {
  hideAllStates();

  // Update UI
  elements.formType.textContent = state.formType;
  elements.fieldCount.textContent = `${state.detectedFields.length} fields detected`;

  // Render field previews
  renderFieldPreviews();

  elements.formDetectedState.classList.remove('hidden');
}

function showNoFormsState(message = 'No forms detected') {
  hideAllStates();
  elements.noFormsState.classList.remove('hidden');
  elements.noFormsState.querySelector('.hero-subtitle').textContent = message;
}

function hideAllStates() {
  elements.welcomeState.classList.add('hidden');
  elements.formDetectedState.classList.add('hidden');
  elements.noFormsState.classList.add('hidden');
}

function showLoading(message = 'Loading...') {
  elements.loadingText.textContent = message;
  elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
  elements.loadingOverlay.classList.add('hidden');
}

function renderFieldPreviews() {
  elements.fieldsPreview.innerHTML = '';

  // Show max 5 fields in preview
  const previewFields = state.detectedFields.slice(0, 5);

  previewFields.forEach(field => {
    const fieldEl = document.createElement('div');
    fieldEl.className = 'field-preview';

    const fieldInfo = document.createElement('div');
    fieldInfo.className = 'field-info';

    const label = document.createElement('div');
    label.className = 'field-label';
    label.textContent = field.label;

    const value = document.createElement('div');
    value.className = 'field-value';
    value.textContent = field.suggested_value || `(${field.field_type})`;

    fieldInfo.appendChild(label);
    fieldInfo.appendChild(value);

    const source = document.createElement('div');
    source.className = 'field-source';
    source.textContent = field.suggested_value ? 'From memory' : 'Empty';

    fieldEl.appendChild(fieldInfo);
    fieldEl.appendChild(source);

    elements.fieldsPreview.appendChild(fieldEl);
  });

  // Show "X more fields" if needed
  if (state.detectedFields.length > 5) {
    const moreEl = document.createElement('div');
    moreEl.style.textAlign = 'center';
    moreEl.style.padding = '8px';
    moreEl.style.fontSize = '12px';
    moreEl.style.color = 'var(--color-text-tertiary)';
    moreEl.textContent = `+ ${state.detectedFields.length - 5} more fields`;
    elements.fieldsPreview.appendChild(moreEl);
  }
}

// ========================================
// EVENT LISTENERS
// ========================================

function setupEventListeners() {
  // Auto-fill button
  elements.autoFillBtn?.addEventListener('click', autoFillForm);

  // Detect forms (welcome state)
  const detectBtn = elements.welcomeState?.querySelector('.btn-primary');
  detectBtn?.addEventListener('click', detectForms);

  // Analyze anyway
  elements.analyzeAnywayBtn?.addEventListener('click', detectForms);

  // Footer links
  elements.templatesLink?.addEventListener('click', (e) => {
    e.preventDefault();
    alert('Templates coming soon!');
  });

  elements.settingsLink?.addEventListener('click', (e) => {
    e.preventDefault();
    alert('Settings coming soon!');
  });

  elements.upgradeLink?.addEventListener('click', (e) => {
    e.preventDefault();
    showPricingInfo();
  });
}

// ========================================
// KEYBOARD SHORTCUTS
// ========================================

function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Cmd/Ctrl + Shift + F: Detect forms
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'F') {
      e.preventDefault();
      detectForms();
    }

    // Cmd/Ctrl + Enter: Auto-fill
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      if (state.detectedFields.length > 0) {
        autoFillForm();
      }
    }

    // Cmd/Ctrl + /: Help
    if ((e.metaKey || e.ctrlKey) && e.key === '/') {
      e.preventDefault();
      showHelp();
    }
  });
}

// ========================================
// HELPERS
// ========================================

function showPricingInfo() {
  const message = `
FormFill AI Pricing

FREE
• 10 forms/month
• Basic auto-fill
• Form detection

PRO - $20/month
• Unlimited forms
• Smart templates
• Priority support
• Memory learning

TEAM - $50/user/month
• Everything in Pro
• Team templates
• Analytics
• SSO/SAML

Want to upgrade?
`.trim();

  alert(message);
}

function showHelp() {
  const message = `
Keyboard Shortcuts

⌘⇧F   Detect forms
⌘↵    Auto-fill form
⌘/    Show this help

Need more help?
Visit: formfill.ai/help
`.trim();

  alert(message);
}
