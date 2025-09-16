#!/usr/bin/env python3

"""
Triad Terminal Theme Visualizer
Provides visual theme previews and customization tools
"""

import colorsys
import json
import logging
import os
from typing import Any

# Try to import visualization libraries
try:
    from PIL import Image, ImageColor, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# For terminal rendering if PIL is not available
try:
    from rich.color import Color
    from rich.columns import Columns
    from rich.console import Console
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

logger = logging.getLogger("triad.theme")

class ColorPalette:
    """Color palette utilities for theme generation"""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    @staticmethod
    def rgb_to_hsl(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """Convert RGB to HSL (Hue, Saturation, Lightness)"""
        r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return h, s, l

    @staticmethod
    def hsl_to_rgb(hsl: tuple[float, float, float]) -> tuple[int, int, int]:
        """Convert HSL to RGB"""
        h, s, l = hsl
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(r * 255), int(g * 255), int(b * 255)

    @staticmethod
    def adjust_brightness(color: str, factor: float) -> str:
        """Adjust brightness of a hex color"""
        rgb = ColorPalette.hex_to_rgb(color)
        h, s, l = ColorPalette.rgb_to_hsl(rgb)

        # Adjust lightness
        l = max(0, min(1, l * factor))

        # Convert back to RGB
        new_rgb = ColorPalette.hsl_to_rgb((h, s, l))
        return ColorPalette.rgb_to_hex(new_rgb)

    @staticmethod
    def generate_complementary(color: str) -> str:
        """Generate a complementary color"""
        rgb = ColorPalette.hex_to_rgb(color)
        h, s, l = ColorPalette.rgb_to_hsl(rgb)

        # Complementary color has hue shifted by 0.5
        new_h = (h + 0.5) % 1.0

        new_rgb = ColorPalette.hsl_to_rgb((new_h, s, l))
        return ColorPalette.rgb_to_hex(new_rgb)

    @staticmethod
    def generate_palette(base_color: str, count: int = 5) -> list[str]:
        """Generate a palette of related colors"""
        rgb = ColorPalette.hex_to_rgb(base_color)
        h, s, l = ColorPalette.rgb_to_hsl(rgb)

        palette = []

        # Generate colors with varying brightness and saturation
        for i in range(count):
            # Adjust saturation and lightness
            new_s = max(0, min(1, s + (i - count/2) * 0.15))
            new_l = max(0.1, min(0.9, l + (i - count/2) * 0.1))

            new_rgb = ColorPalette.hsl_to_rgb((h, new_s, new_l))
            palette.append(ColorPalette.rgb_to_hex(new_rgb))

        return palette

class ThemePreview:
    """Generates visual previews of terminal themes"""

    @staticmethod
    def create_image_preview(theme: dict[str, Any], output_path: str, size: tuple[int, int] = (800, 600)) -> bool:
        """Create an image preview of a terminal theme"""
        if not HAS_PIL:
            logger.error("PIL not available, cannot create image preview")
            return False

        try:
            colors = theme.get("colors", {})

            # Get theme colors with fallbacks
            bg_color = colors.get("background", "#000000")
            fg_color = colors.get("foreground", "#FFFFFF")
            accent_color = colors.get("accent", "#00FF00")
            secondary_color = colors.get("secondary", "#0000FF")

            # Create image
            img = Image.new("RGB", size, bg_color)
            draw = ImageDraw.Draw(img)

            # Try to load a font, use default if not available
            try:
                font_large = ImageFont.truetype("DejaVuSansMono.ttf", 24)
                font_medium = ImageFont.truetype("DejaVuSansMono.ttf", 18)
                font_small = ImageFont.truetype("DejaVuSansMono.ttf", 14)
            except OSError:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Draw header
            header_height = 60
            draw.rectangle([(0, 0), (size[0], header_height)], fill=accent_color)

            # Draw title
            title = f"Triad Terminal - {theme.get('name', 'Custom')} Theme"
            draw.text((20, 15), title, fill=bg_color, font=font_large)

            # Draw main content area
            content_y = header_height + 20

            # Draw a terminal window
            term_width, term_height = size[0] - 40, 200
            draw.rectangle([(20, content_y), (20 + term_width, content_y + term_height)],
                          outline=accent_color, fill=bg_color, width=2)

            # Draw terminal content
            term_content = [
                "user@triad > echo 'Hello, world!'",
                "Hello, world!",
                "",
                "user@triad > ls -la",
                "total 32",
                "drwxr-xr-x  5 user  staff   160 Aug 22 12:34 .",
                "drwxr-xr-x  3 user  staff    96 Aug 22 12:30 ..",
                "-rw-r--r--  1 user  staff  1823 Aug 22 12:32 README.md",
                "drwxr-xr-x  8 user  staff   256 Aug 22 12:33 src",
                "",
                "user@triad > _"
            ]

            for i, line in enumerate(term_content):
                if "user@triad" in line:
                    parts = line.split(">")
                    draw.text((30, content_y + 10 + i * 20), parts[0] + ">", fill=accent_color, font=font_medium)
                    if len(parts) > 1:
                        draw.text((30 + 150, content_y + 10 + i * 20), parts[1], fill=fg_color, font=font_medium)
                else:
                    draw.text((30, content_y + 10 + i * 20), line, fill=fg_color, font=font_medium)

            # Draw color swatches
            swatch_y = content_y + term_height + 40
            swatch_width = (size[0] - 60) // 5
            swatch_height = 40

            color_items = list(colors.items())[:5]  # Take first 5 colors
            for i, (name, color) in enumerate(color_items):
                x = 30 + i * (swatch_width + 10)
                draw.rectangle([(x, swatch_y), (x + swatch_width, swatch_y + swatch_height)],
                              fill=color, outline=fg_color)
                draw.text((x + 5, swatch_y + swatch_height + 10), name, fill=fg_color, font=font_small)

            # Draw footer
            footer_y = size[1] - 60
            draw.rectangle([(0, footer_y), (size[0], size[1])], fill=secondary_color)
            draw.text((20, footer_y + 20), "Triad Terminal - The next generation development environment",
                     fill=bg_color, font=font_medium)

            # Save the image
            img.save(output_path)
            logger.info(f"Theme preview saved to {output_path}")

            return True

        except Exception as e:
            logger.error(f"Error creating theme preview: {e}")
            return False

    @staticmethod
    def print_terminal_preview(theme: dict[str, Any]) -> None:
        """Print a theme preview in the terminal"""
        if HAS_RICH:
            console = Console()

            colors = theme.get("colors", {})
            bg_color = colors.get("background", "#000000")
            fg_color = colors.get("foreground", "#FFFFFF")
            accent_color = colors.get("accent", "#00FF00")

            # Create a header panel
            console.print(Panel(
                f"[bold]{theme.get('name', 'Custom')} Theme[/]",
                style=f"on {accent_color} {bg_color}",
                expand=True
            ))

            # Create color swatches
            swatches = []
            for name, color in colors.items():
                swatches.append(Panel(
                    f"[{color}]■■■■■[/]\n[white]{name}[/]",
                    width=16,
                    style=f"on {bg_color}"
                ))

            # Display swatches in columns
            console.print(Columns(swatches))

            # Create terminal preview
            term_content = "\n".join([
                f"[{accent_color}]user@triad >[/] [white]echo 'Hello, world!'[/]",
                f"[{fg_color}]Hello, world![/]",
                "",
                f"[{accent_color}]user@triad >[/] [white]ls -la[/]",
                f"[{fg_color}]total 32[/]",
                f"[{fg_color}]drwxr-xr-x  5 user  staff   160 Aug 22 12:34 .[/]",
                f"[{fg_color}]drwxr-xr-x  3 user  staff    96 Aug 22 12:30 ..[/]",
                f"[{fg_color}]-rw-r--r--  1 user  staff  1823 Aug 22 12:32 README.md[/]",
                f"[{fg_color}]drwxr-xr-x  8 user  staff   256 Aug 22 12:33 src[/]",
                "",
                f"[{accent_color}]user@triad >[/] [white]_[/]"
            ])

            console.print(Panel(
                term_content,
                title="Terminal Preview",
                border_style=accent_color,
                style=f"on {bg_color}"
            ))
        else:
            # Simple preview without Rich
            print(f"\n=== {theme.get('name', 'Custom')} Theme ===\n")
            print("Colors:")
            for name, color in theme.get("colors", {}).items():
                print(f"  - {name}: {color}")

class ThemeCustomizer:
    """Tools for customizing terminal themes"""

    def __init__(self, theme_dir: str = "~/.triad/themes"):
        self.theme_dir = os.path.expanduser(theme_dir)
        os.makedirs(self.theme_dir, exist_ok=True)

    def load_themes(self) -> dict[str, dict[str, Any]]:
        """Load all available themes"""
        themes = {}

        # Load built-in themes from the ThemeManager
        from enhanced_ui import ThemeManager
        theme_manager = ThemeManager()
        builtin_themes = theme_manager.THEMES

        # Add built-in themes
        themes.update(builtin_themes)

        # Load custom themes from theme directory
        for filename in os.listdir(self.theme_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.theme_dir, filename)) as f:
                        theme_data = json.load(f)
                        theme_id = os.path.splitext(filename)[0]
                        themes[theme_id] = theme_data
                except Exception as e:
                    logger.error(f"Error loading theme {filename}: {e}")

        return themes

    def save_theme(self, theme_id: str, theme_data: dict[str, Any]) -> bool:
        """Save a theme to the theme directory"""
        try:
            theme_path = os.path.join(self.theme_dir, f"{theme_id}.json")
            with open(theme_path, "w") as f:
                json.dump(theme_data, f, indent=2)
            logger.info(f"Theme saved to {theme_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving theme: {e}")
            return False

    def generate_theme(self, base_color: str, name: str = "Custom Theme") -> dict[str, Any]:
        """Generate a complete theme from a base color"""
        # Convert to hex if it's not already
        if not base_color.startswith('#'):
            try:
                base_color = ImageColor.getrgb(base_color)
                base_color = '#{:02x}{:02x}{:02x}'.format(*base_color)
            except:
                base_color = "#00aa00"  # Default to green if conversion fails

        # Generate palette
        palette = ColorPalette.generate_palette(base_color, 5)

        # Determine if the theme is dark or light
        rgb = ColorPalette.hex_to_rgb(base_color)
        h, s, l = ColorPalette.rgb_to_hsl(rgb)
        is_dark = l < 0.5

        # Set background and foreground based on lightness
        if is_dark:
            bg_color = "#121212"  # Dark background
            fg_color = ColorPalette.adjust_brightness(base_color, 2.0)  # Brighter foreground
        else:
            bg_color = "#f5f5f5"  # Light background
            fg_color = ColorPalette.adjust_brightness(base_color, 0.7)  # Darker foreground

        # Generate complementary color for accents
        accent_color = ColorPalette.generate_complementary(base_color)

        # Create theme
        theme = {
            "name": name,
            "description": f"Custom theme based on {base_color}",
            "colors": {
                "background": bg_color,
                "foreground": fg_color,
                "accent": base_color,
                "secondary": accent_color,
                "highlight": palette[0],
                "error": "#ff3333" if is_dark else "#cc0000",
                "warning": "#ffcc00" if is_dark else "#cc9900",
                "success": "#33cc33" if is_dark else "#009900",
                "info": palette[1],
                "panel": ColorPalette.adjust_brightness(bg_color, 1.2 if is_dark else 0.95)
            },
            "styles": {
                "header": f"bold {fg_color} on {bg_color}",
                "title": f"bold {base_color}",
                "text": fg_color,
                "command": f"bold {base_color}",
                "link": f"underline {base_color}",
                "panel_border": accent_color
            }
        }

        return theme

def main() -> None:
    """Main entry point for theme visualizer"""
    import argparse

    parser = argparse.ArgumentParser(description="Triad Terminal Theme Visualizer")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Preview command
    preview_parser = subparsers.add_parser("preview", help="Preview a theme")
    preview_parser.add_argument("theme", help="Theme name or ID")
    preview_parser.add_argument("--output", "-o", help="Output image file path")

    # List command
    list_parser = subparsers.add_parser("list", help="List available themes")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a new theme")
    generate_parser.add_argument("color", help="Base color (hex or name)")
    generate_parser.add_argument("name", help="Theme name")
    generate_parser.add_argument("--save", "-s", action="store_true", help="Save the generated theme")

    args = parser.parse_args()

    customizer = ThemeCustomizer()

    if args.command == "preview":
        themes = customizer.load_themes()
        if args.theme not in themes:
            print(f"Theme '{args.theme}' not found. Available themes: {', '.join(themes.keys())}")
            return

        theme = themes[args.theme]

        if args.output:
            ThemePreview.create_image_preview(theme, args.output)
            print(f"Theme preview saved to {args.output}")
        else:
            ThemePreview.print_terminal_preview(theme)

    elif args.command == "list":
        themes = customizer.load_themes()
        print("\nAvailable themes:")
        for theme_id, theme_data in themes.items():
            print(f"  - {theme_id}: {theme_data.get('name', 'Unnamed')} - {theme_data.get('description', '')}")

    elif args.command == "generate":
        theme = customizer.generate_theme(args.color, args.name)
        if args.save:
            theme_id = args.name.lower().replace(" ", "_")
            customizer.save_theme(theme_id, theme)
            print(f"Theme '{args.name}' saved with ID '{theme_id}'")

        ThemePreview.print_terminal_preview(theme)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
