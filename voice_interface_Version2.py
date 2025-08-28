#!/usr/bin/env python3

"""
Triad Terminal Voice Interface
Provides text-to-speech and speech recognition capabilities
"""

from __future__ import annotations

import os
import json
import time
import logging
import threading
import tempfile
import math
import wave
import array
from typing import Dict, Tuple, List, Any, Optional, Callable

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

class VoiceManager:
    """Manages voice interaction capabilities"""
    
    def __init__(self, config_dir: str = "~/.triad/voice"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "voice_config.json")
        
        # Default configuration
        self.default_config = {
            "tts_enabled": True,
            "voice_recognition_enabled": False,
            "voice_trigger_phrase": "hey triad",
            "voice_type": "default",
            "volume": 80,
            "speaking_rate": 1.0,
            "notification_sounds": True
        }
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize TTS engine
        self.tts_engine: Optional[Any] = None
        self.stt_engine: Optional[Any] = None
        self._init_voice_engines()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load voice configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                # Update with any missing default values
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                logger.error(f"Error loading voice config: {e}")
        
        # If no config file or error, use defaults and create config
        self._save_config(self.default_config)
        return dict(self.default_config)
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save voice configuration"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving voice config: {e}")
    
    def _init_voice_engines(self) -> None:
        """Initialize text-to-speech and speech recognition engines"""
        self._init_tts()
        self._init_stt()
    
    def _init_tts(self) -> None:
        """Initialize text-to-speech engine"""
        if not self.config["tts_enabled"]:
            return
        
        # Try different TTS libraries in order of preference
        try:
            # Try pyttsx3 first (offline, works on most platforms)
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure the engine
            self.tts_engine.setProperty('rate', int(self.config["speaking_rate"]
