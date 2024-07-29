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

# Expose the port the app runs on
EXPOSE 5001

# Command to run the app
CMD ["python", "-m", "app_server.app_server"]
