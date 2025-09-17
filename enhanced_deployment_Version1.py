#!/usr/bin/env python3

"""
Triad Terminal Enhanced Deployment System
Provides streamlined deployment workflows across multiple platforms
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import yaml

logger = logging.getLogger("triad.deployment")


@dataclass
class DeploymentTarget:
    """Configuration for a deployment target"""

    name: str
    type: str  # "vercel", "netlify", "aws", "gcp", "azure", "heroku", "custom"
    config: dict[str, Any]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "DeploymentTarget":
        return DeploymentTarget(
            name=data.get("name", "unnamed"),
            type=data.get("type", "custom"),
            config=data.get("config", {}),
        )


class DeploymentManager:
    """Manages deployment configurations and processes"""

    def __init__(self, config_dir: str = "~/.triad/deployment"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.targets_file = os.path.join(self.config_dir, "targets.yml")
        self.history_file = os.path.join(self.config_dir, "history.json")
        self._targets = None

    def get_targets(self) -> dict[str, DeploymentTarget]:
        """Get all configured deployment targets"""
        if self._targets is not None:
            return self._targets

        self._targets = {}

        # Load targets from file
        if os.path.exists(self.targets_file):
            try:
                with open(self.targets_file) as f:
                    data = yaml.safe_load(f) or {}

                for name, target_data in data.items():
                    target_data["name"] = name  # Ensure name is in the data
                    self._targets[name] = DeploymentTarget.from_dict(target_data)
            except Exception as e:
                logger.error(f"Error loading deployment targets: {e}")

        return self._targets

    def save_targets(self) -> bool:
        """Save deployment targets to file"""
        if self._targets is None:
            return True  # Nothing to save

        try:
            data = {}
            for name, target in self._targets.items():
                data[name] = {"type": target.type, "config": target.config}

            with open(self.targets_file, "w") as f:
                yaml.dump(data, f)

            return True
        except Exception as e:
            logger.error(f"Error saving deployment targets: {e}")
            return False

    def add_target(self, target: DeploymentTarget) -> bool:
        """Add a new deployment target"""
        targets = self.get_targets()
        targets[target.name] = target
        self._targets = targets
        return self.save_targets()

    def remove_target(self, name: str) -> bool:
        """Remove a deployment target"""
        targets = self.get_targets()
        if name in targets:
            del targets[name]
            self._targets = targets
            return self.save_targets()
        return False

    def log_deployment(self, target_name: str, status: str, details: dict[str, Any] = None) -> None:
        """Log a deployment to history"""
        history = []

        # Load existing history
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file) as f:
                    history = json.load(f)
            except:
                history = []

        # Add new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "target": target_name,
            "status": status,
            "details": details or {},
        }

        history.append(entry)

        # Save history (keep last 100 entries)
        with open(self.history_file, "w") as f:
            json.dump(history[-100:], f, indent=2)

    def get_deployment_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent deployment history"""
        if not os.path.exists(self.history_file):
            return []

        try:
            with open(self.history_file) as f:
                history = json.load(f)

            # Return most recent entries first
            return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Error loading deployment history: {e}")
            return []


class DeploymentExecutor:
    """Execute deployments to various platforms"""

    @staticmethod
    async def deploy_to_vercel(project_dir: str, config: dict[str, Any]) -> dict[str, Any]:
        """Deploy to Vercel"""
        result = {"success": False, "url": None, "output": "", "error": None}

        try:
            logger.info(f"Deploying {project_dir} to Vercel")

            # Ensure Vercel CLI is installed
            try:
                process = await asyncio.create_subprocess_exec(
                    "vercel",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    logger.warning("Vercel CLI not installed, attempting to install")
                    npm_process = await asyncio.create_subprocess_exec(
                        "npm",
                        "install",
                        "-g",
                        "vercel",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await npm_process.communicate()
            except:
                result["error"] = "Vercel CLI not installed and could not be installed"
                return result

            # Prepare command arguments
            cmd = ["vercel"]

            # Add options from config
            if config.get("production", False):
                cmd.append("--prod")

            if "token" in config:
                cmd.extend(["--token", config["token"]])

            if "team" in config:
                cmd.extend(["--scope", config["team"]])

            # Add yes flag to skip confirmation
            cmd.append("--yes")

            # Execute deployment
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""

            result["output"] = stdout_str + stderr_str

            if process.returncode == 0:
                result["success"] = True

                # Try to extract the deployment URL
                for line in stdout_str.split("\n"):
                    if "https://" in line and "vercel.app" in line:
                        result["url"] = line.strip()
                        break
            else:
                result["error"] = f"Deployment failed with code {process.returncode}"

            return result

        except Exception as e:
            logger.error(f"Error during Vercel deployment: {e}")
            result["error"] = str(e)
            return result

    @staticmethod
    async def deploy_to_netlify(project_dir: str, config: dict[str, Any]) -> dict[str, Any]:
        """Deploy to Netlify"""
        result = {"success": False, "url": None, "output": "", "error": None}

        try:
            logger.info(f"Deploying {project_dir} to Netlify")

            # Ensure Netlify CLI is installed
            try:
                process = await asyncio.create_subprocess_exec(
                    "netlify",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    logger.warning("Netlify CLI not installed, attempting to install")
                    npm_process = await asyncio.create_subprocess_exec(
                        "npm",
                        "install",
                        "-g",
                        "netlify-cli",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await npm_process.communicate()
            except:
                result["error"] = "Netlify CLI not installed and could not be installed"
                return result

            # Prepare command arguments
            cmd = ["netlify", "deploy"]

            # Add build command if specified
            if "build_command" in config:
                # Run build command first
                build_cmd = config["build_command"].split()
                build_process = await asyncio.create_subprocess_exec(
                    *build_cmd,
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                build_stdout, build_stderr = await build_process.communicate()

                if build_process.returncode != 0:
                    result["error"] = (
                        f"Build failed: {build_stderr.decode() if build_stderr else 'unknown error'}"
                    )
                    return result

            # Set publish directory
            if "publish_dir" in config:
                cmd.extend(["--dir", config["publish_dir"]])
            else:
                cmd.extend(["--dir", "."])  # Default to project directory

            # Production flag
            if config.get("production", False):
                cmd.append("--prod")

            if "site_id" in config:
                cmd.extend(["--site", config["site_id"]])

            # Add auth token if provided
            if "token" in config:
                cmd.extend(["--auth", config["token"]])

            # Execute deployment
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""

            result["output"] = stdout_str + stderr_str

            if process.returncode == 0:
                result["success"] = True

                # Try to extract the deployment URL
                for line in stdout_str.split("\n"):
                    if "Website URL:" in line or "Unique Deploy URL:" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            result["url"] = parts[1].strip()
                            break
            else:
                result["error"] = f"Deployment failed with code {process.returncode}"

            return result

        except Exception as e:
            logger.error(f"Error during Netlify deployment: {e}")
            result["error"] = str(e)
            return result

    @staticmethod
    async def deploy_to_aws(project_dir: str, config: dict[str, Any]) -> dict[str, Any]:
        """Deploy to AWS (S3, Lambda, etc.)"""
        result = {"success": False, "url": None, "output": "", "error": None}

        try:
            logger.info(f"Deploying {project_dir} to AWS")

            # Check AWS CLI
            try:
                process = await asyncio.create_subprocess_exec(
                    "aws",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()

                if process.returncode != 0:
                    result["error"] = "AWS CLI not installed"
                    return result
            except:
                result["error"] = "AWS CLI not installed"
                return result

            # Determine deployment type
            aws_type = config.get("aws_type", "s3")

            if aws_type == "s3":
                # Deploy to S3 bucket
                bucket = config.get("bucket")
                if not bucket:
                    result["error"] = "No S3 bucket specified"
                    return result

                # Sync to S3
                cmd = [
                    "aws",
                    "s3",
                    "sync",
                    config.get("local_dir", "."),  # Source directory (default: project root)
                    f"s3://{bucket}",  # Destination bucket
                    "--delete",  # Remove files that don't exist locally
                ]

                if config.get("public", False):
                    cmd.append("--acl")
                    cmd.append("public-read")

                # Execute sync command
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode() if stdout else ""
                stderr_str = stderr.decode() if stderr else ""

                result["output"] = stdout_str + stderr_str

                if process.returncode == 0:
                    result["success"] = True
                    region = config.get("region", "us-east-1")
                    result["url"] = f"http://{bucket}.s3-website-{region}.amazonaws.com"
                else:
                    result["error"] = f"S3 deployment failed: {stderr_str}"

            elif aws_type == "cloudformation":
                # Deploy using CloudFormation
                stack_name = config.get("stack_name")
                template = config.get("template")

                if not stack_name or not template:
                    result["error"] = "Missing stack_name or template for CloudFormation deployment"
                    return result

                cmd = [
                    "aws",
                    "cloudformation",
                    "deploy",
                    "--template-file",
                    template,
                    "--stack-name",
                    stack_name,
                ]

                # Add parameters if specified
                if "parameters" in config:
                    param_str = []
                    for key, value in config["parameters"].items():
                        param_str.append(f"{key}={value}")

                    if param_str:
                        cmd.extend(["--parameter-overrides", " ".join(param_str)])

                # Add capabilities if needed
                if "capabilities" in config:
                    cmd.extend(["--capabilities", config["capabilities"]])

                # Execute CloudFormation deployment
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode() if stdout else ""
                stderr_str = stderr.decode() if stderr else ""

                result["output"] = stdout_str + stderr_str

                if process.returncode == 0:
                    result["success"] = True
                    result["url"] = f"CloudFormation stack {stack_name} deployed"
                else:
                    result["error"] = f"CloudFormation deployment failed: {stderr_str}"

            elif aws_type == "lambda":
                # Deploy to AWS Lambda
                function_name = config.get("function_name")
                if not function_name:
                    result["error"] = "No function_name specified for Lambda deployment"
                    return result

                # Build the deployment package
                zip_file = os.path.join(project_dir, f"{function_name}.zip")

                # Create zip file
                zip_cmd = ["zip", "-r", zip_file, ".", "-x", "*.git*", "-x", "*.zip"]

                if "exclude" in config:
                    for exclude in config["exclude"]:
                        zip_cmd.extend(["-x", exclude])

                # Execute zip command
                zip_process = await asyncio.create_subprocess_exec(
                    *zip_cmd,
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                zip_stdout, zip_stderr = await zip_process.communicate()

                if zip_process.returncode != 0:
                    result["error"] = (
                        f"Failed to create deployment package: {zip_stderr.decode() if zip_stderr else 'unknown error'}"
                    )
                    return result

                # Deploy to Lambda
                cmd = [
                    "aws",
                    "lambda",
                    "update-function-code",
                    "--function-name",
                    function_name,
                    "--zip-file",
                    f"fileb://{zip_file}",
                ]

                # Execute Lambda deployment
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode() if stdout else ""
                stderr_str = stderr.decode() if stderr else ""

                result["output"] = stdout_str + stderr_str

                if process.returncode == 0:
                    result["success"] = True
                    result["url"] = f"Lambda function {function_name} updated"

                    # Clean up zip file
                    if os.path.exists(zip_file):
                        os.remove(zip_file)
                else:
                    result["error"] = f"Lambda deployment failed: {stderr_str}"

            else:
                result["error"] = f"Unsupported AWS deployment type: {aws_type}"

            return result

        except Exception as e:
            logger.error(f"Error during AWS deployment: {e}")
            result["error"] = str(e)
            return result

    @staticmethod
    async def deploy_to_custom(project_dir: str, config: dict[str, Any]) -> dict[str, Any]:
        """Deploy using custom commands"""
        result = {"success": False, "url": None, "output": "", "error": None}

        try:
            logger.info(f"Running custom deployment for {project_dir}")

            # Get the commands to run
            commands = config.get("commands", [])
            if not commands:
                result["error"] = "No commands specified for custom deployment"
                return result

            # Execute each command in sequence
            all_output = []

            for cmd_str in commands:
                logger.info(f"Running command: {cmd_str}")

                if sys.platform == "win32":
                    # Windows needs shell=True for complex commands
                    process = await asyncio.create_subprocess_shell(
                        cmd_str,
                        cwd=project_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        shell=True,
                    )
                else:
                    # For Unix, use a list of arguments for better security
                    process = await asyncio.create_subprocess_shell(
                        cmd_str,
                        cwd=project_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode() if stdout else ""
                stderr_str = stderr.decode() if stderr else ""

                all_output.append(f"Command: {cmd_str}")
                all_output.append(stdout_str)

                if stderr_str:
                    all_output.append(f"Errors: {stderr_str}")

                if process.returncode != 0:
                    result["error"] = f"Command failed with code {process.returncode}: {cmd_str}"
                    result["output"] = "\n".join(all_output)
                    return result

            result["success"] = True
            result["output"] = "\n".join(all_output)

            # Check for URL in config
            if "url" in config:
                result["url"] = config["url"]

            return result

        except Exception as e:
            logger.error(f"Error during custom deployment: {e}")
            result["error"] = str(e)
            return result


class DeploymentService:
    """Main service for managing deployments"""

    def __init__(self):
        self.manager = DeploymentManager()
        self.executor = DeploymentExecutor()

    async def deploy(self, project_dir: str, target_name: str) -> dict[str, Any]:
        """Deploy a project to a specified target"""
        targets = self.manager.get_targets()

        if target_name not in targets:
            return {"success": False, "error": f"Target '{target_name}' not found"}

        target = targets[target_name]

        logger.info(f"Starting deployment to {target.name} ({target.type})")

        # Execute deployment based on target type
        result = {}

        try:
            if target.type == "vercel":
                result = await self.executor.deploy_to_vercel(project_dir, target.config)
            elif target.type == "netlify":
                result = await self.executor.deploy_to_netlify(project_dir, target.config)
            elif target.type == "aws":
                result = await self.executor.deploy_to_aws(project_dir, target.config)
            elif target.type == "custom":
                result = await self.executor.deploy_to_custom(project_dir, target.config)
            else:
                result = {"success": False, "error": f"Unsupported deployment type: {target.type}"}
        except Exception as e:
            logger.error(f"Error during deployment: {e}")
            result = {"success": False, "error": str(e)}

        # Log the deployment
        self.manager.log_deployment(
            target_name,
            "success" if result.get("success", False) else "failed",
            {"url": result.get("url"), "error": result.get("error")},
        )

        return result


class DeploymentTemplates:
    """Provides templates for common deployment configurations"""

    @staticmethod
    def create_vercel_template(
        name: str, production: bool = False, team: str | None = None
    ) -> DeploymentTarget:
        """Create a template for Vercel deployment"""
        config = {"production": production}

        if team:
            config["team"] = team

        return DeploymentTarget(name=name, type="vercel", config=config)

    @staticmethod
    def create_netlify_template(
        name: str, site_id: str | None = None, production: bool = False, publish_dir: str = "public"
    ) -> DeploymentTarget:
        """Create a template for Netlify deployment"""
        config = {"production": production, "publish_dir": publish_dir}

        if site_id:
            config["site_id"] = site_id

        return DeploymentTarget(name=name, type="netlify", config=config)

    @staticmethod
    def create_aws_s3_template(
        name: str, bucket: str, region: str = "us-east-1", public: bool = True
    ) -> DeploymentTarget:
        """Create a template for AWS S3 deployment"""
        config = {"aws_type": "s3", "bucket": bucket, "region": region, "public": public}

        return DeploymentTarget(name=name, type="aws", config=config)
