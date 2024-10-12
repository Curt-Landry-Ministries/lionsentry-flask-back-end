# Base image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt file into the container
COPY ./requirements.txt /app/

# Upgrade pip and install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -r /app/requirements.txt

# Bundle the entire backend source
COPY . /app/

# Set the PYTHONPATH environment variable
ENV PYTHONPATH /app

# Expose the port the auth server runs on
EXPOSE 5002

# Command to run the auth server
CMD ["python", "-m", "backend.auth_server.auth_server"]
