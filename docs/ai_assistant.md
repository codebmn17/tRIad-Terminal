```html name=index.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DevPod Dashboard</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      margin: 0;
      padding: 0;
      background: #f6f8fa;
      color: #24292e;
    }
    header {
      background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
      color: white;
      padding: 1rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem;
    }
    .dashboard {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.5rem;
      margin-top: 2rem;
    }
    .card {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 1.5rem;
      transition: transform 0.2s ease;
    }
    .card:hover {
      transform: translateY(-5px);
    }
    .card h2 {
      margin-top: 0;
      border-bottom: 1px solid #eaecef;
      padding-bottom: 0.5rem;
    }
    .card-link {
      display: inline-block;
      margin-top: 1rem;
      background: #0366d6;
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      text-decoration: none;
    }
    .status {
      display: inline-block;
      padding: 0.25rem 0.5rem;
      border-radius: 20px;
      font-size: 0.8rem;
      margin-left: 0.5rem;
    }
    .online {
      background: #28a745;
      color: white;
    }
  </style>
</head>
<body>
  <header>
    <h1>DevPod Dashboard</h1>
    <p>Your self-hosted development environment</p>
  </header>

  <div class="container">
    <div class="dashboard">
      <div class="card">
        <h2>Code Editor <span class="status online">online</span></h2>
        <p>VS Code in your browser with full extension support.</p>
        <a href="http://localhost:8080" class="card-link">Open Editor</a>
      </div>

      <div class="card">
        <h2>Git Repository <span class="status online">online</span></h2>
        <p>Store your code with version control and collaboration.</p>
        <a href="http://localhost:3000" class="card-link">Open Gitea</a>
      </div>

      <div class="card">
        <h2>Jupyter Lab <span class="status online">online</span></h2>
        <p>Interactive notebooks for data science and prototyping.</p>
        <a href="http://localhost:8888" class="card-link">Open Jupyter</a>
      </div>

      <div class="card">
        <h2>Project Management</h2>
        <p>Track issues and organize your development workflow.</p>
        <a href="http://localhost:3000/issues" class="card-link">Open Projects</a>
      </div>

      <div class="card">
        <h2>Terminal</h2>
        <p>Command-line access to your development environment.</p>
        <a href="http://localhost:8080/terminal" class="card-link">Open Terminal</a>
      </div>

      <div class="card">
        <h2>Settings</h2>
        <p>Configure your DevPod environment and services.</p>
        <a href="#" class="card-link">Open Settings</a>
      </div>
    </div>
  </div>

  <script>
    // Simple service status checker
    async function checkServices() {
      const services = [
        { url: '/code-server-status', selector: '.card:nth-child(1) .status' },
        { url: '/gitea-status', selector: '.card:nth-child(2) .status' },
        { url: '/jupyter-status', selector: '.card:nth-child(3) .status' }
      ];

      // In a real implementation, you'd check actual service endpoints
      console.log('Service status checked');
    }

    document.addEventListener('DOMContentLoaded', checkServices);
  </script>
</body>
</html>
