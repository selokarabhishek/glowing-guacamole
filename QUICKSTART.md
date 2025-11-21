# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Chrome browser installed
- [ ] At least one API key (Claude, OpenAI, or Ollama running)

## Step 1: Backend Setup (2 minutes)

```bash
# Option A: Use the quick start script
./start.sh

# Option B: Manual setup
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python run.py
```

## Step 2: Configure API Keys (1 minute)

Edit `backend/.env`:

```env
# Use Claude (recommended)
DEFAULT_VLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE

# OR use OpenAI
DEFAULT_VLM_PROVIDER=openai
OPENAI_API_KEY=sk-YOUR-KEY-HERE

# OR use Ollama (free, local)
DEFAULT_VLM_PROVIDER=ollama
# Make sure to run: ollama serve
```

## Step 3: Load Extension (1 minute)

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right toggle)
4. Click "Load unpacked"
5. Select the `extension` folder
6. Done! Look for the icon in your toolbar

## Step 4: Test It (1 minute)

1. Visit any website (try google.com)
2. Click the Visual AI Assistant extension icon
3. Wait for "Connected" status (green dot)
4. Click "Analyze Page"
5. View the AI's analysis!

## Troubleshooting

### "Disconnected" Status
- Make sure backend is running: `python backend/run.py`
- Check terminal for errors

### "Provider not available"
- Verify API key is correct in `.env`
- Restart backend after editing `.env`

### Screenshot Fails
- Make sure tab is focused
- Try a regular webpage (not chrome:// or file://)

### Need Icons?
```bash
cd extension/icons
./generate_placeholder.sh  # Requires ImageMagick
```

## What to Try

### Analyze a Login Form
```
Prompt: "What form fields are on this page? List them with their types."
```

### Get Page Summary
```
Prompt: "What is this page about? Summarize the main content."
```

### Find Specific Elements
```
Prompt: "Find all buttons on this page and tell me what they do."
```

### Use Memory
1. Analyze a page and click "Save to Memory"
2. Visit a similar page
3. Analyze with memory enabled
4. Notice contextual suggestions!

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out the [API docs](http://localhost:8000/docs) when backend is running
- Customize system prompts in `backend/app/config.py`
- Explore the code to understand how it works

## Getting Help

- Check backend terminal for error messages
- Open browser console (F12) for extension errors
- Verify API keys are valid
- Ensure all dependencies are installed

---

Happy analyzing! 🚀
