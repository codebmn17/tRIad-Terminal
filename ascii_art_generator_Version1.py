#!/usr/bin/env python3

"""
Triad Terminal ASCII Art Generator
Creates customized ASCII art for terminal displays
"""

import os
import sys
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

logger = logging.getLogger("triad.ascii")

class ASCIIArtGenerator:
    """Generates ASCII art for the terminal"""
    
    # Collection of small ASCII art elements
    SMALL_ART = {
        "computer": [
            " _____________",
            "|  _________  |",
            "| |         | |",
            "| |_________| |",
            "|_____________|",
            "    _|_____|_  ",
            "   |_________|  "
        ],
        "terminal": [
            " ________________",
            "|                |",
            "| $ _            |",
            "|                |",
            "|________________|"
        ],
        "rocket": [
            "    /\\",
            "   /  \\",
            "  |    |",
            "  |    |",
            " /|    |\\",
            "/ |    | \\",
            "  |____|",
            "  |    |",
            "  |    |",
            " /      \\",
            "/        \\"
        ],
        "cloud": [
            "    .-~~~-.",
            "   /       \\",
            "  |         |",
            "   \\       /",
            "    '-...-'"
        ],
        "lightning": [
            "    /",
            "   /",
            "  /",
            " /",
            "/",
            "\\",
            " \\",
            "  \\"
        ],
        "server": [
            " .------------------.",
            " |  .-----------. |",
            " |  |           | |",
            " |  |           | |",
            " |  |-----------| |",
            " |  |           | |",
            " |  |           | |",
            " |  |-----------| |",
            " |  |           | |",
            " |  |           | |",
            " |  |-----------| |",
            " |  |           | |",
            " |  |           | |",
            " |  '-----------' |",
            " '------------------'"
        ],
        "coffee": [
            "      ) )",
            "     ( (",
            "   .-----.",
            "  |       |]",
            "  `-------'"
        ]
    }
    
    # Collection of banner art styles
    BANNER_STYLES = {
        "standard": {
            "top_left": "╔", "top_right": "╗", "bottom_left": "╚", "bottom_right": "╝",
            "horizontal": "═", "vertical": "║"
        },
        "double": {
            "top_left": "╔", "top_right": "╗", "bottom_left": "╚", "bottom_right": "╝",
            "horizontal": "═", "vertical": "║"
        },
        "ascii": {
            "top_left": "+", "top_right": "+", "bottom_left": "+", "bottom_right": "+",
            "horizontal": "-", "vertical": "|"
        },
        "rounded": {
            "top_left": "╭", "top_right": "╮", "bottom_left": "╰", "bottom_right": "╯",
            "horizontal": "─", "vertical": "│"
        },
        "stars": {
            "top_left": "*", "top_right": "*", "bottom_left": "*", "bottom_right": "*",
            "horizontal": "*", "vertical": "*"
        }
    }
    
    # Predefined figlet-style fonts for small headers
    FIGLET_FONTS = {
        "standard": {
            "T": [" _____", "|_   _|", "  | |  ", "  | |  ", "  |_|  "],
            "R": [" ____  ", "|  _ \\ ", "| |_) |", "|  _ < ", "|_| \\_\\"],
            "I": [" ___ ", "|_ _|", " | | ", " | | ", "|___|"],
            "A": ["     _    ", "    / \\   ", "   / _ \\  ", "  / ___ \\ ", " /_/   \\_\\"],
            "D": [" ____  ", "|  _ \\ ", "| | | |", "| |_| |", "|____/ "],
        }
    }
    
    @staticmethod
    def get_small_art(art_name: str) -> List[str]:
        """Get a small ASCII art piece by name"""
        return ASCIIArtGenerator.SMALL_ART.get(art_name, ["Art not found"])
    
    @staticmethod
    def create_banner(text: str, style: str = "standard", width: int = 50, padding: int = 1) -> List[str]:
        """Create a banner with specified style"""
        style_chars = ASCIIArtGenerator.BANNER_STYLES.get(style, ASCIIArtGenerator.BANNER_STYLES["standard"])
        
        # Ensure width is enough to fit the text
        text_width = len(text) + 2 * padding
        width = max(width, text_width + 2)  # +2 for the border characters
        
        # Create the banner
        banner = []
        
        # Top border
        banner.append(style_chars["top_left"] + style_chars["horizontal"] * (width - 2) + style_chars["top_right"])
        
        # Padding above text
        for _ in range(padding):
            banner.append(style_chars["vertical"] + " " * (width - 2) + style_chars["vertical"])
        
        # Text line
        text_line = style_chars["vertical"]
        text_padding = (width - 2 - len(text)) // 2
        text_line += " " * text_padding + text
        text_line += " " * (width - 2 - len(text) - text_padding) + style_chars["vertical"]
        banner.append(text_line)
        
        # Padding below text
        for _ in range(padding):
            banner.append(style_chars["vertical"] + " " * (width - 2) + style_chars["vertical"])
        
        # Bottom border
        banner.append(style_chars["bottom_left"] + style_chars["horizontal"] * (width - 2) + style_chars["bottom_right"])
        
        return banner
    
    @staticmethod
    def create_header(text: str, font: str = "standard") -> List[str]:
        """Create a figlet-style header"""
        # Only supports uppercase letters, numbers and some special characters
        text = text.upper()
        
        # Get the font
        font_data = ASCIIArtGenerator.FIGLET_FONTS.get(font, ASCIIArtGenerator.FIGLET_FONTS["standard"])
        
        # Find the height of the font
        font_height = 0
        for char in font_data.values():
            font_height = max(font_height, len(char))
        
        # Create the header
        header = ["" for _ in range(font_height)]
        
        # Add each character
        for char in text:
            if char in font_data:
                char_art = font_data[char]
                # Add each line of the character to the header
                for i in range(font_height):
                    if i < len(char_art):
                        header[i] += char_art[i] + " "
                    else:
                        header[i] += " " * (len(char_art[0]) + 1)
            else:
                # For unsupported characters, add spaces
                for i in range(font_height):
                    header[i] += "  "
        
        return header
    
    @staticmethod
    def combine_art(art1: List[str], art2: List[str], horizontal: bool = True, spacing: int = 2) -> List[str]:
        """Combine two pieces of ASCII art"""
        if horizontal:
            # Combine side by side
            max_height = max(len(art1), len(art2))
            result = []
            
            for i in range(max_height):
                line = ""
                if i < len(art1):
                    line += art1[i]
                else:
                    line += " " * len(art1[0] if art1 else 0)
                
                line += " " * spacing
                
                if i < len(art2):
                    line += art2[i]
                
                result.append(line)
            
            return result
        else:
            # Combine top to bottom
            result = list(art1)  # Copy the first art
            
            # Add spacing
            for _ in range(spacing):
                result.append("")
            
            # Add the second art
            result.extend(art2)
            
            return result
    
    @staticmethod
    def create_random_scene() -> List[str]:
        """Create a random scene using multiple art pieces"""
        # Choose 2-3 random art pieces
        available_art = list(ASCIIArtGenerator.SMALL_ART.keys())
        num_pieces = random.randint(2, 3)
        chosen_pieces = random.sample(available_art, min(num_pieces, len(available_art)))
        
        # Start with first piece
        scene = ASCIIArtGenerator.get_small_art(chosen_pieces[0])
        
        # Add additional pieces
        for i in range(1, len(chosen_pieces)):
            next_piece = ASCIIArtGenerator.get_small_art(chosen_pieces[i])
            horizontal = random.choice([True, False])
            spacing = random.randint(1, 4)
            scene = ASCIIArtGenerator.combine_art(scene, next_piece, horizontal, spacing)
        
        return scene
    
    @staticmethod
    def create_logo(text: str, style: str = "standard") -> List[str]:
        """Create a stylized logo"""
        # Create header text
        header = ASCIIArtGenerator.create_header(text, "standard")
        
        # Create a banner around it
        padding = 1
        max_line_length = max(len(line) for line in header)
        banner_width = max_line_length + 4 + (padding * 2)
        
        banner_style = ASCIIArtGenerator.BANNER_STYLES.get(style, ASCIIArtGenerator.BANNER_STYLES["standard"])
        
        logo = []
        
        # Top border
        logo.append(banner_style["top_left"] + banner_style["horizontal"] * (banner_width - 2) + banner_style["top_right"])
        
        # Padding above header
        for _ in range(padding):
            logo.append(banner_style["vertical"] + " " * (banner_width - 2) + banner_style["vertical"])
        
        # Add header lines
        for line in header:
            padding_spaces = (banner_width - 2 - len(line)) // 2
            logo_line = banner_style["vertical"] + " " * padding_spaces + line
            logo_line += " " * (banner_width - 2 - len(line) - padding_spaces) + banner_style["vertical"]
            logo.append(logo_line)
        
        # Padding below header
        for _ in range(padding):
            logo.append(banner_style["vertical"] + " " * (banner_width - 2) + banner_style["vertical"])
        
        # Bottom border
        logo.append(banner_style["bottom_left"] + banner_style["horizontal"] * (banner_width - 2) + banner_style["bottom_right"])
        
        return logo
    
    @staticmethod
    def save_to_file(art: List[str], filename: str) -> bool:
        """Save ASCII art to a file"""
        try:
            with open(filename, "w") as f:
                for line in art:
                    f.write(line + "\n")
            return True
        except Exception as e:
            logger.error(f"Error saving ASCII art: {e}")
            return False
    
    @staticmethod
    def load_from_file(filename: str) -> List[str]:
        """Load ASCII art from a file"""
        try:
            with open(filename, "r") as f:
                return [line.rstrip("\n") for line in f.readlines()]
        except Exception as e:
            logger.error(f"Error loading ASCII art: {e}")
            return ["Error loading art"]

def main() -> None:
    """Main entry point for ASCII art generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Triad Terminal ASCII Art Generator")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Banner command
    banner_parser = subparsers.add_parser("banner", help="Create a banner")
    banner_parser.add_argument("text", help="Text to display in banner")
    banner_parser.add_argument("--style", "-s", default="standard", choices=list(ASCIIArtGenerator.BANNER_STYLES.keys()),
                              help="Banner style")
    banner_parser.add_argument("--width", "-w", type=int, default=50, help="Banner width")
    banner_parser.add_argument("--padding", "-p", type=int, default=1, help="Padding inside banner")
    banner_parser.add_argument("--output", "-o", help="Output file")
    
    # Header command
    header_parser = subparsers.add_parser("header", help="Create a header")
    header_parser.add_argument("text", help="Text to display in header")
    header_parser.add_argument("--font", "-f", default="standard", choices=list(ASCIIArtGenerator.FIGLET_FONTS.keys()),
                              help="Header font")
    header_parser.add_argument("--output", "-o", help="Output file")
    
    # Logo command
    logo_parser = subparsers.add_parser("logo", help="Create a logo")
    logo_parser.add_argument("text", help="Text to display in logo")
    logo_parser.add_argument("--style", "-s", default="standard", choices=list(ASCIIArtGenerator.BANNER_STYLES.keys()),
                            help="Logo style")
    logo_parser.add_argument("--output", "-o", help="Output file")
    
    # Art command
    art_parser = subparsers.add_parser("art", help="Show or combine ASCII art pieces")
    art_parser.add_argument("--art", "-a", action="append", choices=list(ASCIIArtGenerator.SMALL_ART.keys()),
                           help="Art piece to display (can be specified multiple times)")
    art_parser.add_argument("--random", "-r", action="store_true", help="Create a random scene")
    art_parser.add_argument("--output", "-o", help="Output file")
    
    args = parser.parse_args()
    
    if args.command == "banner":
        banner = ASCIIArtGenerator.create_banner(args.text, args.style, args.width, args.padding)
        if args.output:
            ASCIIArtGenerator.save_to_file(banner, args.output)
            print(f"Banner saved to {args.output}")
        else:
            print("\n".join(banner))
    
    elif args.command == "header":
        header = ASCIIArtGenerator.create_header(args.text, args.font)
        if args.output:
            ASCIIArtGenerator.save_to_file(header, args.output)
            print(f"Header saved to {args.output}")
        else:
            print("\n".join(header))
    
    elif args.command == "logo":
        logo = ASCIIArtGenerator.create_logo(args.text, args.style)
        if args.output:
            ASCIIArtGenerator.save_to_file(logo, args.output)
            print(f"Logo saved to {args.output}")
        else:
            print("\n".join(logo))
    
    elif args.command == "art":
        if args.random:
            art = ASCIIArtGenerator.create_random_scene()
        elif args.art:
            # Start with the first piece
            art = ASCIIArtGenerator.get_small_art(args.art[0])
            
            # Combine with additional pieces
            for i in range(1, len(args.art)):
                next_piece = ASCIIArtGenerator.get_small_art(args.art[i])
                art = ASCIIArtGenerator.combine_art(art, next_piece, i % 2 == 0)
        else:
            # Show available art pieces
            print("Available art pieces:")
            for name in ASCIIArtGenerator.SMALL_ART.keys():
                print(f"  - {name}")
            return
        
        if args.output:
            ASCIIArtGenerator.save_to_file(art, args.output)
            print(f"Art saved to {args.output}")
        else:
            print("\n".join(art))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()