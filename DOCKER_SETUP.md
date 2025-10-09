# Docker Setup - Quick Reference

## ✅ Fixed Issues

1. **Agent Dockerfile build context**: Changed from `./agent` to `.` (project root) to properly access `logging/` module
2. **File paths in Dockerfile**: Updated to use `agent/*.py` and `logging/` paths relative to project root
3. **Removed obsolete version**: Removed `version: '3.8'` from docker-compose.yml (no longer needed in Compose v2)

## 🚀 Ready to Run

The Docker setup is now complete and validated. To run:

```bash
# Build containers
docker-compose build

# Run experiment
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f agent
```

## 📁 Docker Build Context Structure

```
. (project root - build context for agent)
├── agent/
│   ├── Dockerfile         # Uses paths relative to project root
│   ├── *.py              # Copied via agent/*.py
│   └── requirements.txt  # Copied via agent/requirements.txt
├── logging/              # Copied via logging/
│   └── logger.py
├── mcp_server/           # Separate build context
│   ├── Dockerfile
│   ├── server.py
│   ├── tools.py
│   └── requirements.txt
├── results/              # Mounted as volume
└── docker-compose.yml

```

## 🔧 Configuration

Environment variables (from `.env`):
- `GOOGLE_API_KEY` - Your Gemini API key (required)
- `GEMINI_MODEL` - Model to use (default: gemini-1.5-flash)
- `MAX_ATTEMPTS` - Maximum injection attempts (default: 10)
- `MCP_SERVER_URL` - Automatically set to `http://mcp-server:8000` in Docker

## 🌐 Network Architecture

```
┌─────────────────────────────────────────┐
│   Docker Network (research-net)         │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  MCP Server Container          │    │
│  │  - Port 8000                   │    │
│  │  - Vulnerable execute tool     │    │
│  └─────────────┬──────────────────┘    │
│                │ HTTP                   │
│  ┌─────────────▼──────────────────┐    │
│  │  Agent Container               │    │
│  │  - LangGraph workflow          │    │
│  │  - Gemini API client           │    │
│  │  - Volume: /app/results        │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## 📊 Results

Results are saved to `./results/` on the host machine and are accessible even after containers stop.

For detailed documentation, see [DOCKER.md](DOCKER.md).
