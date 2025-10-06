FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .
COPY tools.py .

# Expose port for SSE server
EXPOSE 8000

# Run as non-root user (but with access to system for demonstration)
RUN useradd -m -u 1000 mcpuser
USER mcpuser

# Start the server
CMD ["python", "server.py"]
