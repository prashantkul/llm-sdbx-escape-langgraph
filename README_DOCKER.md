# 🐳 Docker Deployment - Quick Start

Run the entire LLM Sandbox Escape Testing Framework in **2 Docker containers**.

## ⚡ Super Quick Start

```bash
# 1. Set your API key
export GOOGLE_API_KEY="your_gemini_api_key"

# 2. Start everything
./docker-start.sh -d

# 3. Open browser
open http://localhost:8080
```

That's it! 🎉

## 📦 What Gets Deployed

### Container 1: `vulnerable-mcp-server`
**Port**: 8000
**Contains**: Python + curl + bash + grep + all system utilities
**Purpose**: Vulnerable target for escape testing

### Container 2: `langgraph-agent-ui`
**Ports**: 8123 (API), 8080 (UI)
**Contains**: LangGraph agent + FastAPI + Web UI
**Purpose**: Testing interface and agent orchestration

## 🚀 Detailed Setup

### Step 1: Prerequisites

- Docker & Docker Compose installed
- Google Gemini API key

### Step 2: Configure

Create `.env` file:
```bash
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Step 3: Launch

**Option A - Using startup script** (Recommended):
```bash
./docker-start.sh
```

**Option B - Direct docker-compose**:
```bash
docker-compose up --build
```

**Option C - Detached mode**:
```bash
./docker-start.sh -d
# or
docker-compose up -d --build
```

### Step 4: Access

- **Web UI**: http://localhost:8080
- **API Docs**: http://localhost:8123/docs
- **MCP Server**: http://localhost:8000

## 🎯 Quick Test

1. Open http://localhost:8080
2. Select "Interactive Mode"
3. Try: `Use read_file to read /etc/passwd`
4. See results instantly!

## 🛠️ Common Commands

```bash
# Start containers
./docker-start.sh

# Start in background
./docker-start.sh -d

# View logs
./docker-start.sh logs
# or
docker-compose logs -f

# Restart
./docker-start.sh restart

# Stop
./docker-start.sh down
# or
docker-compose down

# Complete cleanup
docker-compose down -v
```

## 🔍 Debugging

### Enter containers

```bash
# MCP Server
docker exec -it vulnerable-mcp-server bash

# Agent + UI
docker exec -it langgraph-agent-ui bash
```

### Check logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f mcp-server
docker-compose logs -f langgraph-ui
```

### Test connectivity

```bash
# MCP health
curl http://localhost:8000/mcp

# API health
curl http://localhost:8123/health
```

## 📊 Running Tests Inside Docker

```bash
# Enter the agent container
docker exec -it langgraph-agent-ui bash

# Run automated tests
cd /app/agent
python escape_tester.py

# Copy results out
exit
docker cp langgraph-agent-ui:/app/agent/escape_test_report_*.json ./
```

## 🐛 Troubleshooting

### Problem: GOOGLE_API_KEY not set

```bash
export GOOGLE_API_KEY="your_key"
./docker-start.sh
```

### Problem: Port already in use

```bash
# Find what's using the port
lsof -i :8080

# Kill it or change ports in docker-compose.yml
```

### Problem: Containers won't start

```bash
# Clean slate
docker-compose down -v
docker-compose up --build --force-recreate
```

## 📚 Full Documentation

- [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) - Complete Docker guide
- [ESCAPE_TECHNIQUES.md](./ESCAPE_TECHNIQUES.md) - All escape techniques
- [TESTING_ESCAPE_TECHNIQUES.md](./TESTING_ESCAPE_TECHNIQUES.md) - How to test
- [README_ESCAPE_TESTING.md](./README_ESCAPE_TESTING.md) - Framework overview

## 🎓 Next Steps

1. ✅ Containers running → http://localhost:8080
2. ✅ UI loaded → Try interactive mode
3. ✅ Tests work → Run automated suite
4. ✅ Results analyzed → Develop defenses

## ⚙️ Architecture

```
Host Machine
    ↓
┌───────────────────────────┐
│  Docker Network           │
│  (research-net)           │
│                           │
│  ┌──────────────────┐    │
│  │ MCP Server       │    │
│  │ :8000            │    │
│  │ (curl, bash, py) │◄───┤
│  └──────────────────┘    │
│           ▲               │
│           │               │
│  ┌────────┴──────────┐   │
│  │ LangGraph + UI    │   │
│  │ :8123 (API)       │   │
│  │ :8080 (UI)        │   │
│  └───────────────────┘   │
└───────────────────────────┘
```

## 🔐 Security Note

⚠️ **This contains intentional vulnerabilities for security research only.**

- Only for authorized testing
- Do not expose to internet
- Use in isolated environments
- For educational purposes

---

**Happy Dockerized Testing! 🐳**
