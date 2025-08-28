I#!/usr/bin/env python3

"""
Triad Terminal AI Avatar
Displays a visual representation of the AI assistant
"""

import os
import sys
import json
import random
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Tuple

# Try to import terminal graphics libraries
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

logger = logging.getLogger("triad.avatar")

class AIAvatar:
    """Visual representation of the AI assistant"""
    
    # Default avatar frames for animation
    DEFAULT_AVATAR = [
        r"""
       .---.
      /     \
      \.@-@./
      /`\_/`\
     //  _  \\
    | \     )|_
   /`\_`>  <_/ \
   \__/'---'\__/
        """,
        r"""
       .---.
      /     \
      \.@-@./
      /`\_/`\
     //  _  \\
    | \     )|_
   /`\_`>  <_/ \
   \__/'---'\__/
        """,
        r"""
       .---.
      /     \
      \.o-o./
      /`\_/`\
     //  _  \\
    | \     )|_
   /`\_`>  <_/ \
   \__/'---'\__/
        """
    ]
    
    # Different avatar styles
    AVATAR_STYLES = {
        "robot": [
            r"""
      _______
     |  ___  |
     | |   | |
     | |___| |
     |_______|
    /|     |\
   / |     | \
  /__|_____|__\
     |  |  |
     |__|__|
            """,
            r"""
      _______
     |  ___  |
     | | o | |
     | |___| |
     |_______|
    /|     |\
   / |     | \
  /__|_____|__\
     |  |  |
     |__|__|
            """
        ],
        "brain": [
            r"""
     .-----------------.
    /   ,---.  ,---.   \
   /  /.|   |  |   |.   \
  /  / |   |  |   |  \   \
 |  |  `---'  `---'   |   |
 |  |                 |   |
 |  |     .----.      |   |
 |  |    /      \     |   |
  \  \  |        |   /   /
   \  \  \      /   /   /
    \   `--------'   /
     `--------------'
            """,
            r"""
     .-----------------.
    /   ,---.  ,---.   \
   /  /*|   |  |   |*\  \
  /  / |   |  |   |  \   \
 |  |  `---'  `---'   |   |
 |  |                 |   |
 |  |     .----.      |   |
 |  |    /      \     |   |
  \  \  |        |   /   /
   \  \  \      /   /   /
    \   `--------'   /
     `--------------'
            """
        ],
        "ghost": [
            r"""
      .-.
     (o o)
     | O |
     |   |
     '~~~'
            """,
            r"""
      .-.
     (* *)
     | O |
     |   |
     '~~~'
            """
        ],
        "pixel": [
            r"""
     ┌─────┐
     │ ┌─┐ │
     │ │ │ │
     │ └─┘ │
     └─────┘
     ┌─────┐
     │     │
     │  ■  │
     │     │
     └─────┘
            """,
            r"""
     ┌─────┐
     │ ┌─┐ │
     │ │*│ │
     │ └─┘ │
     └─────┘
     ┌─────┐
     │  ▲  │
     │ ■■■ │
     │     │
     └─────┘
            """
        ]
    }
    
    def __init__(self, style: str = "robot", color: str = "cyan", 
                data_dir: str = "~/.triad/avatar"):
        self.data_dir = os.path.expanduser(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load custom avatar if available
        self.custom_avatar = self._load_custom_avatar()
        
        # Set avatar style
        if self.custom_avatar:
            self.frames = self.custom_avatar
        else:
            self.frames = self.AVATAR_STYLES.get(style, self.DEFAULT_AVATAR)
            
        self.color = color
        self.current_frame = 0
        self.animation_thread = None
        self.stop_event = threading.Event()
    
    def _load_custom_avatar(self) -> Optional[List[str]]:
        """Load custom avatar from file"""
        custom_avatar_file = os.path.join(self.data_dir, "custom_avatar.json")
        
        if os.path.exists(custom_avatar_file):
            try:
                with open(custom_avatar_file, "r") as f:
                    avatar_data = json.load(f)
                    
                if isinstance(avatar_data, list) and all(isinstance(frame, str) for frame in avatar_data):
                    logger.info("Loaded custom avatar")
                    return avatar_data
                    
            except Exception as e:
                logger.error(f"Error loading custom avatar: {e}")
                
        return None
    
    def save_custom_avatar(self, frames: List[str]) -> bool:
        """Save custom avatar frames"""
        try:
            custom_avatar_file = os.path.join(self.data_dir, "custom_avatar.json")
            
            with open(custom_avatar_file, "w") as f:
                json.dump(frames, f, indent=2)
                
            self.custom_avatar = frames
            self.frames = frames
            
            logger.info("Saved custom avatar")
            return True
            
        except Exception as e:
            logger.error(f"Error saving custom avatar: {e}")
            return False
    
def reset_to_default(self, style: str = "robot") -> None:
    """Reset to a built-in avatar style and remove any saved custom avatar.

    Args:
        style (str): Which built-in style to use (e.g., "robot").
    """
    # Pick frames from built-ins, fall back to DEFAULT_AVATAR
    self.frames = self.AVATAR_STYLES.get(style, self.DEFAULT_AVATAR)
    self.custom_avatar = None

    # Best-effort cleanup of on-disk custom avatar
    custom_avatar_file = os.path.join(self.data_dir, "custom_avatar.json")
    try:
        if os.path.exists(custom_avatar_file):
            os.remove(custom_avatar_file)
            logger.info("Removed custom avatar file")
    except Exception as e:
        # Don’t fail the app if deletion isn’t possible; just log it
        logger.warning(f"Could not remove custom avatar file: {e}")
