#!/bin/bash

######################
##### IMPORTANT ######
######################
# SETUP SSH KEYS ON INSTANCE FOR GITHUB FIRST #
# https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
# ssh-keygen -t ed25519 -C "your_email@example.com"
# ssh-keygen -t rsa -b 4096 -C "your_email@example.com" for legacy systems
# cat .ssh/id_ed25519.pub or cat .ssh/id_rsa.pub


# Remove conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Setup Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version

# Install python and pip packages
sudo apt-get install python3 python3-pip python3.10-venv

git clone git@github.com:Curt-Landry-Ministries/lionsentry-flask-back-end.git
cd lion-sentry-flask-backend
sudo apt-get update
sudo apt-get upgrade
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo bash build.sh -f