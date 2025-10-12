FROM python:3.11-slim

# Install supervisor to run multiple processes
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install agent requirements
COPY agent/requirements.txt ./agent/requirements.txt
RUN pip install --no-cache-dir -r ./agent/requirements.txt

# Copy agent code
COPY agent/*.py ./agent/
COPY logging/ ./logging/

# Copy UI code
COPY ui/ ./ui/

# Create results directory
RUN mkdir -p /app/agent/results

# Create supervisor config
RUN mkdir -p /var/log/supervisor && \
    echo "[supervisord]" > /etc/supervisor/conf.d/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "user=root" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:api_server]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=python /app/agent/api_server.py" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "directory=/app/agent" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/var/log/supervisor/api_server.err.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/var/log/supervisor/api_server.out.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:ui_server]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=python /app/ui/server.py" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "directory=/app/ui" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/var/log/supervisor/ui_server.err.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/var/log/supervisor/ui_server.out.log" >> /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 8123 8080

# Run supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
