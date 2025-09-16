#!/usr/bin/env python3

"""
Triad Terminal Voice Interface
Provides text-to-speech and speech recognition capabilities
"""

from __future__ import annotations

import array
import contextlib
import json
import logging
import math
import os
import tempfile
import threading
import time
import wave
from collections.abc import Callable
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
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
            "notification_sounds": True,
        }

        # Load configuration
        self.config = self._load_config()

        # Initialize TTS engine
        self.tts_engine: Any | None = None
        self.stt_engine: Any | None = None
        self._init_voice_engines()

    def _load_config(self) -> dict[str, Any]:
        """Load voice configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
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

    def _save_config(self, config: dict[str, Any]) -> None:
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
            self.tts_engine.setProperty("rate", int(self.config["speaking_rate"] * 200))  # Speed
            self.tts_engine.setProperty("volume", self.config["volume"] / 100)  # Volume (0-1)

            # Set voice type if available
            voices = self.tts_engine.getProperty("voices")
            voice_type = self.config["voice_type"].lower()

            for voice in voices:
                # Try to match the requested voice type
                if voice_type in voice.name.lower():
                    self.tts_engine.setProperty("voice", voice.id)
                    break

            logger.info("Initialized pyttsx3 TTS engine")
            return
        except ImportError:
            logger.warning("pyttsx3 not available, trying alternative TTS engines")
        except Exception as e:
            logger.warning(f"pyttsx3 initialization failed: {e}. Trying alternative TTS engines.")

        try:
            # Try gTTS with playsound (online, requires internet)
            import playsound
            from gtts import gTTS

            # Wrapper to make it compatible with our interface
            class GTTSWrapper:
                def __init__(self, volume=0.8, rate=1.0):
                    self.volume = volume
                    self.rate = rate
                    self.temp_dir = tempfile.gettempdir()

                def say(self, text):
                    try:
                        # Generate unique filename (same text -> same name, fine for temps)
                        temp_file = os.path.join(
                            self.temp_dir, f"tts_{(hash(text) & 0xffffffff)}.mp3"
                        )

                        # Generate speech
                        tts = gTTS(text=text, lang="en", slow=(self.rate < 0.9))
                        tts.save(temp_file)

                        # Play the audio (blocking to serialize playback)
                        playsound.playsound(temp_file, True)

                        # Clean up
                        with contextlib.suppress(Exception):
                            os.remove(temp_file)
                    except Exception as e:
                        logger.error(f"TTS (gTTS) error: {e}")

                def runAndWait(self):
                    # Not needed for this wrapper
                    pass

            self.tts_engine = GTTSWrapper(
                volume=self.config["volume"] / 100, rate=self.config["speaking_rate"]
            )

            logger.info("Initialized gTTS engine")
            return
        except ImportError:
            logger.warning("gTTS/playsound not available")
        except Exception as e:
            logger.warning(f"gTTS initialization failed: {e}")

        # If we get here, we couldn't initialize any TTS engine
        logger.error("No TTS engine available. Install pyttsx3 or gtts+playsound")
        self.config["tts_enabled"] = False
        self._save_config(self.config)

    def _init_stt(self) -> None:
        """Initialize speech recognition engine"""
        if not self.config["voice_recognition_enabled"]:
            return

        try:
            # Try speech_recognition library
            import speech_recognition as sr

            self.stt_engine = sr.Recognizer()
            logger.info("Initialized speech recognition engine")
        except ImportError:
            logger.warning("speech_recognition not available, voice input disabled")
            self.config["voice_recognition_enabled"] = False
            self._save_config(self.config)
        except Exception as e:
            logger.warning(f"Speech recognition initialization failed: {e}")
            self.config["voice_recognition_enabled"] = False
            self._save_config(self.config)

    def speak(self, text: str, blocking: bool = False) -> None:
        """Convert text to speech"""
        if not self.config["tts_enabled"] or not self.tts_engine:
            return

        def _speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS error: {e}")

        if blocking:
            _speak_thread()
        else:
            # Run in a separate thread to avoid blocking
            thread = threading.Thread(target=_speak_thread)
            thread.daemon = True
            thread.start()

    def listen(self, timeout: int = 5, phrase_time_limit: int = 5) -> str | None:
        """Listen for speech and convert to text"""
        if not self.config["voice_recognition_enabled"] or not self.stt_engine:
            return None

        try:
            import speech_recognition as sr

            with sr.Microphone() as source:
                logger.info("Listening...")
                # Adjust for ambient noise
                self.stt_engine.adjust_for_ambient_noise(source)
                # Listen for audio
                audio = self.stt_engine.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )

                try:
                    # Use Google's speech recognition
                    text = self.stt_engine.recognize_google(audio)
                    logger.info(f"Recognized: {text}")
                    return text
                except sr.UnknownValueError:
                    logger.info("Speech not understood")
                    return None
                except sr.RequestError as e:
                    logger.error(f"Speech recognition service error: {e}")
                    return None
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return None

    def listen_for_trigger(
        self, callback: Callable[[str], None], stop_event: threading.Event
    ) -> None:
        """Listen continuously for trigger phrase"""
        if not self.config["voice_recognition_enabled"] or not self.stt_engine:
            return

        trigger_phrase = self.config["voice_trigger_phrase"].lower()

        try:
            import speech_recognition as sr

            with sr.Microphone() as source:
                logger.info(f"Listening for trigger phrase: '{trigger_phrase}'")
                self.stt_engine.adjust_for_ambient_noise(source)

                while not stop_event.is_set():
                    try:
                        audio = self.stt_engine.listen(source, timeout=1, phrase_time_limit=3)
                        try:
                            text = self.stt_engine.recognize_google(audio).lower()
                            logger.info(f"Heard: {text}")

                            if trigger_phrase in text:
                                logger.info("Trigger phrase detected")
                                # Play acknowledgement sound if enabled
                                if self.config["notification_sounds"]:
                                    self._play_notification("activation")

                                # Wait a moment for follow-up command
                                time.sleep(0.5)
                                callback(text.replace(trigger_phrase, "").strip())
                        except sr.UnknownValueError:
                            pass  # Speech wasn't understood, just continue listening
                        except sr.RequestError:
                            # If we can't reach the service, take a short break
                            time.sleep(5)
                    except Exception:
                        # Any other error, just continue
                        time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in trigger listener: {e}")

    def start_voice_assistant(self, command_handler: Callable[[str], str]) -> threading.Event:
        """Start voice assistant in background thread"""
        stop_event = threading.Event()

        def voice_assistant_thread():
            def on_trigger_detected(command_text):
                if not command_text:
                    # If no command was included with the trigger, listen for one
                    self.speak("How can I help?")
                    command_text_local = self.listen(timeout=5, phrase_time_limit=5)
                else:
                    command_text_local = command_text

                if command_text_local:
                    # Process the command
                    response = command_handler(command_text_local)
                    # Speak the response
                    if response:
                        self.speak(response)

            self.listen_for_trigger(on_trigger_detected, stop_event)

        # Start the voice assistant thread
        thread = threading.Thread(target=voice_assistant_thread)
        thread.daemon = True
        thread.start()

        return stop_event

    def _play_notification(self, sound_type: str = "notification") -> None:
        """Play a notification sound"""
        if not self.config["notification_sounds"]:
            return

        try:
            import playsound

            # Map of sound types to filenames (use WAV, since we write WAV data)
            sounds = {
                "notification": "notification.wav",
                "activation": "activation.wav",
                "error": "error.wav",
                "success": "success.wav",
            }

            sound_file = os.path.join(
                self.config_dir, "sounds", sounds.get(sound_type, "notification.wav")
            )

            # Ensure sounds directory exists
            sounds_dir = os.path.join(self.config_dir, "sounds")
            os.makedirs(sounds_dir, exist_ok=True)

            # Generate sound if missing
            if not os.path.exists(sound_file) or os.path.getsize(sound_file) == 0:
                self._generate_notification_sound(sound_type, sound_file)

            # Play the sound (non-blocking)
            playsound.playsound(sound_file, block=False)
        except ImportError:
            logger.warning("playsound not available, notification sounds disabled")
        except Exception as e:
            logger.error(f"Error playing notification sound: {e}")

    def _generate_notification_sound(self, sound_type: str, output_file: str) -> None:
        """Generate a simple notification sound as WAV without external deps"""
        try:
            sample_rate = 44100
            duration = 0.12  # seconds
            amplitude = int(0.3 * 32767)

            def gen_tone(freq: float, dur: float) -> array.array:
                n_samples = int(sample_rate * dur)
                data = array.array("h")
                for i in range(n_samples):
                    # simple sine wave
                    sample = int(amplitude * math.sin(2 * math.pi * freq * (i / sample_rate)))
                    data.append(sample)
                return data

            # Build pattern by type
            if sound_type == "activation":
                data = gen_tone(440, 0.08) + gen_tone(880, 0.08)
            elif sound_type == "error":
                data = gen_tone(880, 0.08) + gen_tone(440, 0.08)
            elif sound_type == "success":
                # Short pleasant chord (C5-E5-G5)
                dur = 0.18
                n_samples = int(sample_rate * dur)
                data = array.array("h")
                freqs = [523.25, 659.25, 783.99]
                for i in range(n_samples):
                    val = sum(math.sin(2 * math.pi * f * (i / sample_rate)) for f in freqs) / len(
                        freqs
                    )
                    sample = int(amplitude * val)
                    data.append(sample)
            else:
                # Default beep
                data = gen_tone(440, duration)

            # Write WAV
            with wave.open(output_file, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(44100)
                wf.writeframes(data.tobytes())

            logger.info(f"Generated notification sound: {output_file}")
        except Exception as e:
            logger.warning(f"Could not generate notification sound ({sound_type}): {e}")
            # Create an empty file as a placeholder
            try:
                with open(output_file, "wb") as f:
                    f.write(b"")
            except Exception:
                pass


class VoiceCommands:
    """Handles voice command parsing and execution"""

    def __init__(self, voice_manager: VoiceManager):
        self.voice_manager = voice_manager

        # Define common command patterns
        self.commands = {
            "help": ["help", "what can you do", "commands", "show help"],
            "open": ["open", "launch", "start", "run"],
            "close": ["close", "exit", "quit", "stop"],
            "deploy": ["deploy", "publish", "upload"],
            "status": ["status", "info", "how is", "what is the status"],
        }

    def parse_command(self, text: str) -> tuple[str, dict[str, str]]:
        """Parse voice command into command type and arguments"""
        text = text.lower().strip()

        # Try to match command patterns
        command_type: str | None = None
        for cmd, patterns in self.commands.items():
            for pattern in patterns:
                if text.startswith(pattern):
                    command_type = cmd
                    text = text[len(pattern) :].strip()
                    break
            if command_type:
                break

        # If no specific command was identified, treat as a generic query
        if not command_type:
            command_type = "query"

        # Extract parameters based on command type
        params: dict[str, str] = {}

        if command_type == "open":
            # Extract what to open
            params["target"] = text

        elif command_type == "deploy":
            # Extract deployment target
            if " to " in text:
                parts = text.split(" to ", 1)
                params["project"] = parts[0].strip()
                params["target"] = parts[1].strip()
            else:
                params["project"] = text

        elif command_type == "status":
            # Extract what to check status of
            params["target"] = text

        return command_type, params

    def execute_command(self, text: str) -> str:
        """Execute a voice command and return response"""
        command_type, params = self.parse_command(text)

        # Simple command handling
        if command_type == "help":
            return self._help_command()

        elif command_type == "open":
            return self._open_command(params.get("target", ""))

        elif command_type == "close":
            return "Closing application"

        elif command_type == "deploy":
            return self._deploy_command(
                params.get("project", ""), params.get("target", "production")
            )

        elif command_type == "status":
            return self._status_command(params.get("target", "system"))

        else:
            # Generic query handling
            return f"I heard you say: {text}. This command isn't fully implemented yet."

    def _help_command(self) -> str:
        """Handle help command"""
        return (
            "I can help you with various tasks. Try commands like: "
            "Open a project, Deploy an application, Check system status, or Close an application."
        )

    def _open_command(self, target: str) -> str:
        """Handle open command"""
        if not target:
            return "Please specify what you'd like to open."

        # Handle common targets
        if "project" in target:
            return "Opening project manager"
        elif "terminal" in target or "shell" in target:
            return "Opening terminal"
        elif "editor" in target or "code" in target:
            return "Opening code editor"
        elif "browser" in target or "web" in target:
            return "Opening web browser"
        elif "settings" in target or "preferences" in target:
            return "Opening settings"
        else:
            return f"Opening {target}"

    def _deploy_command(self, project: str, target: str) -> str:
        """Handle deploy command"""
        if not project:
            return "Please specify what project you'd like to deploy."

        return f"Starting deployment of {project} to {target}"

    def _status_command(self, target: str) -> str:
        """Handle status command"""
        if "system" in target:
            return "System status: All services operational"
        elif "network" in target:
            return "Network status: Connected"
        elif "deployment" in target or "deploy" in target:
            return "Deployment status: No active deployments"
        elif "project" in target:
            return "Project status: 3 projects active"
        else:
            return f"Status of {target}: Unknown"
