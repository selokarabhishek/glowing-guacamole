# Security Analysis & Recommendations

## ⚠️ CRITICAL VULNERABILITIES (Must Fix Before Production)

### 1. CORS Configuration - **CRITICAL**
**Risk Level**: 🔴 **CRITICAL**

**Current Issue**:
```python
allow_origins=["*"]  # Allows ANY website to access your API
```

**Attack Scenario**:
- Attacker hosts malicious website at evil.com
- When you visit evil.com, it can call your localhost:8000 API
- Can steal your memory data, analyze your browsing, or spam your VLM providers

**Fix**:
```python
# Only allow extension to access API
allow_origins=[
    "chrome-extension://*",  # Allow any Chrome extension (can be more specific)
]
```

### 2. No Authentication - **CRITICAL**
**Risk Level**: 🔴 **CRITICAL**

**Current Issue**:
- Any process on your computer can access the API
- No API key or token required
- Anyone on localhost:8000 can delete all your memory

**Attack Scenario**:
- Malware on your computer calls DELETE /api/memory/clear
- All your stored interactions are gone
- Or continuously queries memory to steal browsing history

**Recommended Fix**:
Add API token authentication between extension and backend.

### 3. Screenshot Data Leakage - **HIGH**
**Risk Level**: 🟠 **HIGH**

**Current Issue**:
- Screenshots may contain passwords, credit cards, personal info
- Sent to third-party APIs (Anthropic, OpenAI)
- No warning to user about sensitive data
- Stored in memory database without encryption

**Attack Scenarios**:
- User analyzes banking page → credentials sent to Claude/OpenAI
- VLM provider logs may retain sensitive data
- ChromaDB memory stores unencrypted screenshots/analyses

**Mitigations**:
1. Add warning for sensitive pages
2. Don't store screenshots in memory
3. Detect password fields and warn user
4. Add "sensitive mode" that uses only local Ollama

### 4. Information Disclosure - **MEDIUM**
**Risk Level**: 🟡 **MEDIUM**

**Current Issue**:
```python
# /api/settings/providers reveals if API keys are configured
api_key_configured=bool(self.settings.anthropic_api_key)
```

**Risk**: Reveals which providers you have access to

### 5. No Input Sanitization - **MEDIUM**
**Risk Level**: 🟡 **MEDIUM**

**Current Issue**:
- User prompts sent directly to VLM without sanitization
- Could be used for prompt injection attacks
- VLM responses rendered with limited sanitization

### 6. Memory Storage - **MEDIUM**
**Risk Level**: 🟡 **MEDIUM**

**Current Issue**:
- ChromaDB stores all data in plaintext
- File permissions only protection
- Contains URLs, analyses, user instructions
- No encryption at rest

### 7. No Rate Limiting - **LOW**
**Risk Level**: 🟢 **LOW**

**Current Issue**:
- No limits on API calls
- Could drain VLM API credits
- No cost protection

---

## 🛡️ SECURITY FIXES

### Priority 1: Immediate Fixes (Before Any Use)

#### Fix 1: Restrict CORS
**File**: `backend/app/main.py`

```python
# Replace existing CORS middleware with:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Allow Chrome extensions only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Only needed methods
    allow_headers=["Content-Type"],
)
```

#### Fix 2: Add Simple Authentication
**File**: `backend/app/config.py`

```python
class Settings(BaseSettings):
    # Add authentication token
    api_token: str = ""  # Set in .env
```

**File**: `backend/.env.example`
```env
# Security - generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_TOKEN=your-secure-token-here
```

**File**: `backend/app/main.py`
```python
from fastapi import HTTPException, Header
from app.config import get_settings

async def verify_token(authorization: str = Header(None)):
    settings = get_settings()
    if not settings.api_token:
        return  # Optional in dev mode

    if not authorization or authorization != f"Bearer {settings.api_token}":
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Add to protected routes
@app.post("/api/analyze/")
async def analyze(request: AnalyzeRequest, token: str = Depends(verify_token)):
    ...
```

**File**: `extension/popup/popup.js`
```javascript
// Load token from extension storage
let API_TOKEN = null;

async function loadApiToken() {
  const result = await chrome.storage.local.get(['apiToken']);
  API_TOKEN = result.apiToken || '';
}

// Add to all fetch calls:
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${API_TOKEN}`
}
```

#### Fix 3: Add Sensitive Page Warning
**File**: `extension/popup/popup.js`

```javascript
// Add before screenshot capture
async function analyzeCurrentPage() {
  // Check for sensitive page
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (isSensitivePage(tab.url)) {
    const confirmed = confirm(
      '⚠️ WARNING: This page may contain sensitive information.\n\n' +
      'Screenshots will be sent to AI providers and may be logged.\n\n' +
      'Consider using:\n' +
      '- Local provider (Ollama) instead\n' +
      '- Disabling memory storage\n\n' +
      'Continue anyway?'
    );

    if (!confirmed) return;
  }

  // Continue with analysis...
}

function isSensitivePage(url) {
  const sensitivePatterns = [
    /banking|bank|chase|wellsfargo|bofa/i,
    /paypal|venmo|cashapp/i,
    /login|signin|password|auth/i,
    /checkout|payment|credit-card/i,
    /medical|health|patient/i,
    /ssn|tax|irs|w2|w9/i,
  ];

  return sensitivePatterns.some(pattern => pattern.test(url));
}
```

### Priority 2: Recommended Enhancements

#### Enhancement 1: Encrypt Memory Storage
```python
from cryptography.fernet import Fernet

class MemoryStore:
    def __init__(self, persist_dir: str, encryption_key: str = None):
        self.cipher = Fernet(encryption_key) if encryption_key else None

    def store(self, analysis: str, ...):
        if self.cipher:
            analysis = self.cipher.encrypt(analysis.encode()).decode()
        # ... rest of storage
```

#### Enhancement 2: Add Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/analyze/")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def analyze(...):
    ...
```

#### Enhancement 3: Input Validation
```python
from pydantic import validator

class AnalyzeRequest(BaseModel):
    prompt: str

    @validator('prompt')
    def validate_prompt(cls, v):
        if len(v) > 2000:
            raise ValueError('Prompt too long')
        # Check for suspicious patterns
        if any(word in v.lower() for word in ['ignore previous', 'system:', 'admin']):
            raise ValueError('Suspicious prompt detected')
        return v
```

---

## 🔒 SECURITY BEST PRACTICES

### For Users

1. **API Keys**:
   - ✅ Never commit `.env` file
   - ✅ Use environment-specific keys (dev vs prod)
   - ✅ Rotate keys regularly
   - ❌ Don't share screenshots of your extension

2. **Sensitive Data**:
   - ❌ Don't analyze banking/payment pages
   - ❌ Don't analyze pages with passwords visible
   - ✅ Use Ollama (local) for sensitive content
   - ✅ Disable memory for sensitive sessions

3. **Memory Storage**:
   - 🔍 Review stored memories periodically
   - 🗑️ Clear memory when analyzing sensitive sites
   - 🔒 Know that data is stored in plaintext

4. **Provider Selection**:
   - **Claude/OpenAI**: Data sent to third-party, may be logged
   - **Ollama**: Stays on your computer, more private
   - Check each provider's data retention policy

### For Developers

1. **Before Deploying**:
   ```bash
   # Generate secure token
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Add to .env
   API_TOKEN=<generated-token>
   ```

2. **Network Security**:
   - Use HTTPS if exposing beyond localhost
   - Consider VPN for remote access
   - Don't expose 8000 to public internet

3. **Code Review**:
   - Audit all data flows
   - Check for XSS in UI rendering
   - Validate all user inputs
   - Review VLM provider responses

4. **Monitoring**:
   - Log failed auth attempts
   - Monitor API usage
   - Alert on unusual patterns

---

## 🎯 THREAT MODEL

### What We're Protecting

1. **API Keys** → Financial loss if stolen
2. **Browsing History** → Privacy violation
3. **Personal Data in Screenshots** → Identity theft
4. **Memory Database** → Complete browsing profile

### Threat Actors

1. **Malicious Websites**: Can exploit CORS if not fixed
2. **Malware on Local Machine**: Can access localhost API
3. **VLM Providers**: Have access to all screenshot data
4. **Physical Access**: Can read ChromaDB files

### Attack Vectors

1. ✅ **XSS**: Mitigated (using textContent)
2. 🔴 **CSRF**: Vulnerable (no CORS restrictions)
3. 🔴 **Unauthorized Access**: Vulnerable (no auth)
4. 🟡 **Data Leakage**: Partially vulnerable (VLM providers)
5. 🟡 **Prompt Injection**: Partially vulnerable

---

## ✅ SECURITY CHECKLIST

Before using this application:

- [ ] Apply CORS fix (Priority 1)
- [ ] Add authentication token (Priority 1)
- [ ] Test sensitive page warnings (Priority 1)
- [ ] Review `.gitignore` excludes `.env`
- [ ] Generate strong API token
- [ ] Understand VLM provider data policies
- [ ] Set up rate limiting (recommended)
- [ ] Document incident response plan
- [ ] Regular security audits

---

## 📞 REPORTING SECURITY ISSUES

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security concerns privately
3. Include detailed reproduction steps
4. Allow time for fixes before disclosure

---

## 📚 REFERENCES

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Chrome Extension Security](https://developer.chrome.com/docs/extensions/mv3/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Anthropic Data Policy](https://www.anthropic.com/privacy)
- [OpenAI Data Policy](https://openai.com/policies/privacy-policy)

---

**Last Updated**: 2025-11-21
**Status**: ⚠️ Development Only - Not Production Ready
