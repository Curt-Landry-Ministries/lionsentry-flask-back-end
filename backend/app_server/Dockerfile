# Use a slim Python 3.11 base image
FROM python:3.11-slim

# Set environment variables to prevent Python from buffering outputs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set the working directory to /app
WORKDIR /app

# Install only necessary system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ./requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . /app/

# Expose the port the app runs on
EXPOSE 5001

# Run the application
CMD ["python", "-m", "backend.app_server.app_server"]
