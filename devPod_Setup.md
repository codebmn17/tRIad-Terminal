# DevPod: Self-Hosted Development Environment

This guide helps you set up a personal development environment with code editing, execution, and storage capabilities using entirely open-source components.

## Core Components

1. **Code-Server**: VS Code in the browser
2. **Docker**: For containerized environments
3. **Jupyter**: For interactive notebooks
4. **GitLab/Gitea**: For code storage and version control

## Setup Instructions

### Prerequisites
- A Linux server (can be local or cloud VPS)
- Docker and Docker Compose
- 2GB+ RAM, 10GB+ storage

### Basic Installation
```bash
# Create project directory
mkdir -p ~/devpod && cd ~/devpod

# Create docker-compose configuration
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  code-server:
    image: codercom/code-server:latest
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./workspace:/home/coder/project
      - ./config:/home/coder/.config
    environment:
      - PASSWORD=your_secure_password
      - DOCKER_HOST=tcp://docker-socket-proxy:2375

  gitea:
    image: gitea/gitea:latest
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - ./gitea:/data
    environment:
      - USER_UID=1000
      - USER_GID=1000

  jupyter:
    image: jupyter/datascience-notebook:latest
    ports:
      - "8888:8888"
    volumes:
      - ./jupyter:/home/jovyan/work

  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - CONTAINERS=1
      - IMAGES=1
      - NETWORKS=1
      - VOLUMES=1
      - SERVICES=1
EOF

# Launch the environment
docker-compose up -d
