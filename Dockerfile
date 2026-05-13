# Use a stable, official Python runtime baseline matching your application stack
FROM python:3.11-slim

# Enforce clean terminal telemetry streams inside container environments
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Establish the secure system isolation root
WORKDIR /app

# Install native system binary compilation utilities required for heavy python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage dependency manifestations into the filesystem cache layer
COPY requirements.txt .

# --- CRITICAL RESOLUTION PHASE ---
# 1. Upgrade baseline packaging ecosystem binaries
# 2. Pre-install the pinned telemetry/typing baseline to break version loops 
# 3. Compile the comprehensive multi-framework requirements sheet using the legacy architecture
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        "pydantic==2.10.6" \
        "opentelemetry-api==1.25.0" \
        "opentelemetry-sdk==1.25.0" \
        "opentelemetry-semantic-conventions==0.46b0" \
        --break-system-packages && \
    pip install --no-cache-dir -r requirements.txt --use-deprecated=legacy-resolver --break-system-packages

# Pre-provision the required persistent system directories 
# This prevents Docker volume mounting racing state permission blocks during Jenkins runs
RUN mkdir -p /app/output /app/knowledge /app/plugins /app/.crewai

# Copy the complete functional orchestration logic layer into the image context
COPY . .

# Grant execution rights to python entrypoints inside the target runtime profile
RUN chmod +x main.py

# Execute the core workflow engine bootstrapper
CMD ["python", "main.py"]
