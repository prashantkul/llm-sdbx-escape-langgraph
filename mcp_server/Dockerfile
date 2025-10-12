FROM python:3.11-slim

# Install system utilities (intentionally available for security testing)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    bash \
    procps \
    findutils \
    grep \
    coreutils \
    vim \
    less \
    file \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server_official.py .

# Create a fake /etc/passwd with test data (for escape testing)
RUN echo "root:x:0:0:root:/root:/bin/bash" > /etc/passwd.test && \
    echo "mcpuser:x:1000:1000:MCP User:/home/mcpuser:/bin/bash" >> /etc/passwd.test && \
    echo "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin" >> /etc/passwd.test && \
    echo "nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin" >> /etc/passwd.test

# Expose MCP server port
EXPOSE 8000

# Run as non-root user (but with intentional access for testing)
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to mcpuser
USER mcpuser

# Start the server
CMD ["python", "server_official.py"]
