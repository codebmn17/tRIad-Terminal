#!/usr/bin/env python3

"""
Triad Terminal Repository Manager
Handles Git repositories and GitHub integration
"""

import json
import logging
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger("triad.repo")

class GitCommand:
    """Helper for running Git commands"""

    @staticmethod
    def is_git_installed() -> bool:
        """Check if Git is installed"""
        try:
            subprocess.run(
                ["git", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def run(args: list[str], cwd: str = None, capture_output: bool = True) -> tuple[bool, str, str]:
        """Run a Git command and return result"""
        try:
            if capture_output:
                result = subprocess.run(
                    ["git"] + args,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                success = result.returncode == 0
                stdout = result.stdout.strip()
                stderr = result.stderr.strip()

                return success, stdout, stderr
            else:
                # Run without capturing output (interactive mode)
                result = subprocess.run(["git"] + args, cwd=cwd)
                return result.returncode == 0, "", ""
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            return False, "", str(e)

    @staticmethod
    def is_repo(path: str) -> bool:
        """Check if directory is a Git repository"""
        success, _, _ = GitCommand.run(["rev-parse", "--is-inside-work-tree"], path)
        return success

    @staticmethod
    def get_remote_url(path: str, remote: str = "origin") -> str | None:
        """Get remote URL for a repository"""
        success, stdout, _ = GitCommand.run(["remote", "get-url", remote], path)
        return stdout if success else None

    @staticmethod
    def get_current_branch(path: str) -> str | None:
        """Get current branch name"""
        success, stdout, _ = GitCommand.run(["branch", "--show-current"], path)
        return stdout if success else None

class GitHubAPI:
    """Interface with GitHub API"""

    def __init__(self, token: str | None = None, config_dir: str = "~/.triad/github"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.token_file = os.path.join(self.config_dir, "token")
        self.config_file = os.path.join(self.config_dir, "config.json")

        # Try to load token
        self.token = token or self._load_token()

        # Load config
        self.config = self._load_config()

        # API rate limit tracking
        self.rate_limit = None
        self.rate_limit_reset = None

    def _load_token(self) -> str | None:
        """Load GitHub token from file"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file) as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Error loading GitHub token: {e}")
        return None

    def save_token(self, token: str) -> None:
        """Save GitHub token to file"""
        try:
            # Make token file readable only by the user
            with open(self.token_file, 'w') as f:
                f.write(token)
            os.chmod(self.token_file, 0o600)
        except Exception as e:
            logger.error(f"Error saving GitHub token: {e}")

    def _load_config(self) -> dict[str, Any]:
        """Load GitHub configuration"""
        default_config = {
            "username": "",
            "default_visibility": "private",
            "default_license": "mit",
            "auto_init": True
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                    # Update with any missing default values
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"Error loading GitHub config: {e}")

        return default_config

    def save_config(self) -> None:
        """Save GitHub configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving GitHub config: {e}")

    def set_username(self, username: str) -> None:
        """Set GitHub username"""
        self.config["username"] = username
        self.save_config()

    def _make_request(self, method: str, url: str, data: Any = None,
                    headers: dict[str, str] = None) -> tuple[bool, Any]:
        """Make a request to GitHub API"""
        if not self.token:
            return False, {"message": "GitHub token not set"}

        if not headers:
            headers = {}

        # Add authorization and content type headers
        headers["Authorization"] = f"token {self.token}"
        headers["Accept"] = "application/vnd.github.v3+json"

        if data and method != "GET":
            data_bytes = json.dumps(data).encode('utf-8')
            headers["Content-Type"] = "application/json"
        else:
            data_bytes = None

        # Add API version
        if not url.startswith("https://"):
            url = f"https://api.github.com/{url.lstrip('/')}"

        try:
            # Create request
            request = urllib.request.Request(
                url=url,
                data=data_bytes,
                headers=headers,
                method=method
            )

            # Send request
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode('utf-8'))

                # Track rate limit
                if 'X-RateLimit-Remaining' in response.headers:
                    self.rate_limit = int(response.headers['X-RateLimit-Remaining'])
                if 'X-RateLimit-Reset' in response.headers:
                    self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])

                return True, response_data

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
            except json.JSONDecodeError:
                error_data = {"message": error_body}

            logger.error(f"GitHub API error ({e.code}): {error_data.get('message', 'Unknown error')}")
            return False, error_data

        except Exception as e:
            logger.error(f"Error making GitHub API request: {e}")
            return False, {"message": str(e)}

    def get_user(self) -> tuple[bool, dict[str, Any]]:
        """Get authenticated user information"""
        return self._make_request("GET", "/user")

    def create_repo(self, name: str, description: str = "", private: bool = None,
                  auto_init: bool = None, license_template: str = None) -> tuple[bool, dict[str, Any]]:
        """Create a new GitHub repository"""
        # Use config defaults if not specified
        if private is None:
            private = self.config.get("default_visibility", "private") == "private"

        if auto_init is None:
            auto_init = self.config.get("auto_init", True)

        if license_template is None and self.config.get("default_license"):
            license_template = self.config.get("default_license")

        # Prepare request data
        data = {
            "name": name,
            "private": private,
            "auto_init": auto_init
        }

        if description:
            data["description"] = description

        if license_template:
            data["license_template"] = license_template

        return self._make_request("POST", "/user/repos", data)

    def list_repos(self, username: str = None, type: str = "all") -> tuple[bool, list[dict[str, Any]]]:
        """List repositories for a user"""
        if not username:
            username = self.config.get("username", "")
            if not username:
                # Use authenticated user
                return self._make_request("GET", "/user/repos")

        return self._make_request("GET", f"/users/{username}/repos?type={type}")

    def get_repo(self, owner: str, repo: str) -> tuple[bool, dict[str, Any]]:
        """Get repository information"""
        return self._make_request("GET", f"/repos/{owner}/{repo}")

    def create_issue(self, owner: str, repo: str, title: str, body: str = "",
                   labels: list[str] = None) -> tuple[bool, dict[str, Any]]:
        """Create a new issue"""
        data = {
            "title": title,
            "body": body
        }

        if labels:
            data["labels"] = labels

        return self._make_request("POST", f"/repos/{owner}/{repo}/issues", data)

    def list_issues(self, owner: str, repo: str, state: str = "open") -> tuple[bool, list[dict[str, Any]]]:
        """List issues in a repository"""
        return self._make_request("GET", f"/repos/{owner}/{repo}/issues?state={state}")

    def create_pull_request(self, owner: str, repo: str, title: str, head: str,
                         base: str = "main", body: str = "") -> tuple[bool, dict[str, Any]]:
        """Create a pull request"""
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }

        return self._make_request("POST", f"/repos/{owner}/{repo}/pulls", data)

    def list_branches(self, owner: str, repo: str) -> tuple[bool, list[dict[str, Any]]]:
        """List branches in a repository"""
        return self._make_request("GET", f"/repos/{owner}/{repo}/branches")

    def get_rate_limit(self) -> tuple[bool, dict[str, Any]]:
        """Get API rate limit information"""
        return self._make_request("GET", "/rate_limit")

    def create_gist(self, description: str, files: dict[str, str], public: bool = False) -> tuple[bool, dict[str, Any]]:
        """Create a new gist"""
        # Format files for API
        formatted_files = {}
        for name, content in files.items():
            formatted_files[name] = {"content": content}

        data = {
            "description": description,
            "public": public,
            "files": formatted_files
        }

        return self._make_request("POST", "/gists", data)

    def list_gists(self) -> tuple[bool, list[dict[str, Any]]]:
        """List user's gists"""
        return self._make_request("GET", "/gists")

class RepositoryManager:
    """Manages Git repositories and GitHub integration"""

    def __init__(self, config_dir: str = "~/.triad/repos"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)

        self.repos_file = os.path.join(self.config_dir, "repos.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")

        # Default settings
        self.default_settings = {
            "default_clone_dir": os.path.expanduser("~/Projects"),
            "track_remote_changes": True,
            "auto_fetch_interval": 30,  # minutes
            "use_ssh_keys": True,
            "git_username": "",
            "git_email": ""
        }

        # Load settings and repos
        self.settings = self._load_settings()
        self.repos = self._load_repos()

        # Create GitHub API
        self.github = GitHubAPI()

        # Check git installation
        self._check_git()

    def _check_git(self) -> None:
        """Check Git installation and configure if needed"""
        if not GitCommand.is_git_installed():
            logger.warning("Git is not installed or not in PATH")
            return

        # Configure Git globally if needed
        if self.settings["git_username"] and self.settings["git_email"]:
            # Check if already configured
            success, stdout, _ = GitCommand.run(["config", "--global", "user.name"])

            if not success or not stdout:
                GitCommand.run(["config", "--global", "user.name", self.settings["git_username"]])

            success, stdout, _ = GitCommand.run(["config", "--global", "user.email"])

            if not success or not stdout:
                GitCommand.run(["config", "--global", "user.email", self.settings["git_email"]])

    def _load_settings(self) -> dict[str, Any]:
        """Load repository manager settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file) as f:
                    settings = json.load(f)

                # Update with any missing default values
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value

                return settings
            except Exception as e:
                logger.error(f"Error loading repository settings: {e}")

        return dict(self.default_settings)

    def save_settings(self) -> None:
        """Save repository manager settings"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving repository settings: {e}")

    def update_settings(self, key: str, value: Any) -> bool:
        """Update a settings value"""
        if key in self.settings:
            self.settings[key] = value
            self.save_settings()
            return True
        return False

    def _load_repos(self) -> dict[str, dict[str, Any]]:
        """Load tracked repositories"""
        if os.path.exists(self.repos_file):
            try:
                with open(self.repos_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading repositories: {e}")

        return {}

    def save_repos(self) -> None:
        """Save tracked repositories"""
        try:
            with open(self.repos_file, 'w') as f:
                json.dump(self.repos, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving repositories: {e}")

    def add_repo(self, path: str, name: str = None) -> bool:
        """Add a repository to tracked repos"""
        path = os.path.abspath(os.path.expanduser(path))

        # Check if directory exists and is a Git repo
        if not os.path.isdir(path) or not GitCommand.is_repo(path):
            return False

        # Get repo name from directory if not specified
        if not name:
            name = os.path.basename(path)

        # Get repo details
        remote_url = GitCommand.get_remote_url(path)
        current_branch = GitCommand.get_current_branch(path)

        # Get GitHub owner/repo if this is a GitHub repository
        github_info = self._extract_github_info(remote_url) if remote_url else None

        # Add to repos
        self.repos[name] = {
            "path": path,
            "remote_url": remote_url,
            "added_at": time.time(),
            "last_fetched": time.time(),
            "default_branch": current_branch,
            "github_info": github_info
        }

        self.save_repos()
        return True

    def remove_repo(self, name: str) -> bool:
        """Remove a repository from tracking"""
        if name in self.repos:
            del self.repos[name]
            self.save_repos()
            return True
        return False

    def get_repos(self) -> dict[str, dict[str, Any]]:
        """Get all tracked repositories"""
        return dict(self.repos)

    def get_repo(self, name: str) -> dict[str, Any] | None:
        """Get a specific repository"""
        return self.repos.get(name)

    def clone_repo(self, url: str, directory: str = None, name: str = None) -> tuple[bool, str]:
        """Clone a repository"""
        if not directory:
            # Use default clone directory
            directory = self.settings["default_clone_dir"]

        # Create directory if it doesn't exist
        os.makedirs(os.path.expanduser(directory), exist_ok=True)

        # Extract repo name from URL if not specified
        if not name:
            name = self._extract_repo_name(url)

        # Build target path
        target_path = os.path.join(os.path.expanduser(directory), name)

        # Check if directory already exists
        if os.path.exists(target_path):
            return False, f"Directory already exists: {target_path}"

        # Clone the repository
        success, stdout, stderr = GitCommand.run(["clone", url, target_path])

        if success:
            # Add to tracked repos
            self.add_repo(target_path, name)
            return True, f"Repository cloned to {target_path}"
        else:
            return False, stderr

    def create_repo(self, path: str, name: str = None, remote: bool = False,
                  description: str = "", private: bool = None) -> tuple[bool, str]:
        """Create a new repository"""
        # Handle name
        if not name:
            name = os.path.basename(os.path.abspath(path))

        # Create local directory if it doesn't exist
        path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(path, exist_ok=True)

        # Initialize git repository
        success, _, stderr = GitCommand.run(["init"], path)

        if not success:
            return False, f"Failed to initialize repository: {stderr}"

        # Create README.md if it doesn't exist
        readme_path = os.path.join(path, "README.md")
        if not os.path.exists(readme_path):
            try:
                with open(readme_path, 'w') as f:
                    f.write(f"# {name}\n\n{description}\n")

                # Add and commit README
                GitCommand.run(["add", "README.md"], path)
                GitCommand.run(["commit", "-m", "Initial commit with README"], path)
            except Exception as e:
                logger.error(f"Error creating README: {e}")

        # Create remote repository on GitHub if requested
        if remote:
            if not self.github.token:
                return False, "GitHub token not set. Cannot create remote repository"

            success, response = self.github.create_repo(
                name=name,
                description=description,
                private=private
            )

            if not success:
                return False, f"Failed to create GitHub repository: {response.get('message', 'Unknown error')}"

            # Add remote
            remote_url = response.get("ssh_url" if self.settings["use_ssh_keys"] else "clone_url")
            GitCommand.run(["remote", "add", "origin", remote_url], path)

            # Push to remote
            push_success, _, push_error = GitCommand.run(["push", "-u", "origin", "main"], path)

            if not push_success:
                # Try pushing to master if main fails
                GitCommand.run(["push", "-u", "origin", "master"], path)

        # Add to tracked repos
        self.add_repo(path, name)

        return True, f"Repository created at {path}"

    def get_repo_status(self, name: str) -> tuple[bool, dict[str, Any]]:
        """Get detailed status of a repository"""
        repo = self.repos.get(name)
        if not repo:
            return False, {"error": "Repository not found"}

        path = repo["path"]

        # Check if directory exists
        if not os.path.isdir(path):
            return False, {"error": "Repository directory not found"}

        # Get current branch
        branch_success, branch, _ = GitCommand.run(["branch", "--show-current"], path)
        current_branch = branch if branch_success else "unknown"

        # Get status
        status_success, status_output, _ = GitCommand.run(["status", "--porcelain"], path)

        # Parse status output
        modified_files = []
        staged_files = []
        untracked_files = []

        if status_success:
            for line in status_output.splitlines():
                if line:
                    status = line[:2]
                    filename = line[3:]

                    if status.startswith('?'):
                        untracked_files.append(filename)
                    elif status.startswith('M'):
                        modified_files.append(filename)
                    elif status[0] in ['A', 'M', 'D', 'R', 'C']:
                        staged_files.append(filename)

        # Get last commit
        commit_success, commit_output, _ = GitCommand.run(["log", "-1", "--oneline"], path)
        last_commit = commit_output if commit_success else "No commits yet"

        # Get number of commits ahead/behind
        ahead_behind = {}
        if repo.get("remote_url"):
            ahead_behind_success, ahead_behind_output, _ = GitCommand.run(
                ["rev-list", "--left-right", "--count", f"{current_branch}...origin/{current_branch}"],
                path
            )

            if ahead_behind_success:
                parts = ahead_behind_output.split()
                if len(parts) == 2:
                    ahead_behind = {"ahead": parts[0], "behind": parts[1]}

        # Build result
        result = {
            "name": name,
            "path": path,
            "current_branch": current_branch,
            "remote_url": repo.get("remote_url"),
            "last_commit": last_commit,
            "status": {
                "clean": not (modified_files or staged_files or untracked_files),
                "staged_files": staged_files,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
                "ahead_behind": ahead_behind
            }
        }

        # Add GitHub info if available
        if repo.get("github_info"):
            result["github_info"] = repo["github_info"]

        return True, result

    def pull_repo(self, name: str) -> tuple[bool, str]:
        """Pull latest changes from remote"""
        repo = self.repos.get(name)
        if not repo:
            return False, "Repository not found"

        path = repo["path"]

        # Check if directory exists
        if not os.path.isdir(path):
            return False, "Repository directory not found"

        # Pull from remote
        success, stdout, stderr = GitCommand.run(["pull"], path)

        if success:
            return True, stdout or "Pull successful"
        else:
            return False, stderr or "Pull failed"

    def push_repo(self, name: str, force: bool = False) -> tuple[bool, str]:
        """Push local changes to remote"""
        repo = self.repos.get(name)
        if not repo:
            return False, "Repository not found"

        path = repo["path"]

        # Check if directory exists
        if not os.path.isdir(path):
            return False, "Repository directory not found"

        # Get current branch
        branch_success, branch, _ = GitCommand.run(["branch", "--show-current"], path)
        current_branch = branch if branch_success else "main"

        # Push to remote
        push_args = ["push"]
        if force:
            push_args.append("--force")

        push_args.extend(["origin", current_branch])

        success, stdout, stderr = GitCommand.run(push_args, path)

        if success:
            return True, stdout or "Push successful"
        else:
            return False, stderr or "Push failed"

    def commit_changes(self, name: str, message: str, add_all: bool = False) -> tuple[bool, str]:
        """Commit changes to repository"""
        repo = self.repos.get(name)
        if not repo:
            return False, "Repository not found"

        path = repo["path"]

        # Check if directory exists
        if not os.path.isdir(path):
            return False, "Repository directory not found"

        # Add files if requested
        if add_all:
            add_success, _, add_error = GitCommand.run(["add", "--all"], path)
            if not add_success:
                return False, f"Failed to add files: {add_error}"

        # Commit changes
        commit_success, commit_output, commit_error = GitCommand.run(
            ["commit", "-m", message],
            path
        )

        if commit_success:
            return True, commit_output or "Changes committed successfully"
        else:
            return False, commit_error or "Commit failed"

    def create_branch(self, name: str, branch_name: str, checkout: bool = True) -> tuple[bool, str]:
        """Create a new branch in repository"""
        repo = self.repos.get(name)
        if not repo:
            return False, "Repository not found"

        path = repo["path"]

        # Check if directory exists
        if not os.path.isdir(path):
            return False, "Repository directory not found"

        # Create branch
        branch_args = ["branch", branch_name]
        success, stdout, stderr = GitCommand.run(branch_args, path)

        if not success:
            return False, stderr or f"Failed to create branch {branch_name}"

        # Checkout the branch if requested
        if checkout:
            checkout_success, _, checkout_error = GitCommand.run(
                ["checkout", branch_name],
                path
            )

            if not checkout_success:
                return False, checkout_error or f"Created branch but failed to checkout {branch_name}"

        return True, f"Branch {branch_name} created successfully"

    def list_branches(self, name: str) -> tuple[bool, list[dict[str, Any]]]:
        """List branches in repository"""
        repo = self.repos.get(name)
        if not repo:
            return False, []

        path = repo["path"]

        # Check if directory exists
        if not os.path.isdir(path):
            return False, []

        # Get branches
        success, stdout, _ = GitCommand.run(["branch", "-a"], path)

        if not success:
            return False, []

        branches = []
        current_branch = ""

        # Parse branch output
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            is_current = False
            if line.startswith('*'):
                is_current = True
                line = line[1:].strip()
                current_branch = line

            is_remote = line.startswith('remotes/')
            branch_name = line.replace('remotes/origin/', '', 1) if is_remote else line

            branches.append({
                "name": branch_name,
                "is_current": is_current,
                "is_remote": is_remote
            })

        return True, branches

    def checkout_branch(self, name: str, branch: str, create: bool = False) -> tuple[bool, str]:
        """Checkout a branch in repository"""
        repo = self.repos.get(name)
        if not repo:
            return False, "Repository not found"

        path = repo["path"]

        # Check if directory exists
        if not os.path.isdir(path):
            return False, "Repository directory not found"

        # Build checkout command
        checkout_args = ["checkout"]
        if create:
            checkout_args.append("-b")
        checkout_args.append(branch)

        # Run checkout
        success, stdout, stderr = GitCommand.run(checkout_args, path)

        if success:
            return True, stdout or f"Switched to branch '{branch}'"
        else:
            return False, stderr or f"Failed to checkout branch {branch}"

    def create_github_issue(self, name: str, title: str, body: str = "",
                          labels: list[str] = None) -> tuple[bool, dict[str, Any]]:
        """Create a GitHub issue for the repository"""
        repo = self.repos.get(name)
        if not repo:
            return False, {"error": "Repository not found"}

        # Check if we have GitHub info
        github_info = repo.get("github_info")
        if not github_info:
            return False, {"error": "Not a GitHub repository"}

        # Create issue
        success, response = self.github.create_issue(
            github_info["owner"],
            github_info["repo"],
            title,
            body,
            labels
        )

        if success:
            return True, response
        else:
            return False, {"error": response.get("message", "Failed to create issue")}

    def create_pull_request(self, name: str, title: str, head: str = None,
                          base: str = "main", body: str = "") -> tuple[bool, dict[str, Any]]:
        """Create a GitHub pull request for the repository"""
        repo = self.repos.get(name)
        if not repo:
            return False, {"error": "Repository not found"}

        # Check if we have GitHub info
        github_info = repo.get("github_info")
        if not github_info:
            return False, {"error": "Not a GitHub repository"}

        # Use current branch if head not specified
        if not head:
            success, stdout, _ = GitCommand.run(["branch", "--show-current"], repo["path"])
            if not success:
                return False, {"error": "Failed to get current branch"}
            head = stdout

        # Create pull request
        success, response = self.github.create_pull_request(
            github_info["owner"],
            github_info["repo"],
            title,
            head,
            base,
            body
        )

        if success:
            return True, response
        else:
            return False, {"error": response.get("message", "Failed to create pull request")}

    def _extract_github_info(self, url: str) -> dict[str, str] | None:
        """Extract GitHub owner and repo from URL"""
        if not url:
            return None

        # Try to match GitHub URL patterns
        patterns = [
            r"git@github\.com:([^/]+)/([^/.]+)\.git",  # SSH format
            r"https://github\.com/([^/]+)/([^/.]+)\.git",  # HTTPS format
            r"https://github\.com/([^/]+)/([^/.]+)",  # Web URL format
        ]

        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                return {
                    "owner": match.group(1),
                    "repo": match.group(2)
                }

        return None

    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL"""
        # Try to extract from GitHub URL
        github_info = self._extract_github_info(url)
        if github_info:
            return github_info["repo"]

        # Fallback: extract from end of URL
        name = url.rstrip('/').split('/')[-1]

        # Remove .git suffix if present
        if name.endswith('.git'):
            name = name[:-4]

        return name

def main():
    """CLI interface for repository management"""
    import argparse

    parser = argparse.ArgumentParser(description="Triad Terminal Repository Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new repository")
    init_parser.add_argument("path", help="Path for the new repository")
    init_parser.add_argument("--name", help="Repository name (defaults to directory name)")
    init_parser.add_argument("--remote", action="store_true", help="Create remote GitHub repository")
    init_parser.add_argument("--description", help="Repository description")
    init_parser.add_argument("--private", action="store_true", help="Make GitHub repository private")

    # Clone command
    clone_parser = subparsers.add_parser("clone", help="Clone a repository")
    clone_parser.add_argument("url", help="Repository URL to clone")
    clone_parser.add_argument("--dir", help="Target directory")
    clone_parser.add_argument("--name", help="Repository name (defaults to URL basename)")

    # List command
    subparsers.add_parser("list", help="List tracked repositories")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show repository status")
    status_parser.add_argument("name", help="Repository name")

    # Pull command
    pull_parser = subparsers.add_parser("pull", help="Pull latest changes")
    pull_parser.add_argument("name", help="Repository name")

    # Push command
    push_parser = subparsers.add_parser("push", help="Push changes to remote")
    push_parser.add_argument("name", help="Repository name")
    push_parser.add_argument("--force", "-f", action="store_true", help="Force push")

    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Commit changes")
    commit_parser.add_argument("name", help="Repository name")
    commit_parser.add_argument("message", help="Commit message")
    commit_parser.add_argument("--all", "-a", action="store_true", help="Add all changes")

    # Branch command
    branch_parser = subparsers.add_parser("branch", help="Create a new branch")
    branch_parser.add_argument("name", help="Repository name")
    branch_parser.add_argument("branch", help="Branch name")
    branch_parser.add_argument("--no-checkout", action="store_true", help="Don't checkout the new branch")

    # Checkout command
    checkout_parser = subparsers.add_parser("checkout", help="Checkout a branch")
    checkout_parser.add_argument("name", help="Repository name")
    checkout_parser.add_argument("branch", help="Branch name")
    checkout_parser.add_argument("--create", "-b", action="store_true", help="Create and checkout the branch")

    # Issue command
    issue_parser = subparsers.add_parser("issue", help="Create a GitHub issue")
    issue_parser.add_argument("name", help="Repository name")
    issue_parser.add_argument("title", help="Issue title")
    issue_parser.add_argument("--body", help="Issue description")
    issue_parser.add_argument("--labels", help="Comma-separated list of labels")

    # PR command
    pr_parser = subparsers.add_parser("pr", help="Create a GitHub pull request")
    pr_parser.add_argument("name", help="Repository name")
    pr_parser.add_argument("title", help="PR title")
    pr_parser.add_argument("--head", help="Source branch (defaults to current)")
    pr_parser.add_argument("--base", default="main", help="Target branch")
    pr_parser.add_argument("--body", help="PR description")

    # GitHub auth command
    auth_parser = subparsers.add_parser("auth", help="Set GitHub authentication token")
    auth_parser.add_argument("token", nargs="?", help="GitHub personal access token")

    # Config command
    config_parser = subparsers.add_parser("config", help="Set configuration options")
    config_parser.add_argument("--username", help="Set Git username")
    config_parser.add_argument("--email", help="Set Git email")
    config_parser.add_argument("--gh-username", help="Set GitHub username")
    config_parser.add_argument("--clone-dir", help="Set default clone directory")
    config_parser.add_argument("--use-ssh", action="store_true", help="Use SSH for GitHub")
    config_parser.add_argument("--use-https", action="store_true", help="Use HTTPS for GitHub")

    args = parser.parse_args()

    # Initialize repository manager
    manager = RepositoryManager()

    # Execute the appropriate command
    try:
        if args.command == "init":
            success, message = manager.create_repo(
                args.path,
                args.name,
                args.remote,
                args.description,
                args.private
            )

            print(f"{'✅' if success else '❌'} {message}")

        elif args.command == "clone":
            success, message = manager.clone_repo(
                args.url,
                args.dir,
                args.name
            )

            print(f"{'✅' if success else '❌'} {message}")

        elif args.command == "list":
            repos = manager.get_repos()

            if repos:
                print(f"Tracked repositories ({len(repos)}):")
                for name, repo in repos.items():
                    branch = repo.get("default_branch", "")
                    path = repo.get("path", "")
                    print(f"  {name} ({branch}) - {path}")
            else:
                print("No repositories tracked. Use 'init' or 'clone' to add repositories.")

        elif args.command == "status":
            success, status = manager.get_repo_status(args.name)

            if success:
                print(f"Repository: {status['name']}")
                print(f"Path: {status['path']}")
                print(f"Branch: {status['current_branch']}")

                if status.get("remote_url"):
                    print(f"Remote: {status['remote_url']}")

                if status.get("github_info"):
                    github_info = status["github_info"]
                    print(f"GitHub: {github_info['owner']}/{github_info['repo']}")

                print(f"Last commit: {status['last_commit']}")

                # Status information
                repo_status = status["status"]
                if repo_status["clean"]:
                    print("Status: Clean")
                else:
                    print("Status: Dirty")

                    if repo_status["staged_files"]:
                        print("Staged files:")
                        for file in repo_status["staged_files"]:
                            print(f"  {file}")

                    if repo_status["modified_files"]:
                        print("Modified files:")
                        for file in repo_status["modified_files"]:
                            print(f"  {file}")

                    if repo_status["untracked_files"]:
                        print("Untracked files:")
                        for file in repo_status["untracked_files"]:
                            print(f"  {file}")

                # Ahead/behind information
                ahead_behind = repo_status.get("ahead_behind", {})
                if ahead_behind:
                    print(f"Commits ahead: {ahead_behind.get('ahead', 0)}")
                    print(f"Commits behind: {ahead_behind.get('behind', 0)}")
            else:
                print(f"❌ {status.get('error', 'Unknown error')}")

        elif args.command == "pull":
            success, message = manager.pull_repo(args.name)
            print(f"{'✅' if success else '❌'} {message}")

        elif args.command == "push":
            success, message = manager.push_repo(args.name, args.force)
            print(f"{'✅' if success else '❌'} {message}")

        elif args.command == "commit":
            success, message = manager.commit_changes(args.name, args.message, args.all)
            print(f"{'✅' if success else '❌'} {message}")

        elif args.command == "branch":
            success, message = manager.create_branch(args.name, args.branch, not args.no_checkout)
            print(f"{'✅' if success else '❌'} {message}")

        elif args.command == "checkout":
            success, message = manager.checkout_branch(args.name, args.branch, args.create)
            print(f"{'✅' if success else '❌'} {message}")

        elif args.command == "issue":
            labels = args.labels.split(",") if args.labels else None
            success, response = manager.create_github_issue(args.name, args.title, args.body, labels)

            if success:
                print(f"✅ Issue created: #{response['number']}")
                print(f"URL: {response['html_url']}")
            else:
                print(f"❌ {response.get('error', 'Unknown error')}")

        elif args.command == "pr":
            success, response = manager.create_pull_request(
                args.name, args.title, args.head, args.base, args.body
            )

            if success:
                print(f"✅ Pull request created: #{response['number']}")
                print(f"URL: {response['html_url']}")
            else:
                print(f"❌ {response.get('error', 'Unknown error')}")

        elif args.command == "auth":
            if args.token:
                manager.github.save_token(args.token)
                print("✅ GitHub token saved")

                # Test the token
                success, user_info = manager.github.get_user()
                if success:
                    print(f"Authenticated as: {user_info['login']}")
                else:
                    print(f"❌ Token validation failed: {user_info.get('message', 'Unknown error')}")
            else:
                # Interactive token input
                import getpass
                token = getpass.getpass("Enter GitHub personal access token: ")

                if token:
                    manager.github.save_token(token)
                    print("✅ GitHub token saved")
                else:
                    print("No token provided")

        elif args.command == "config":
            changes_made = False

            if args.username:
                manager.settings["git_username"] = args.username
                changes_made = True
                print(f"Git username set to: {args.username}")

            if args.email:
                manager.settings["git_email"] = args.email
                changes_made = True
                print(f"Git email set to: {args.email}")

            if args.gh_username:
                manager.github.set_username(args.gh_username)
                print(f"GitHub username set to: {args.gh_username}")

            if args.clone_dir:
                manager.settings["default_clone_dir"] = os.path.expanduser(args.clone_dir)
                changes_made = True
                print(f"Default clone directory set to: {args.clone_dir}")

            if args.use_ssh:
                manager.settings["use_ssh_keys"] = True
                changes_made = True
                print("Using SSH for GitHub repositories")

            if args.use_https:
                manager.settings["use_ssh_keys"] = False
                changes_made = True
                print("Using HTTPS for GitHub repositories")

            if changes_made:
                manager.save_settings()

        else:
            print("Please specify a command. Use --help for usage information.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
