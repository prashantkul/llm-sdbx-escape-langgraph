FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY *.py ./
COPY langgraph.json ./

# Create results directory
RUN mkdir -p results

# Expose LangGraph server port
EXPOSE 2024

# Set environment variable for logging directory
ENV LOG_DIR=/app/results

# Run LangGraph server
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024"]
