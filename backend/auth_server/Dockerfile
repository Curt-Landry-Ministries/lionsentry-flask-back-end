# Use a slim Python 3.11 base image
FROM python:3.11-slim

# Set environment variables to optimize runtime and prevent caching
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Set the working directory to /app
WORKDIR /app

# Install only necessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY ./requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . /app/

# Expose the port the auth server runs on
EXPOSE 5002

# Run the auth server
CMD ["python", "-m", "backend.auth_server.auth_server"]
