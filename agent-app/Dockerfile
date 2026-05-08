FROM python:3.11-slim

# Install system dependencies for PDF processing, document parsing, and security tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic-dev \
    gcc \
    dos2unix \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy from the host's agent-app folder into the container's /app
COPY agent-app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the contents of agent-app into /app
COPY agent-app/ .

# Ensure line endings are fixed for all copied files
RUN find . -type f -name "*.py" -print0 | xargs -0 dos2unix && \
    apt-get --purge remove -y dos2unix

# Create necessary persistent and safe directories
RUN mkdir -p /app/output /app/knowledge /app/.crewai
