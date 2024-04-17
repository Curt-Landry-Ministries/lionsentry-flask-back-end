### Steps to configure AWS [EC2](https://aws.amazon.com/ec2/) cloud instance 

#### Create and configure EC2 Instance

1.  Sign in to [AWS](https://signin.aws.amazon.com/)
2.  Click on [EC2]
3.  Click on [Launch Instance]
4.  Select [Ubuntu] Instance
5.  Select [Create new key pair] and download PEM file
6.  Select to allow [SSH] [HTTP] & [HTTPS]
7.  Select [Launch Instance]
8.  Once instance is launched, click [Connect]
9.  You are now in the ubuntu terminal
10. Set up docker

Install and Configure Docker
```
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
```

Setup Python
```
sudo apt-get install python3 python3-pip python3.10-venv
```

Run Containers
```
sudo apt-get update
sudo apt-get upgrade
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo bash build.sh -f
```

### To Do

- [X] Setup EC2 Instance
- [X] Setup Docker, Python, Pip
- [X] Setup NGINX Proxy for Docker Containers and Ports

### Resources
- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Docker-Compose](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04)