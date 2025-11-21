# Visual AI Assistant

A browser extension with Python FastAPI backend that uses Vision Language Models (Claude, OpenAI, Ollama) to analyze web pages, extract form fields, and learn from interactions using RAG memory.

## Features

- **Screenshot Analysis**: Capture and analyze any web page with AI vision models
- **Multi-Provider Support**: Choose between Claude, OpenAI GPT-4o, or Ollama (local)
- **Form Detection**: Automatically detect and extract form fields with labels and selectors
- **RAG Memory**: Store and retrieve past interactions for personalized suggestions
- **React Compatible**: Smart form filling that works with React and other frameworks
- **Clean UI**: Modern, Apple-inspired interface

## Architecture

```
visual-ai-assistant/
├── backend/              # FastAPI backend server
│   ├── app/
│   │   ├── vlm/         # VLM provider implementations
│   │   ├── memory/      # ChromaDB RAG storage
│   │   ├── routes/      # API endpoints
│   │   └── models/      # Pydantic schemas
│   └── data/            # ChromaDB persistence
├── extension/            # Chrome extension
│   ├── popup/           # Extension UI
│   ├── background.js    # Service worker
│   └── content.js       # Page interaction script
```

## Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- API keys for Claude or OpenAI (or Ollama running locally)
- macOS, Linux, or Windows

## Quick Start

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend
python run.py
```

The backend will start on `http://localhost:8000`

### 2. Extension Setup

```bash
# Generate placeholder icons (optional, requires ImageMagick)
cd extension/icons
./generate_placeholder.sh

# Or add your own icons:
# - icon16.png (16x16)
# - icon48.png (48x48)
# - icon128.png (128x128)
```

**Load Extension in Chrome:**

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` folder
5. The Visual AI Assistant icon should appear in your toolbar

### 3. Configuration

Edit `backend/.env` with your API keys:

```env
# Choose your default provider
DEFAULT_VLM_PROVIDER=claude

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...

# For Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5vl:7b

# Models
CLAUDE_MODEL=claude-sonnet-4-20250514
OPENAI_MODEL=gpt-4o

# Server
HOST=127.0.0.1
PORT=8000

# Memory
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Usage

### Basic Analysis

1. Navigate to any web page
2. Click the Visual AI Assistant extension icon
3. Wait for "Connected" status (green)
4. Enter your prompt (e.g., "What forms are on this page?")
5. Click "Analyze Page"
6. View results and detected form fields

### Extract Form Fields

1. Click "Extract Forms" button
2. AI will identify all input fields with:
   - Field type (text, email, password, etc.)
   - Label text
   - CSS selector
   - Required status
   - Suggested values

### Save to Memory

1. After analyzing a page, click "Save to Memory"
2. Future analyses on similar pages will use this context
3. Memory is stored in ChromaDB with semantic search

### Provider Selection

- Use the dropdown in the header to switch between providers
- Green checkmark = available
- Red X = not configured or unavailable

## API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Analyze Page
```bash
POST http://localhost:8000/api/analyze/
Content-Type: application/json

{
  "image_base64": "base64_encoded_screenshot",
  "prompt": "What forms are on this page?",
  "url": "https://example.com",
  "use_memory": true,
  "provider": "claude"
}
```

### Extract Form Fields
```bash
POST http://localhost:8000/api/analyze/extract-fields
```

### Store Memory
```bash
POST http://localhost:8000/api/memory/store
Content-Type: application/json

{
  "url": "https://example.com",
  "analysis": "This page contains a login form...",
  "instruction": "Analyze the login page",
  "metadata": {}
}
```

### Query Memory
```bash
POST http://localhost:8000/api/memory/query
Content-Type: application/json

{
  "query": "login form",
  "url_filter": "example.com",
  "limit": 5
}
```

### Get Settings
```bash
GET http://localhost:8000/api/settings/
```

### Get Providers
```bash
GET http://localhost:8000/api/settings/providers
```

## Ollama Setup (Optional)

To use local models with Ollama:

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama server
ollama serve

# Pull vision model
ollama pull qwen2.5vl:7b

# Configure backend/.env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5vl:7b
```

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
python run.py

# API docs available at:
# http://localhost:8000/docs
```

### Extension Development

1. Make changes to extension files
2. Go to `chrome://extensions/`
3. Click the refresh icon on your extension
4. Test changes

## Testing

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Get providers
curl http://localhost:8000/api/settings/providers

# Get memory stats
curl http://localhost:8000/api/memory/stats
```

### Test Extension

1. Open extension popup
2. Check "Connected" status
3. Try analyzing a simple page (e.g., Google)
4. Verify results display correctly

## Troubleshooting

### Backend Not Connecting

- Ensure backend is running: `python backend/run.py`
- Check backend logs for errors
- Verify no other service is using port 8000

### CORS Errors

- Backend should have CORS middleware enabled (already configured)
- Check browser console for specific error messages

### Screenshot Fails

- Ensure `activeTab` permission is granted
- Tab must be focused when capturing
- Some pages (chrome://, file://) cannot be captured

### Provider Not Available

- Check API key is set in `.env`
- For Claude: Verify key starts with `sk-ant-api03-`
- For OpenAI: Verify key starts with `sk-`
- For Ollama: Ensure server is running (`ollama serve`)

### ChromaDB Errors

- Ensure `data/chroma` directory exists
- Check write permissions
- Try clearing memory from extension popup

### Memory Not Working

- Check ChromaDB is initialized (logs show on startup)
- Verify embedding model is downloaded
- Try saving a simple interaction first

## Project Structure

```
backend/app/
├── config.py           # Settings management
├── main.py            # FastAPI app
├── vlm/
│   ├── base.py        # Abstract VLM class
│   ├── claude_vlm.py  # Claude integration
│   ├── openai_vlm.py  # OpenAI integration
│   ├── ollama_vlm.py  # Ollama integration
│   └── router.py      # Provider factory
├── memory/
│   ├── store.py       # ChromaDB storage
│   └── retriever.py   # RAG retrieval
├── routes/
│   ├── analyze.py     # Analysis endpoints
│   ├── memory.py      # Memory endpoints
│   └── settings.py    # Settings endpoints
└── models/
    └── schemas.py     # Pydantic models
```

## Security Notes

- API keys are stored in `.env` (not committed to git)
- Backend runs on localhost only
- CORS allows all origins for extension development
- For production, configure proper CORS origins
- Never commit `.env` file with real API keys

## Future Enhancements

- [ ] Auto-fill functionality with user confirmation
- [ ] Support for more VLM providers (Gemini, LLaVA)
- [ ] Field validation before filling
- [ ] Export/import memory database
- [ ] Multi-page workflow memory
- [ ] Custom system prompts per domain
- [ ] Browser extension settings page
- [ ] Dark mode support

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions

## Credits

Built with:
- FastAPI - Modern Python web framework
- Anthropic Claude - Vision language model
- OpenAI GPT-4o - Vision language model
- Ollama - Local LLM runtime
- ChromaDB - Vector database for RAG
- Chrome Extensions API - Browser integration

---

**Status**: Ready for development and testing
**Version**: 1.0.0
**Last Updated**: 2025-11-21
