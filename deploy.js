#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const askQuestion = (query) => new Promise((resolve) => rl.question(query, resolve));

async function deployProject() {
  console.log('\x1b[36m%s\x1b[0m', '╔══════════════════════════════════════════════╗');
  console.log('\x1b[36m%s\x1b[0m', '║        DevPod Deployment Manager             ║');
  console.log('\x1b[36m%s\x1b[0m', '╚══════════════════════════════════════════════╝');

  try {
    // Get workspace directory
    const workspaceDir = path.join(process.cwd(), 'workspace');

    if (!fs.existsSync(workspaceDir)) {
      console.error(`Workspace directory not found at ${workspaceDir}`);
      return;
    }

    // List available projects
    const projects = fs.readdirSync(workspaceDir).filter(
      item => fs.statSync(path.join(workspaceDir, item)).isDirectory()
    );

    if (projects.length === 0) {
      console.log('No projects found in workspace. Create a project first.');
      return;
    }

    console.log('Available projects:');
    projects.forEach((project, i) => {
      console.log(`${i + 1}. ${project}`);
    });

    const projectIndex = parseInt(await askQuestion('\nSelect project to deploy (number): '));
    const projectName = projects[projectIndex - 1];

    if (!projectName) {
      console.error('Invalid project selection');
      return;
    }

    const projectDir = path.join(workspaceDir, projectName);
    const deployFile = path.join(projectDir, 'docker-compose.deploy.yml');

    if (!fs.existsSync(deployFile)) {
      console.log('Deployment configuration not found. Creating one...');

      const dockerfileExists = fs.existsSync(path.join(projectDir, 'Dockerfile'));

      const deployYaml = `version: '3'
services:
  ${projectName}:
    ${dockerfileExists ? 'build:\n      context: .' : 'image: nginx:latest'}
    ports:
      - "8000:${dockerfileExists ? '8000' : '80'}"
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.${projectName}.rule=Host(\`${projectName}.localhost\`)"
`;

      fs.writeFileSync(deployFile, deployYaml);
      console.log('Created deployment configuration.');
    }

    console.log(`\nDeploying ${projectName}...`);

    // Build and deploy using docker-compose
    process.chdir(projectDir);
    execSync('docker-compose -f docker-compose.deploy.yml up -d --build', { stdio: 'inherit' });

    console.log('\n\x1b[32m✓ Deployment complete!\x1b[0m');
    console.log(`\nAccess your application at: http://${projectName}.localhost`);
    console.log('(Make sure Traefik is configured correctly)');

    // Add to traefik dashboard
    console.log('\nYou can monitor your application at:');
    console.log('- Traefik Dashboard: http://localhost:8082/dashboard/');
    console.log('- Portainer: https://localhost:9443');

  } catch (error) {
    console.error('Deployment error:', error);
  } finally {
    rl.close();
  }
}

deployProject();
