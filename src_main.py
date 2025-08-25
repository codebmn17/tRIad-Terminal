python src/main.py
```""" % name)

    elif template == "node":
        # Create package.json
        with open(os.path.join(project_dir, "package.json"), "w") as f:
            f.write("""{
  "name": "%s",
  "version": "1.0.0",
  "description": "Node.js project",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  },
  "dependencies": {}
}""" % name)

        # Create index.js
        with open(os.path.join(project_dir, "index.js"), "w") as f:
            f.write("""console.log('Hello from your Node.js project!');""")

        # Create README.md
        with open(os.path.join(project_dir, "README.md"), "w") as f:
            f.write("""# %s

A Node.js project created with Triad Terminal.

## Setup

```bash
npm install
