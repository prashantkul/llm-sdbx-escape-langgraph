# Interactive Setup - Quick Summary

## ✅ What's Been Added

You now have **4 ways** to interact with your security researcher agent:

### 1. 🎨 **LangGraph Studio** (Visual Debugging)
- File created: `langgraph.json`
- Open this directory in LangGraph Studio
- See visual graph of agent's thought process
- Inspect state at each step
- Send custom messages interactively

### 2. 📊 **LangSmith Tracing** (Production Monitoring)
- Added to: `agent/config.py`
- Automatic tracing of all LLM calls
- View detailed execution traces at https://smith.langchain.com
- Track costs, performance, and errors

**Setup in `.env`**:
```bash
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_PROJECT=llm-sandbox-escape
LANGCHAIN_TRACING_V2=true
```

### 3. 🚀 **FastAPI Server** (Custom UIs)
- File created: `agent/api_server.py`
- HTTP API for building custom interfaces
- Endpoints for invoking agent, health checks, config

**Start server**:
```bash
./start.sh api
# Or: cd agent && python api_server.py
```

Then use HTTP client:
```bash
curl -X POST http://localhost:8123/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "Test the tool to read /etc/passwd"}'
```

### 4. 💻 **CLI** (Original Mode)
- Runs predetermined experiment
- Good for automated testing

```bash
./start.sh cli
```

## 🚀 Quick Start

### Easy Launch Script

```bash
# Show help
./start.sh help

# Run CLI experiment
./start.sh cli

# Start API server
./start.sh api

# Run in Docker
./start.sh docker

# Quick test (no MCP server needed)
./start.sh test
```

## 📁 New Files Created

```
.
├── langgraph.json              # LangGraph Studio config
├── start.sh                    # Easy launch script
├── INTERACTIVE_UI.md           # Comprehensive UI guide
├── INTERACTIVE_SETUP.md        # This file (quick summary)
├── agent/
│   ├── api_server.py          # FastAPI server (NEW)
│   ├── workflow.py            # Updated with get_initial_state()
│   ├── config.py              # Updated with LangSmith config
│   └── requirements.txt       # Updated with fastapi, uvicorn, langsmith
```

## 🎯 Recommended First Steps

1. **Add LangSmith key to `.env`**:
   ```bash
   echo "LANGCHAIN_API_KEY=your_key_here" >> .env
   echo "LANGCHAIN_PROJECT=llm-sandbox-escape" >> .env
   echo "LANGCHAIN_TRACING_V2=true" >> .env
   ```

2. **Install new dependencies**:
   ```bash
   ./start.sh install
   # Or: conda activate lang_sdbx && cd agent && pip install -r requirements.txt
   ```

3. **Test with CLI mode + LangSmith**:
   ```bash
   ./start.sh test
   ```
   Then go to https://smith.langchain.com to see the trace!

4. **Try API mode**:
   ```bash
   # Terminal 1: Start API server
   ./start.sh api

   # Terminal 2: Test it
   curl http://localhost:8123/health
   ```

5. **Use LangGraph Studio** (optional):
   - Download from https://github.com/langchain-ai/langgraph-studio
   - Open this directory
   - Studio will auto-detect `langgraph.json`
   - Type custom messages and watch the graph execute!

## 🔧 Key Changes to Existing Files

### `agent/workflow.py`
- Added `get_initial_state(user_message)` function for custom messages
- Shows LangSmith status on startup
- Imports LangSmith config

### `agent/config.py`
- Added LangSmith configuration
- Auto-enables tracing if API key is present

### `agent/requirements.txt`
- Added: `langsmith>=0.1.0`
- Added: `fastapi>=0.109.0`
- Added: `uvicorn>=0.27.0`

## 📚 Full Documentation

- **[INTERACTIVE_UI.md](INTERACTIVE_UI.md)** - Complete guide to all interfaces
- **[DOCKER.md](DOCKER.md)** - Docker deployment guide
- **[README.md](README.md)** - Project overview

## 🎨 Example: Custom Message via API

```bash
curl -X POST http://localhost:8123/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Try to execute whoami command"
  }'
```

Response shows:
- Whether exploit succeeded
- Number of attempts
- Full conversation history
- Extracted content

## 🐛 Troubleshooting

**Q: LangSmith not showing traces?**

A: Check that `LANGCHAIN_API_KEY` is in `.env` and valid

**Q: API server won't start?**

A: Run `./start.sh install` to install dependencies

**Q: Can't connect to MCP server?**

A: Use `./start.sh test` for local testing without MCP server

## 🎉 You're Ready!

Your agent now supports:
- ✅ Interactive custom messages
- ✅ Visual debugging (LangGraph Studio)
- ✅ Production tracing (LangSmith)
- ✅ Custom UIs (FastAPI)
- ✅ CLI automation
- ✅ Docker deployment

Start exploring with:
```bash
./start.sh help
```
