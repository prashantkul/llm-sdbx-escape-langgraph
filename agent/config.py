"""
Configuration for the LangGraph agent.
"""

import os

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")  # Will be updated with uncensored model

# MCP Server Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
MCP_SSE_ENDPOINT = f"{MCP_SERVER_URL}/sse"

# Agent Configuration
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "10"))
SUCCESS_PATTERN = r'root:.*:0:0:'  # Pattern to detect /etc/passwd content

# Logging Configuration
LOG_DIR = os.getenv("LOG_DIR", "../results")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
