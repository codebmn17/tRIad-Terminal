#!/usr/bin/env python3

"""
Triad Terminal Snippet Manager
Save, organize and reuse code snippets
"""

import datetime
import json
import logging
import os
from typing import Any

# Try to import syntax highlighting
try:
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.lexers import get_lexer_by_name

    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

# For clipboard operations
try:
    import pyperclip

    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

logger = logging.getLogger("triad.snippets")


class Snippet:
    """Represents a code snippet"""

    def __init__(
        self, title: str, code: str, language: str, tags: list[str] = None, description: str = None
    ):
        self.title = title
        self.code = code
        self.language = language
        self.tags = tags or []
        self.description = description or ""
        self.created = datetime.datetime.now().isoformat()
        self.last_used = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "code": self.code,
            "language": self.language,
            "tags": self.tags,
            "description": self.description,
            "created": self.created,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Snippet":
        """Create from dictionary"""
        snippet = cls(
            title=data["title"],
            code=data["code"],
            language=data["language"],
            tags=data.get("tags", []),
            description=data.get("description", ""),
        )
        snippet.created = data.get("created", datetime.datetime.now().isoformat())
        snippet.last_used = data.get("last_used")
        return snippet

    def use(self) -> None:
        """Mark snippet as used"""
        self.last_used = datetime.datetime.now().isoformat()

    def display(self, with_syntax_highlighting: bool = True) -> None:
        """Display the snippet with optional syntax highlighting"""
        print(f"\n--- {self.title} ({self.language}) ---")

        if self.description:
            print(f"{self.description}\n")

        if with_syntax_highlighting and HAS_PYGMENTS:
            try:
                lexer = get_lexer_by_name(self.language, stripall=True)
                formatter = Terminal256Formatter()
                highlighted_code = highlight(self.code, lexer, formatter)
                print(highlighted_code)
            except:
                print(self.code)
        else:
            print(self.code)

        if self.tags:
            print(f"\nTags: {', '.join(self.tags)}")

    def copy_to_clipboard(self) -> bool:
        """Copy snippet code to clipboard"""
        if HAS_CLIPBOARD:
            try:
                pyperclip.copy(self.code)
                return True
            except:
                return False
        return False

    def save_to_file(self, output_dir: str) -> str | None:
        """Save snippet to a file"""
        try:
            ext = self.get_file_extension()
            filename = f"{self.title.lower().replace(' ', '_')}.{ext}"
            file_path = os.path.join(output_dir, filename)

            with open(file_path, "w") as f:
                f.write(self.code)

            return file_path
        except Exception as e:
            logger.error(f"Error saving snippet to file: {e}")
            return None

    def get_file_extension(self) -> str:
        """Get appropriate file extension for the snippet language"""
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "html": "html",
            "css": "css",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "csharp": "cs",
            "go": "go",
            "ruby": "rb",
            "php": "php",
            "rust": "rs",
            "swift": "swift",
            "bash": "sh",
            "sql": "sql",
            "json": "json",
            "xml": "xml",
            "yaml": "yml",
            "markdown": "md",
        }
        return extensions.get(self.language.lower(), "txt")


class SnippetManager:
    """Manages code snippets"""

    def __init__(self, data_dir: str = "~/.triad/snippets"):
        self.data_dir = os.path.expanduser(data_dir)
        self.index_file = os.path.join(self.data_dir, "index.json")
        self.snippets_dir = os.path.join(self.data_dir, "snippets")

        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.snippets_dir, exist_ok=True)

        # Load snippets
        self.snippets = self._load_index()

    def _load_index(self) -> dict[str, Snippet]:
        """Load snippet index"""
        snippets = {}

        if os.path.exists(self.index_file):
            try:
                with open(self.index_file) as f:
                    data = json.load(f)

                for snippet_id, snippet_data in data.items():
                    snippets[snippet_id] = Snippet.from_dict(snippet_data)

            except Exception as e:
                logger.error(f"Error loading snippets index: {e}")

        return snippets

    def _save_index(self) -> bool:
        """Save snippet index"""
        try:
            data = {}
            for snippet_id, snippet in self.snippets.items():
                data[snippet_id] = snippet.to_dict()

            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error saving snippets index: {e}")
            return False

    def add_snippet(self, snippet: Snippet) -> str:
        """Add a new snippet and return its ID"""
        # Generate a unique ID
        import uuid

        snippet_id = str(uuid.uuid4())[:8]

        # Add to collection
        self.snippets[snippet_id] = snippet

        # Save index
        self._save_index()

        return snippet_id

    def update_snippet(self, snippet_id: str, snippet: Snippet) -> bool:
        """Update an existing snippet"""
        if snippet_id not in self.snippets:
            return False

        self.snippets[snippet_id] = snippet
        return self._save_index()

    def delete_snippet(self, snippet_id: str) -> bool:
        """Delete a snippet"""
        if snippet_id not in self.snippets:
            return False

        del self.snippets[snippet_id]
        return self._save_index()

    def get_snippet(self, snippet_id: str) -> Snippet | None:
        """Get a snippet by ID"""
        return self.snippets.get(snippet_id)

    def search_snippets(
        self, query: str = None, language: str = None, tags: list[str] = None
    ) -> list[tuple[str, Snippet]]:
        """Search snippets by query text, language, or tags"""
        results = []

        for snippet_id, snippet in self.snippets.items():
            # Match all criteria
            if query and not (
                query.lower() in snippet.title.lower()
                or query.lower() in snippet.description.lower()
                or query.lower() in snippet.code.lower()
            ):
                continue

            if language and snippet.language.lower() != language.lower():
                continue

            if tags and not all(tag.lower() in [t.lower() for t in snippet.tags] for tag in tags):
                continue

            results.append((snippet_id, snippet))

        return results

    def list_snippets(self) -> list[tuple[str, Snippet]]:
        """List all snippets"""
        return list(self.snippets.items())

    def list_languages(self) -> list[str]:
        """List all languages used in snippets"""
        languages = set()
        for snippet in self.snippets.values():
            languages.add(snippet.language.lower())
        return sorted(list(languages))

    def list_tags(self) -> list[str]:
        """List all tags used in snippets"""
        tags = set()
        for snippet in self.snippets.values():
            tags.update([t.lower() for t in snippet.tags])
        return sorted(list(tags))

    def create_snippet_from_file(
        self, file_path: str, title: str = None, description: str = None, tags: list[str] = None
    ) -> tuple[str, Snippet] | None:
        """Create a snippet from a file"""
        try:
            # Read file content
            with open(file_path) as f:
                code = f.read()

            # Determine language from file extension
            _, ext = os.path.splitext(file_path)
            language = self._get_language_from_extension(ext)

            # Use filename as title if not provided
            if not title:
                title = os.path.basename(file_path)
                title = os.path.splitext(title)[0].replace("_", " ").title()

            # Create snippet
            snippet = Snippet(
                title=title, code=code, language=language, description=description, tags=tags or []
            )

            # Add to collection
            snippet_id = self.add_snippet(snippet)

            return (snippet_id, snippet)

        except Exception as e:
            logger.error(f"Error creating snippet from file: {e}")
            return None

    def export_snippets(self, output_dir: str) -> bool:
        """Export all snippets to files in a directory"""
        try:
            os.makedirs(output_dir, exist_ok=True)

            # Create a manifest file
            manifest = []

            for snippet_id, snippet in self.snippets.items():
                # Save the snippet to a file
                file_path = snippet.save_to_file(output_dir)

                if file_path:
                    # Add to manifest
                    manifest.append(
                        {
                            "id": snippet_id,
                            "title": snippet.title,
                            "language": snippet.language,
                            "file": os.path.basename(file_path),
                            "tags": snippet.tags,
                            "created": snippet.created,
                        }
                    )

            # Save manifest
            with open(os.path.join(output_dir, "manifest.json"), "w") as f:
                json.dump(manifest, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error exporting snippets: {e}")
            return False

    def import_snippets(self, input_dir: str) -> int:
        """Import snippets from files in a directory"""
        try:
            manifest_file = os.path.join(input_dir, "manifest.json")

            if os.path.exists(manifest_file):
                # Import with manifest
                with open(manifest_file) as f:
                    manifest = json.load(f)

                count = 0
                for item in manifest:
                    file_path = os.path.join(input_dir, item["file"])
                    if os.path.exists(file_path):
                        with open(file_path) as f:
                            code = f.read()

                        snippet = Snippet(
                            title=item["title"],
                            code=code,
                            language=item["language"],
                            tags=item.get("tags", []),
                            description=item.get("description", ""),
                        )

                        if "created" in item:
                            snippet.created = item["created"]

                        self.add_snippet(snippet)
                        count += 1

                return count
            else:
                # Import individual files
                count = 0
                for filename in os.listdir(input_dir):
                    file_path = os.path.join(input_dir, filename)

                    if os.path.isfile(file_path):
                        result = self.create_snippet_from_file(file_path)
                        if result:
                            count += 1

                return count
        except Exception as e:
            logger.error(f"Error importing snippets: {e}")
            return 0

    def _get_language_from_extension(self, ext: str) -> str:
        """Get language name from file extension"""
        ext = ext.lower().lstrip(".")

        # Common extensions to language mapping
        mapping = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "html": "html",
            "css": "css",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "cc": "cpp",
            "cs": "csharp",
            "go": "go",
            "rb": "ruby",
            "php": "php",
            "rs": "rust",
            "swift": "swift",
            "sh": "bash",
            "sql": "sql",
            "json": "json",
            "xml": "xml",
            "yml": "yaml",
            "yaml": "yaml",
            "md": "markdown",
        }

        return mapping.get(ext, "text")


def create_snippet_interactive() -> Snippet | None:
    """Create a snippet interactively"""
    try:
        print("\nCreating a new snippet")
        print("=====================")

        title = input("Title: ")
        if not title:
            print("Title is required")
            return None

        print("\nAvailable languages:")
        print("python, javascript, html, css, bash, sql, java, c, cpp, go, ruby, php, rust, etc.")
        language = input("Language: ")
        if not language:
            print("Language is required")
            return None

        description = input("Description (optional): ")

        tags_input = input("Tags (comma-separated): ")
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

        print("\nEnter code (Ctrl+D or Ctrl+Z to finish):")
        code_lines = []

        try:
            while True:
                line = input()
                code_lines.append(line)
        except EOFError:
            code = "\n".join(code_lines)

        if not code.strip():
            # If no code entered, try to open an editor
            try:
                import subprocess
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=f".{language}", delete=False) as temp:
                    temp_name = temp.name

                # Try to determine the best editor to use
                editor = os.environ.get("EDITOR", "nano")

                subprocess.call([editor, temp_name])

                with open(temp_name) as f:
                    code = f.read()

                # Clean up
                os.unlink(temp_name)

                if not code.strip():
                    print("No code entered")
                    return None
            except:
                print("No code entered")
                return None

        return Snippet(
            title=title, code=code, language=language, description=description, tags=tags
        )

    except KeyboardInterrupt:
        print("\nSnippet creation cancelled")
        return None


def main() -> None:
    """Main entry point for snippet manager"""
    import argparse

    parser = argparse.ArgumentParser(description="Triad Terminal Snippet Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new snippet")
    add_parser.add_argument("--file", "-f", help="Create snippet from a file")
    add_parser.add_argument("--title", "-t", help="Snippet title")
    add_parser.add_argument("--language", "-l", help="Snippet language")
    add_parser.add_argument("--description", "-d", help="Snippet description")
    add_parser.add_argument("--tags", help="Comma-separated list of tags")

    # List command
    list_parser = subparsers.add_parser("list", help="List snippets")
    list_parser.add_argument("--language", "-l", help="Filter by language")
    list_parser.add_argument("--tag", "-t", help="Filter by tag")
    list_parser.add_argument("--query", "-q", help="Search in title and description")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show a snippet")
    show_parser.add_argument("id", help="Snippet ID")
    show_parser.add_argument(
        "--no-highlight", action="store_true", help="Disable syntax highlighting"
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a snippet")
    delete_parser.add_argument("id", help="Snippet ID")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export snippets")
    export_parser.add_argument("directory", help="Output directory")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import snippets")
    import_parser.add_argument("directory", help="Input directory")

    # Copy command
    copy_parser = subparsers.add_parser("copy", help="Copy snippet to clipboard")
    copy_parser.add_argument("id", help="Snippet ID")

    args = parser.parse_args()

    manager = SnippetManager()

    if args.command == "add":
        if args.file:
            # Create from file
            tags = args.tags.split(",") if args.tags else []
            result = manager.create_snippet_from_file(
                args.file, title=args.title, description=args.description, tags=tags
            )

            if result:
                snippet_id, snippet = result
                print(f"Snippet added with ID: {snippet_id}")
            else:
                print("Failed to add snippet from file")
        else:
            # Interactive creation
            snippet = create_snippet_interactive()
            if snippet:
                snippet_id = manager.add_snippet(snippet)
                print(f"\nSnippet added with ID: {snippet_id}")

    elif args.command == "list":
        # Build search criteria
        language = args.language
        tags = [args.tag] if args.tag else None
        query = args.query

        if language or tags or query:
            snippets = manager.search_snippets(query, language, tags)
        else:
            snippets = manager.list_snippets()

        if not snippets:
            print("No snippets found")
            return

        print(f"\nFound {len(snippets)} snippets:")
        print("=" * 40)

        for snippet_id, snippet in snippets:
            # Format the output
            tags_str = ", ".join(snippet.tags) if snippet.tags else "None"
            created = datetime.datetime.fromisoformat(snippet.created).strftime("%Y-%m-%d")

            print(f"ID: {snippet_id}")
            print(f"Title: {snippet.title}")
            print(f"Language: {snippet.language}")
            print(f"Created: {created}")
            print(f"Tags: {tags_str}")
            print("-" * 40)

    elif args.command == "show":
        snippet = manager.get_snippet(args.id)
        if snippet:
            snippet.display(not args.no_highlight)
            # Update last used timestamp
            snippet.use()
            manager.update_snippet(args.id, snippet)
        else:
            print(f"Snippet with ID {args.id} not found")

    elif args.command == "delete":
        if manager.delete_snippet(args.id):
            print(f"Snippet {args.id} deleted")
        else:
            print(f"Snippet with ID {args.id} not found")

    elif args.command == "export":
        if manager.export_snippets(args.directory):
            print(f"Snippets exported to {args.directory}")
        else:
            print("Failed to export snippets")

    elif args.command == "import":
        count = manager.import_snippets(args.directory)
        print(f"Imported {count} snippets")

    elif args.command == "copy":
        snippet = manager.get_snippet(args.id)
        if snippet:
            if snippet.copy_to_clipboard():
                print(f"Snippet '{snippet.title}' copied to clipboard")
                # Update last used timestamp
                snippet.use()
                manager.update_snippet(args.id, snippet)
            else:
                print("Failed to copy to clipboard (pyperclip not installed)")
        else:
            print(f"Snippet with ID {args.id} not found")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
