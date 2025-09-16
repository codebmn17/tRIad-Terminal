#!/usr/bin/env python3

"""
Triad Terminal Advanced Features
Adds professional development capabilities
"""

import datetime
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any

import psutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.triad/logs/triad.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("triad")

class ResourceMonitor:
    """Monitor system resources for performance optimization"""

    @staticmethod
    def get_system_info() -> dict[str, Any]:
        """Get information about the system"""
        info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
        return info

    @staticmethod
    def log_resource_usage():
        """Log current resource usage"""
        info = ResourceMonitor.get_system_info()
        logger.debug(f"CPU: {info['cpu_percent']}% | Memory: {info['memory']['percent']}% | Disk: {info['disk']['percent']}%")

    @staticmethod
    def should_optimize() -> bool:
        """Check if resources are constrained and optimization needed"""
        info = ResourceMonitor.get_system_info()
        return info['memory']['percent'] > 85 or info['cpu_percent'] > 90

class DevelopmentServer:
    """Local development server for web projects"""

    def __init__(self, project_dir: str, port: int = 8000):
        self.project_dir = project_dir
        self.port = port
        self.process = None

    def start(self, server_type: str = "auto") -> bool:
        """Start a development server based on project type"""
        if server_type == "auto":
            server_type = self._detect_project_type()

        logger.info(f"Starting {server_type} development server at port {self.port}")

        try:
            if server_type == "node":
                if os.path.exists(os.path.join(self.project_dir, "package.json")):
                    if os.path.exists(os.path.join(self.project_dir, "node_modules", ".bin", "vite")):
                        self.process = psutil.Popen(["npx", "vite", "--port", str(self.port)], cwd=self.project_dir)
                    elif os.path.exists(os.path.join(self.project_dir, "node_modules", ".bin", "next")):
                        self.process = psutil.Popen(["npx", "next", "dev", "-p", str(self.port)], cwd=self.project_dir)
                    else:
                        self.process = psutil.Popen(["npx", "serve", "-l", str(self.port)], cwd=self.project_dir)
                else:
                    self.process = psutil.Popen(["npx", "serve", "-l", str(self.port)], cwd=self.project_dir)

            elif server_type == "python":
                if os.path.exists(os.path.join(self.project_dir, "manage.py")):
                    self.process = psutil.Popen([sys.executable, "manage.py", "runserver", f"0.0.0.0:{self.port}"], cwd=self.project_dir)
                elif os.path.exists(os.path.join(self.project_dir, "app.py")):
                    self.process = psutil.Popen([sys.executable, "app.py"], cwd=self.project_dir)
                else:
                    self.process = psutil.Popen([sys.executable, "-m", "http.server", str(self.port)], cwd=self.project_dir)

            elif server_type == "php":
                self.process = psutil.Popen(["php", "-S", f"0.0.0.0:{self.port}"], cwd=self.project_dir)

            else:  # static content
                self.process = psutil.Popen([sys.executable, "-m", "http.server", str(self.port)], cwd=self.project_dir)

            # Wait a moment to see if the server starts properly
            time.sleep(1)
            if self.process and self.process.is_running():
                logger.info(f"Development server running at http://localhost:{self.port}")
                return True

            logger.error("Failed to start development server")
            return False

        except Exception as e:
            logger.error(f"Error starting development server: {e}")
            return False

    def stop(self):
        """Stop the development server"""
        if self.process and self.process.is_running():
            logger.info("Stopping development server")

            for child in self.process.children(recursive=True):
                child.terminate()

            self.process.terminate()

            # Give it some time to terminate
            try:
                self.process.wait(timeout=5)
            except psutil.TimeoutExpired:
                self.process.kill()

    def _detect_project_type(self) -> str:
        """Detect the type of project"""
        # Check for Node.js project
        if os.path.exists(os.path.join(self.project_dir, "package.json")):
            return "node"

        # Check for Python projects
        if any(os.path.exists(os.path.join(self.project_dir, f)) for f in ["requirements.txt", "manage.py", "app.py"]):
            return "python"

        # Check for PHP projects
        if any(f.endswith(".php") for f in os.listdir(self.project_dir) if os.path.isfile(os.path.join(self.project_dir, f))):
            return "php"

        # Default to static content
        return "static"

class PackageManager:
    """Unified interface for package management across languages"""

    @staticmethod
    def install_package(package_name: str, language: str, dev: bool = False) -> bool:
        """Install a package for a specific language"""
        logger.info(f"Installing {language} package: {package_name} {'(dev)' if dev else ''}")

        try:
            if language == "python":
                cmd = [sys.executable, "-m", "pip", "install", package_name]
                subprocess.run(cmd, check=True)
                return True

            elif language == "node":
                if dev:
                    cmd = ["npm", "install", "--save-dev", package_name]
                else:
                    cmd = ["npm", "install", "--save", package_name]
                subprocess.run(cmd, check=True)
                return True

            elif language == "rust":
                cmd = ["cargo", "add", package_name]
                subprocess.run(cmd, check=True)
                return True

            else:
                logger.error(f"Unsupported language: {language}")
                return False

        except Exception as e:
            logger.error(f"Error installing package {package_name}: {e}")
            return False

    @staticmethod
    def uninstall_package(package_name: str, language: str) -> bool:
        """Uninstall a package for a specific language"""
        logger.info(f"Uninstalling {language} package: {package_name}")

        try:
            if language == "python":
                cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
                subprocess.run(cmd, check=True)
                return True

            elif language == "node":
                cmd = ["npm", "uninstall", package_name]
                subprocess.run(cmd, check=True)
                return True

            elif language == "rust":
                cmd = ["cargo", "remove", package_name]
                subprocess.run(cmd, check=True)
                return True

            else:
                logger.error(f"Unsupported language: {language}")
                return False

        except Exception as e:
            logger.error(f"Error uninstalling package {package_name}: {e}")
            return False

    @staticmethod
    def list_packages(language: str) -> list[dict[str, str]]:
        """List installed packages for a specific language"""
        logger.info(f"Listing {language} packages")

        try:
            if language == "python":
                output = subprocess.check_output([sys.executable, "-m", "pip", "list", "--format=json"])
                return json.loads(output)

            elif language == "node":
                if os.path.exists("package.json"):
                    with open("package.json") as f:
                        package_json = json.load(f)

                    deps = []
                    if "dependencies" in package_json:
                        for name, version in package_json["dependencies"].items():
                            deps.append({"name": name, "version": version, "type": "prod"})

                    if "devDependencies" in package_json:
                        for name, version in package_json["devDependencies"].items():
                            deps.append({"name": name, "version": version, "type": "dev"})

                    return deps
                return []

            else:
                logger.error(f"Unsupported language: {language}")
                return []

        except Exception as e:
            logger.error(f"Error listing packages: {e}")
            return []

class DatabaseManager:
    """Manage local databases for development"""

    @staticmethod
    def create_sqlite_db(name: str, directory: str | None = None) -> str | None:
        """Create a SQLite database"""
        try:
            import sqlite3

            if directory is None:
                directory = os.path.expanduser("~/.triad/databases")
                os.makedirs(directory, exist_ok=True)

            db_path = os.path.join(directory, f"{name}.db")

            # Create the database file
            conn = sqlite3.connect(db_path)
            conn.close()

            logger.info(f"Created SQLite database: {db_path}")
            return db_path

        except Exception as e:
            logger.error(f"Error creating SQLite database: {e}")
            return None

    @staticmethod
    def backup_database(db_path: str, backup_dir: str | None = None) -> str | None:
        """Back up a database"""
        try:
            if backup_dir is None:
                backup_dir = os.path.expanduser("~/.triad/backups")
                os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = os.path.basename(db_path)
            backup_path = os.path.join(backup_dir, f"{db_name}.{timestamp}.bak")

            # Simple file copy for backup
            import shutil
            shutil.copy2(db_path, backup_path)

            logger.info(f"Database backed up to: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return None

class CodeAnalyzer:
    """Static code analysis tools"""

    @staticmethod
    def analyze_python_code(file_path: str) -> dict[str, Any]:
        """Analyze Python code for issues"""
        results = {
            "errors": [],
            "warnings": [],
            "metrics": {}
        }

        try:
            # Use pylint for static analysis
            import subprocess

            # Run pylint
            process = subprocess.run(
                ["pylint", "--output-format=json", file_path],
                capture_output=True,
                text=True
            )

            # Process output
            if process.stdout:
                try:
                    pylint_results = json.loads(process.stdout)
                    for item in pylint_results:
                        if item["type"] == "error":
                            results["errors"].append({
                                "line": item["line"],
                                "message": item["message"],
                                "code": item["symbol"]
                            })
                        elif item["type"] in ["warning", "convention", "refactor"]:
                            results["warnings"].append({
                                "line": item["line"],
                                "message": item["message"],
                                "code": item["symbol"]
                            })
                except json.JSONDecodeError:
                    results["errors"].append({
                        "line": 0,
                        "message": "Failed to parse pylint output",
                        "code": "json-error"
                    })

            # Get complexity metrics
            try:
                import radon.complexity as cc
                import radon.metrics as metrics

                with open(file_path) as f:
                    code = f.read()

                # Calculate complexity
                complexity = cc.cc_visit(code)
                results["metrics"]["complexity"] = [
                    {
                        "name": item.name,
                        "type": item.type,
                        "complexity": item.complexity,
                        "line": item.lineno
                    } for item in complexity
                ]

                # Calculate maintainability index
                results["metrics"]["maintainability_index"] = metrics.mi_visit(code, True)

                # Calculate raw metrics
                raw_metrics = metrics.mi_parameters(code)
                results["metrics"]["halstead_volume"] = raw_metrics.h_vol
                results["metrics"]["loc"] = raw_metrics.sloc

            except ImportError:
                results["warnings"].append({
                    "line": 0,
                    "message": "Radon not installed, skipping complexity metrics",
                    "code": "import-error"
                })

        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            results["errors"].append({
                "line": 0,
                "message": f"Analysis failed: {str(e)}",
                "code": "analysis-error"
            })

        return results

class DocumentationGenerator:
    """Generate documentation for code"""

    @staticmethod
    def generate_python_docs(project_dir: str, output_dir: str | None = None) -> bool:
        """Generate documentation for Python project"""
        try:
            if output_dir is None:
                output_dir = os.path.join(project_dir, "docs")

            os.makedirs(output_dir, exist_ok=True)

            # Try to generate documentation with sphinx
            logger.info(f"Generating documentation for Python project: {project_dir}")

            # Check if sphinx is installed
            try:
                import sphinx
            except ImportError:
                logger.warning("Sphinx not installed, attempting to install it")
                subprocess.run([sys.executable, "-m", "pip", "install", "sphinx"], check=True)

            # Create sphinx configuration if needed
            conf_path = os.path.join(output_dir, "conf.py")
            if not os.path.exists(conf_path):
                # Create minimal sphinx configuration
                with open(conf_path, "w") as f:
                    f.write(f"""# Configuration file for the Sphinx documentation builder.

project = 'Triad Terminal Project'
copyright = '{datetime.datetime.now().year}, Triad Terminal'
author = 'Triad Terminal'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
""")

            # Create index file if needed
            index_path = os.path.join(output_dir, "index.rst")
            if not os.path.exists(index_path):
                with open(index_path, "w") as f:
                    f.write("""Welcome to Triad Terminal's documentation!
=====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
""")

            # Run sphinx-apidoc to generate module documentation
            subprocess.run([
                "sphinx-apidoc",
                "-o", output_dir,
                project_dir,
                "--force",
                "--separate"
            ], check=True)

            # Build HTML documentation
            subprocess.run([
                "sphinx-build",
                "-b", "html",
                output_dir,
                os.path.join(output_dir, "_build", "html")
            ], check=True)

            logger.info(f"Documentation generated at: {os.path.join(output_dir, '_build', 'html')}")
            return True

        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return False

class TestRunner:
    """Run tests for projects"""

    @staticmethod
    def run_python_tests(project_dir: str) -> dict[str, Any]:
        """Run Python tests using pytest"""
        results = {
            "success": False,
            "tests_run": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "details": []
        }

        try:
            logger.info(f"Running tests for Python project: {project_dir}")

            # Check if pytest is installed
            try:
                import pytest
            except ImportError:
                logger.warning("pytest not installed, attempting to install it")
                subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)

            # Run pytest with JSON output
            process = subprocess.run(
                [sys.executable, "-m", "pytest", "--json-report", "--json-report-file=none"],
                cwd=project_dir,
                capture_output=True,
                text=True
            )

            # Try to parse the JSON output
            try:
                import json
                output = json.loads(process.stdout)

                results["tests_run"] = output["summary"]["total"]
                results["passed"] = output["summary"]["passed"]
                results["failed"] = output["summary"]["failed"]
                results["errors"] = output["summary"]["errors"]
                results["skipped"] = output["summary"]["skipped"]
                results["success"] = results["failed"] == 0 and results["errors"] == 0

                # Add details for each test
                for test_name, test_result in output["tests"].items():
                    results["details"].append({
                        "name": test_name,
                        "outcome": test_result["outcome"],
                        "duration": test_result["duration"]
                    })

            except (json.JSONDecodeError, KeyError):
                # Fallback to just the return code
                results["success"] = process.returncode == 0
                results["tests_run"] = -1  # Unknown count

                # Add the output as details
                results["details"].append({
                    "name": "pytest_output",
                    "output": process.stdout
                })

            logger.info(f"Test results: {results['passed']} passed, {results['failed']} failed, {results['errors']} errors")
            return results

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            results["success"] = False
            results["errors"] = 1
            results["details"].append({
                "name": "error",
                "error": str(e)
            })
            return results
