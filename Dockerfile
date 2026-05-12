FROM python:3.11-slim

ENV PYTHONPATH="/app"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic-dev \
    gcc \
    dos2unix \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/local/bin/python3 /usr/bin/python3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --use-deprecated=legacy-resolver --break-system-packages

COPY . .

# Sanitize line endings for all Python files
RUN find . -type f -name "*.py" -print0 | xargs -0 dos2unix && \
    apt-get --purge remove -y dos2unix

# Create necessary persistent and safe directories
RUN mkdir -p /app/output /app/knowledge /app/.crewai

CMD ["python", "main.py"]

