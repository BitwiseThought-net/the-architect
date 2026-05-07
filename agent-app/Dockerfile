FROM python:3.11-slim

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Keep the container running so we can 'exec' into it
CMD ["tail", "-f", "/dev/null"]
