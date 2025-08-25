#!/usr/bin/env python3

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
        """Reset to default avatar style"""
        if style in self.AVATAR_STYLES:
            self.frames = self.AVATAR_STYLES[style]
            self.custom_avatar = None
            
            # Remove custom avatar file if it exists
            custom_avatar_file = os.path.join(self.data_dir, "custom_avatar.json")
            if os.path.exists(custom_avatar_file):
                try:
                    os.remove(custom_avatar_file)
                except Exception:
                    pass
                    
            logger.info(f"Reset to default avatar style: {style}")
        else:
            logger.error(f"Unknown avatar style: {style}")
    
    def display(self) -> None:
        """Display current avatar frame"""
        frame = self.frames[self.current_frame]
        
        if HAS_RICH:
            console = Console()
            console.print(Panel(
                frame, 
                border_style=self.color,
                box=box.ROUNDED,
                title="AI Assistant",
                title_align="center"
            ))
        else:
            print(frame)
    
    def animate(self, duration: float = 5.0, fps: int = 2) -> None:
        """Animate the avatar for a specified duration"""
        if self.animation_thread and self.animation_thread.is_alive():
            # Animation already running
            return
            
        self.stop_event.clear()
        self.animation_thread = threading.Thread(
            target=self._animation_loop,
            args=(duration, fps)
        )
        self.animation_thread.daemon = True
        self.animation_thread.start()
    
    def stop_animation(self) -> None:
        """Stop the avatar animation"""
        if self.animation_thread and self.animation_thread.is_alive():
            self.stop_event.set()
            self.animation_thread.join(timeout=1.0)
    
    def _animation_loop(self, duration: float, fps: int) -> None:
        """Animation loop in background thread"""
        start_time = time.time()
        frame_delay = 1.0 / fps
        
        try:
            while not self.stop_event.is_set() and (time.time() - start_time < duration):
                # Clear the console (platform-specific)
                if os.name == 'nt':  # Windows
                    os.system('cls')
                else:  # Unix/Linux/MacOS
                    os.system('clear')
                
                # Display current frame
                self.display()
                
                # Move to next frame
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                
                # Sleep
                time.sleep(frame_delay)
                
        except Exception as e:
            logger.error(f"Error in animation loop: {e}")
    
    def speak_animation(self, text: str, speed: float = 0.05) -> None:
        """Display the avatar with animated speaking"""
        if self.animation_thread and self.animation_thread.is_alive():
            self.stop_animation()
            
        self.stop_event.clear()
        self.animation_thread = threading.Thread(
            target=self._speak_animation_loop,
            args=(text, speed)
        )
        self.animation_thread.daemon = True
        self.animation_thread.start()
    
    def _speak_animation_loop(self, text: str, speed: float) -> None:
        """Speaking animation loop"""
        try:
            if HAS_RICH:
                console = Console()
                
                for i, char in enumerate(text):
                    if self.stop_event.is_set():
                        break
                        
                    # Switch frames to simulate speaking
                    self.current_frame = i % len(self.frames)
                    
                    # Build text display
                    displayed_text = text[:i+1]
                    remaining = len(text) - (i+1)
                    if remaining > 0:
                        displayed_text += "█" + " " * (remaining - 1)
                    
                    # Clear screen and display
                    os.system('cls' if os.name == 'nt' else 'clear')
                    
                    console.print(Panel(
                        self.frames[self.current_frame], 
                        border_style=self.color,
                        box=box.ROUNDED,
                        title="AI Assistant",
                        title_align="center"
                    ))
                    
                    console.print(Panel(
                        displayed_text,
                        border_style=self.color,
                        title="Speaking",
                        title_align="center"
                    ))
                    
                    time.sleep(speed)
                    
                # Show complete text at the end
                os.system('cls' if os.name == 'nt' else 'clear')
                console.print(Panel(
                    self.frames[0], 
                    border_style=self.color,
                    box=box.ROUNDED,
                    title="AI Assistant",
                    title_align="center"
                ))
                
                console.print(Panel(
                    text,
                    border_style=self.color,
                    title="Message",
                    title_align="center"
                ))
            else:
                # Simple animation without rich
                for i, char in enumerate(text):
                    if self.stop_event.is_set():
                        break
                        
                    self.current_frame = i % len(self.frames)
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(self.frames[self.current_frame])
                    print("\n" + text[:i+1])
                    
                    time.sleep(speed)
                    
        except Exception as e:
            logger.error(f"Error in speaking animation: {e}")
    
    def create_custom_avatar(self, frames: List[str] = None) -> bool:
        """Create a new custom avatar"""
        if not frames:
            # Interactive avatar creation
            print("Creating a custom avatar")
            print("Enter avatar frames (empty line to finish):")
            
            frames = []
            frame_num = 1
            
            while True:
                print(f"\nEnter frame {frame_num} (empty line to finish):")
                frame_lines = []
                
                while True:
                    line = input()
                    if not line:
                        break
                    frame_lines.append(line)
                
                if not frame_lines:
                    break
                
                frames.append("\n".join(frame_lines))
                frame_num += 1
                
                if frame_num > 10:
                    print("Maximum frames reached (10)")
                    break
            
            if not frames:
                print("No frames entered, avatar creation cancelled")
                return False
        
        return self.save_custom_avatar(frames)