#!/usr/bin/env python3

"""
Triad Terminal Code Formatter
Format and beautify code in various languages
"""

import logging
import os
import subprocess
import sys

logger = logging.getLogger("triad.formatter")

class CodeFormatter:
    """Format code in various languages"""

    @staticmethod
    def format_python(file_path: str, style: str = "pep8") -> tuple[bool, str]:
        """Format Python code"""
        try:
            logger.info(f"Formatting Python file: {file_path}")

            # Check if black is installed
            try:
                subprocess.run([sys.executable, "-m", "black", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Black not installed, attempting to install it")
                subprocess.run([sys.executable, "-m", "pip", "install", "black"], check=True)

            # Format with black
            result = subprocess.run(
                [sys.executable, "-m", "black", file_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Python code formatted successfully")
                return True, "Formatting successful"
            else:
                logger.warning(f"Python formatting failed: {result.stderr}")
                return False, result.stderr

        except Exception as e:
            logger.error(f"Error formatting Python code: {e}")
            return False, str(e)

    @staticmethod
    def format_javascript(file_path: str, style: str = "standard") -> tuple[bool, str]:
        """Format JavaScript/TypeScript code"""
        try:
            logger.info(f"Formatting JavaScript/TypeScript file: {file_path}")

            # Check if prettier is installed
            try:
                subprocess.run(["npx", "prettier", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Prettier not installed, attempting to install it")
                subprocess.run(["npm", "install", "--global", "prettier"], check=True)

            # Format with prettier
            result = subprocess.run(
                ["npx", "prettier", "--write", file_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("JavaScript/TypeScript code formatted successfully")
                return True, "Formatting successful"
            else:
                logger.warning(f"JavaScript/TypeScript formatting failed: {result.stderr}")
                return False, result.stderr

        except Exception as e:
            logger.error(f"Error formatting JavaScript/TypeScript code: {e}")
            return False, str(e)

    @staticmethod
    def format_code(file_path: str) -> tuple[bool, str]:
        """Format code based on file type"""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        # Determine file type by extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext in ['.py']:
            return CodeFormatter.format_python(file_path)

        elif ext in ['.js', '.jsx', '.ts', '.tsx'] or ext in ['.json'] or ext in ['.html', '.css', '.scss']:
            return CodeFormatter.format_javascript(file_path)

        else:
            return False, f"Unsupported file type: {ext}"
