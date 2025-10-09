FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent/*.py ./

# Copy logging module
COPY logging/ ./logging/

# Create results directory
RUN mkdir -p /app/results

# Run the agent
CMD ["python", "workflow.py"]
