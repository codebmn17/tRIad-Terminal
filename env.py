# Example: Create a Python development container
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "Python Development",
  "image": "python:3.10",
  "extensions": [
    "ms-python.python",
    "ms-python.vscode-pylance"
  ],
  "settings": {
    "python.linting.enabled": true
  }
}
EOF
