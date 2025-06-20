FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if any needed for your packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Default command
CMD ["python", "agent.py", "dev"] 