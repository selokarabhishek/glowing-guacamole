// Content script for Visual AI Assistant
// Handles form detection and field filling on web pages

console.log('Visual AI Assistant content script loaded');

// Listen for messages from background or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'fillFields') {
    fillFields(request.fields)
      .then(result => sendResponse({ success: true, result: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }

  if (request.action === 'detectFields') {
    const fields = detectFormFields();
    sendResponse({ success: true, fields: fields });
    return true;
  }

  if (request.action === 'highlightField') {
    highlightField(request.selector);
    sendResponse({ success: true });
    return true;
  }
});

/**
 * Detect all form fields on the page
 * @returns {Array} Array of detected field objects
 */
function detectFormFields() {
  const fields = [];
  const inputs = document.querySelectorAll('input, textarea, select');

  inputs.forEach((input, index) => {
    // Skip hidden, submit, and button inputs
    if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') {
      return;
    }

    // Try to find label
    let label = '';
    if (input.id) {
      const labelEl = document.querySelector(`label[for="${input.id}"]`);
      if (labelEl) {
        label = labelEl.textContent.trim();
      }
    }

    // Fallback: check for nearby label
    if (!label) {
      const parent = input.closest('label');
      if (parent) {
        label = parent.textContent.replace(input.value, '').trim();
      }
    }

    // Fallback: use placeholder or name
    if (!label) {
      label = input.placeholder || input.name || `Field ${index + 1}`;
    }

    // Build selector
    let selector = '';
    if (input.id) {
      selector = `#${input.id}`;
    } else if (input.name) {
      selector = `[name="${input.name}"]`;
    } else {
      // Generate a unique selector
      selector = generateUniqueSelector(input);
    }

    fields.push({
      field_type: input.type || input.tagName.toLowerCase(),
      label: label,
      selector: selector,
      required: input.required || false,
      placeholder: input.placeholder || null,
      current_value: input.value || null
    });
  });

  return fields;
}

/**
 * Generate a unique CSS selector for an element
 * @param {Element} element - The element to generate selector for
 * @returns {string} CSS selector
 */
function generateUniqueSelector(element) {
  if (element.id) {
    return `#${element.id}`;
  }

  const path = [];
  let current = element;

  while (current && current.nodeType === Node.ELEMENT_NODE) {
    let selector = current.nodeName.toLowerCase();

    if (current.className) {
      const classes = current.className.trim().split(/\s+/).filter(c => c);
      if (classes.length > 0) {
        selector += '.' + classes.join('.');
      }
    }

    // Add nth-child if needed for uniqueness
    const parent = current.parentNode;
    if (parent) {
      const siblings = Array.from(parent.children).filter(
        el => el.nodeName === current.nodeName
      );
      if (siblings.length > 1) {
        const index = siblings.indexOf(current) + 1;
        selector += `:nth-child(${index})`;
      }
    }

    path.unshift(selector);

    // Stop at form or body
    if (current.nodeName === 'FORM' || current.nodeName === 'BODY') {
      break;
    }

    current = current.parentNode;
  }

  return path.join(' > ');
}

/**
 * Fill form fields with provided data
 * React-compatible value setting
 * @param {Array} fields - Array of field objects with selector and value
 * @returns {Promise} Promise that resolves when all fields are filled
 */
async function fillFields(fields) {
  const results = [];

  for (const field of fields) {
    try {
      const element = document.querySelector(field.selector);

      if (!element) {
        results.push({
          selector: field.selector,
          success: false,
          error: 'Element not found'
        });
        continue;
      }

      // Set value using React-compatible method
      const success = setReactValue(element, field.suggested_value || field.value);

      results.push({
        selector: field.selector,
        success: success,
        value: field.suggested_value || field.value
      });

      // Optional: highlight filled field briefly
      highlightField(field.selector, 1000);

    } catch (error) {
      results.push({
        selector: field.selector,
        success: false,
        error: error.message
      });
    }
  }

  return results;
}

/**
 * Set input value in a React-compatible way
 * @param {Element} element - The input element
 * @param {string} value - The value to set
 * @returns {boolean} Success status
 */
function setReactValue(element, value) {
  try {
    // Get the native setter
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      'value'
    )?.set;

    const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype,
      'value'
    )?.set;

    // Use native setter
    if (element.tagName === 'TEXTAREA' && nativeTextAreaValueSetter) {
      nativeTextAreaValueSetter.call(element, value);
    } else if (nativeInputValueSetter) {
      nativeInputValueSetter.call(element, value);
    } else {
      element.value = value;
    }

    // Dispatch events for React and other frameworks
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));

    return true;
  } catch (error) {
    console.error('Failed to set value:', error);
    return false;
  }
}

/**
 * Highlight a field temporarily
 * @param {string} selector - CSS selector for the field
 * @param {number} duration - Duration in milliseconds
 */
function highlightField(selector, duration = 2000) {
  const element = document.querySelector(selector);
  if (!element) return;

  const originalOutline = element.style.outline;
  const originalTransition = element.style.transition;

  element.style.transition = 'outline 0.3s';
  element.style.outline = '3px solid #667eea';

  setTimeout(() => {
    element.style.transition = originalTransition;
    element.style.outline = originalOutline;
  }, duration);
}

/**
 * Scroll element into view smoothly
 * @param {string} selector - CSS selector for the element
 */
function scrollToField(selector) {
  const element = document.querySelector(selector);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// Export functions for potential use by popup
window.visualAIAssistant = {
  detectFormFields,
  fillFields,
  highlightField,
  scrollToField
};
