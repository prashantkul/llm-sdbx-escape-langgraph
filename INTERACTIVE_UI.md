# Interactive UI Guide

This guide explains how to interact with the security researcher agent using various UIs and interfaces.

## 🎨 Available Interfaces

### 1. **LangGraph Studio** (Recommended for Visual Debugging)

LangGraph Studio provides a visual interface to see your agent's thought process, state transitions, and tool calls in real-time.

#### Setup

1. **Install LangGraph Studio**:
   ```bash
   # Download from: https://github.com/langchain-ai/langgraph-studio
   # Or use the desktop app
   ```

2. **Configure the project**:

   The `langgraph.json` file is already configured:
   ```json
   {
     "dependencies": ["."],
     "graphs": {
       "security_researcher": "./agent/workflow.py:create_agent_graph"
     },
     "env": ".env"
   }
   ```

3. **Open in LangGraph Studio**:
   - Open LangGraph Studio
   - Click "Open Project"
   - Select this directory
   - Studio will automatically detect `langgraph.json`

4. **Interact with the agent**:
   - Type custom messages in the input box
   - Click "Run" to execute
   - Watch the state transitions in real-time
   - View tool calls and outputs
   - Inspect intermediate states

### 2. **LangSmith Tracing** (For Production Monitoring)

LangSmith provides detailed tracing of all LLM calls, tool executions, and agent decisions.

#### Setup

1. **Get LangSmith API Key**:
   - Sign up at https://smith.langchain.com
   - Create a new API key

2. **Add to `.env`**:
   ```bash
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   LANGCHAIN_PROJECT=llm-sandbox-escape
   LANGCHAIN_TRACING_V2=true
   ```

3. **Run the agent** (any mode):
   ```bash
   # CLI mode
   conda activate lang_sdbx
   cd agent
   python workflow.py

   # API mode
   python api_server.py

   # Docker mode
   docker-compose up
   ```

4. **View traces**:
   - Go to https://smith.langchain.com
   - Select your project: "llm-sandbox-escape"
   - View detailed traces of each run
   - See LLM prompts, responses, tool calls
   - Analyze performance and costs

#### What You'll See in LangSmith

- **Full conversation history**: Every message, system prompt, and response
- **Tool calls**: Each `execute_shell_command` invocation with arguments
- **LLM reasoning**: The agent's thought process before each tool call
- **Timing data**: How long each step takes
- **Token usage**: Input/output tokens for cost analysis
- **Errors**: Stack traces and error details

### 3. **FastAPI Server** (For Custom UIs)

Run the agent as an HTTP API to build your own custom UI.

#### Start the server

```bash
conda activate lang_sdbx
cd agent
python api_server.py
```

Server starts on `http://localhost:8123`

#### API Endpoints

##### `GET /` - API Information
```bash
curl http://localhost:8123/
```

Response:
```json
{
  "name": "Security Researcher Agent API",
  "version": "1.0.0",
  "model": "gemini-1.5-flash",
  "max_attempts": 10,
  "endpoints": {
    "POST /invoke": "Run the agent with a custom message",
    "GET /health": "Health check",
    "GET /config": "Get current configuration"
  }
}
```

##### `POST /invoke` - Run the agent
```bash
curl -X POST http://localhost:8123/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test the execute_shell_command tool to read /etc/passwd"
  }'
```

Response:
```json
{
  "success": true,
  "attempt_count": 1,
  "target_content": "root:x:0:0:root:/root:/bin/bash...",
  "error": "",
  "messages": [
    {
      "type": "SystemMessage",
      "content": "You are an expert security researcher..."
    },
    {
      "type": "HumanMessage",
      "content": "Test the execute_shell_command tool..."
    },
    {
      "type": "AIMessage",
      "content": "I'll test the tool..."
    }
  ]
}
```

##### `GET /health` - Health check
```bash
curl http://localhost:8123/health
```

##### `GET /config` - Current configuration
```bash
curl http://localhost:8123/config
```

#### Build a Custom Web UI

Example using HTML + JavaScript:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Security Researcher Agent</title>
</head>
<body>
    <h1>Security Researcher Agent</h1>
    <textarea id="message" rows="4" cols="50"
              placeholder="Enter your security testing task..."></textarea>
    <br>
    <button onclick="runAgent()">Run Agent</button>
    <br><br>
    <div id="result"></div>

    <script>
        async function runAgent() {
            const message = document.getElementById('message').value;
            const resultDiv = document.getElementById('result');

            resultDiv.innerHTML = 'Running...';

            try {
                const response = await fetch('http://localhost:8123/invoke', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message || null})
                });

                const data = await response.json();

                resultDiv.innerHTML = `
                    <h2>Results</h2>
                    <p><strong>Success:</strong> ${data.success}</p>
                    <p><strong>Attempts:</strong> ${data.attempt_count}</p>
                    <p><strong>Target Content:</strong></p>
                    <pre>${data.target_content}</pre>
                `;
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${error}</p>`;
            }
        }
    </script>
</body>
</html>
```

### 4. **Command Line (Programmatic)**

The original CLI interface for automated testing.

```bash
conda activate lang_sdbx
cd agent
python workflow.py
```

## 🔧 Configuration

All interfaces use the same `.env` configuration:

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional
GEMINI_MODEL=gemini-1.5-flash
MAX_ATTEMPTS=10
MCP_SERVER_URL=http://localhost:8000

# LangSmith (optional but recommended)
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=llm-sandbox-escape
LANGCHAIN_TRACING_V2=true

# For local testing without MCP server
USE_DIRECT_CLIENT=true
```

## 📊 Comparison of Interfaces

| Feature | LangGraph Studio | LangSmith | FastAPI | CLI |
|---------|-----------------|-----------|---------|-----|
| Visual graph | ✅ | ❌ | ❌ | ❌ |
| State inspection | ✅ | ✅ | ❌ | ❌ |
| Custom messages | ✅ | ❌ | ✅ | ❌ |
| Tracing | ✅ | ✅ | ✅ | ✅ |
| Production ready | ❌ | ✅ | ✅ | ✅ |
| Custom UI | ❌ | ❌ | ✅ | ❌ |
| Debugging | ✅✅ | ✅✅ | ✅ | ✅ |

## 🎯 Recommended Workflow

1. **Development**: Use **LangGraph Studio** for visual debugging and iteration
2. **Testing**: Use **LangSmith** to trace all runs and analyze behavior
3. **Production**: Use **FastAPI server** with custom UI for end users
4. **Automation**: Use **CLI** for scripted testing and CI/CD

## 🐛 Troubleshooting

### LangGraph Studio issues

**Problem**: Can't see the graph

**Solution**: Make sure `langgraph.json` is in project root and points to correct graph function:
```json
{
  "graphs": {
    "security_researcher": "./agent/workflow.py:create_agent_graph"
  }
}
```

### LangSmith not showing traces

**Problem**: No traces appearing in LangSmith

**Solution**:
1. Check API key is correct in `.env`
2. Verify `LANGCHAIN_TRACING_V2=true`
3. Check internet connection (traces are sent to cloud)
4. View console output for any errors

### API server won't start

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
conda activate lang_sdbx
pip install fastapi uvicorn
```

### MCP server connection failed

**Problem**: Agent can't connect to MCP server

**Solution**:
```bash
# For local testing, use direct mode
export USE_DIRECT_CLIENT=true

# Or start MCP server in another terminal
cd mcp_server
python server.py
```

## 📚 Next Steps

- **Customize prompts**: Edit `agent/prompts.py` to change agent behavior
- **Add more tools**: Extend the MCP server with additional vulnerable tools
- **Build dashboards**: Use the FastAPI endpoints to create monitoring dashboards
- **Export traces**: Use LangSmith API to export and analyze traces programmatically

For more details, see:
- [DOCKER.md](DOCKER.md) - Docker deployment
- [README.md](README.md) - Project overview
- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- [LangSmith docs](https://docs.smith.langchain.com/)
