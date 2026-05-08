FROM python:3.11-slim

# Install system dependencies
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

# Copy requirements from the root
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all project files from root into /app
COPY . .

# Sanitize line endings for all Python files
RUN find . -type f -name "*.py" -print0 | xargs -0 dos2unix && \
    apt-get --purge remove -y dos2unix

# Create necessary persistent and safe directories
RUN mkdir -p /app/output /app/knowledge /app/.crewai
