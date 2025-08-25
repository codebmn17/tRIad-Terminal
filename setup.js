#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('\x1b[36m%s\x1b[0m', '╔══════════════════════════════════════════════╗');
console.log('\x1b[36m%s\x1b[0m', '║           DevPod Setup Assistant             ║');
console.log('\x1b[36m%s\x1b[0m', '╚══════════════════════════════════════════════╝');

const askQuestion = (query) => new Promise((resolve) => rl.question(query, resolve));

async function setup() {
  try {
    // Create base directory
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    const installPath = await askQuestion(`Installation directory [${path.join(homeDir, 'devpod')}]: `);
    const basePath = installPath || path.join(homeDir, 'devpod');
    
    console.log(`\nSetting up DevPod in ${basePath}...`);
    
    if (!fs.existsSync(basePath)) {
      fs.mkdirSync(basePath, { recursive: true });
    }
    
    // Create subdirectories
    ['workspace', 'config', 'gitea', 'jupyter', '.devcontainer'].forEach(dir => {
      if (!fs.existsSync(path.join(basePath, dir))) {
        fs.mkdirSync(path.join(basePath, dir), { recursive: true });
      }
    });
    
    // Generate password
    const password = await askQuestion('Set password for code-server: ');
    
    // Write docker-compose file
    const composeFile = path.join(basePath, 'docker-compose.yml');
    const composeContent = `version: '3'
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
      - PASSWORD=${password}
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
`;

    fs.writeFileSync(composeFile, composeContent);
    
    // Copy dashboard HTML
    fs.writeFileSync(path.join(basePath, 'dashboard.html'), fs.readFileSync(path.join(__dirname, 'index.html')));
    
    console.log('\nConfiguration complete!');
    
    const startNow = (await askQuestion('Start DevPod now? [y/n]: ')).toLowerCase();
    
    if (startNow === 'y' || startNow === 'yes') {
      console.log('\nStarting DevPod...');
      process.chdir(basePath);
      execSync('docker-compose up -d', { stdio: 'inherit' });
      console.log('\n\x1b[32m%s\x1b[0m', '✓ DevPod is running!');
      console.log('\nAccess your development environment at:');
      console.log('- Code Editor: http://localhost:8080');
      console.log('- Git Repository: http://localhost:3000');
      console.log('- Jupyter Notebooks: http://localhost:8888');
    } else {
      console.log('\nTo start DevPod later, run:');
      console.log(`cd ${basePath} && docker-compose up -d`);
    }
    
    console.log('\nThank you for using DevPod!');
  } catch (error) {
    console.error('Setup failed:', error);
  } finally {
    rl.close();
  }
}

setup();