#!/usr/bin/env python3

"""
Triad Terminal Voice Integration
Integrates enhanced voice and avatar with terminal interface
"""

import logging
import threading
import time
from collections.abc import Callable
from typing import Any

from ai_avatar import AIAvatar

# Import our enhanced modules
from enhanced_voice import EnhancedVoice, VoiceCommandHandler


class VoiceInterface:
    """Integrated voice and avatar interface for the terminal"""

    def __init__(self, voice_dir: str = "~/.triad/voice", avatar_dir: str = "~/.triad/avatar"):
        # Initialize components
        self.voice = EnhancedVoice(voice_dir)
        self.avatar = AIAvatar(data_dir=avatar_dir)
        self.voice_handler = VoiceCommandHandler(self.voice)

        # State tracking
        self.speaking_lock = threading.Lock()
        self.command_callback = None
        self.auto_speak = True

        # Start voice wake word detection if enabled
        self.wake_thread = None
        self.stop_wake = threading.Event()

        # Try to initialize wake word detection if enabled
        if self.voice.config["voice_recognition_enabled"]:
            self._start_wake_detection()

    def speak(
        self, text: str, blocking: bool = False, with_avatar: bool = True, animation: bool = True
    ) -> None:
        """Speak text with optional avatar animation"""
        if not text:
            return

        with self.speaking_lock:
            if with_avatar and animation:
                # Start avatar speaking animation
                self.avatar.speak_animation(text, speed=0.03)

                # Wait a moment for animation to start
                time.sleep(0.1)

                # Speak text
                self.voice.speak(text, blocking=True)

                # Stop animation
                self.avatar.stop_animation()

            elif with_avatar:
                # Just display avatar
                self.avatar.display()
                self.voice.speak(text, blocking)

            else:
                # Just speak
                self.voice.speak(text, blocking)

    def process_voice_command(self, command: str) -> None:
        """Process a voice command"""
        if not command:
            return

        # Log the command
        logging.info(f"Processing voice command: {command}")

        # If we have a callback, use it
        if self.command_callback:
            # Create a copy to avoid callback changing during processing
            callback = self.command_callback

            # Acknowledge the command
            self.speak(f"Processing command: {command}", with_avatar=True, animation=False)

            # Call the callback
            try:
                callback(command)
            except Exception as e:
                logging.error(f"Error in voice command callback: {e}")
                self.speak("Sorry, there was an error processing that command.", with_avatar=True)
        else:
            # No callback registered
            self.speak("Voice command received, but no handler is registered.", with_avatar=True)

    def set_command_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback for voice commands"""
        self.command_callback = callback

    def _start_wake_detection(self) -> None:
        """Start listening for wake words"""
        try:
            import speech_recognition as sr

            self.stop_wake.clear()
            self.wake_thread = threading.Thread(target=self._wake_detection_loop)
            self.wake_thread.daemon = True
            self.wake_thread.start()

            logging.info("Started wake word detection")

        except ImportError:
            logging.warning("SpeechRecognition not available, wake word detection disabled")

    def _stop_wake_detection(self) -> None:
        """Stop wake word detection"""
        if self.wake_thread and self.wake_thread.is_alive():
            self.stop_wake.set()
            self.wake_thread.join(timeout=2.0)
            logging.info("Stopped wake word detection")

    def _wake_detection_loop(self) -> None:
        """Background thread for wake word detection"""
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # Wake words
        wake_words = ["hey triad", "okay triad", "hi triad", "triad"]

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source)

                while not self.stop_wake.is_set():
                    try:
                        # Listen for audio with a short timeout
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)

                        # Use Google's speech recognition
                        text = recognizer.recognize_google(audio).lower()

                        # Check for wake word
                        if any(wake_word in text for wake_word in wake_words):
                            logging.info(f"Wake word detected: {text}")

                            # Alert user we heard them
                            self.avatar.animate(duration=2.0)
                            self.voice.speak("Yes? How can I help?")

                            # Listen for command
                            try:
                                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                                command = recognizer.recognize_google(audio)

                                if command:
                                    # Process the command
                                    self.process_voice_command(command)

                            except sr.WaitTimeoutError:
                                self.voice.speak("Sorry, I didn't hear a command.")
                            except sr.UnknownValueError:
                                self.voice.speak("I didn't understand that command.")
                            except Exception as e:
                                logging.error(f"Error processing command: {e}")

                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError:
                        time.sleep(5)  # Wait before retrying if service unavailable
                    except Exception as e:
                        logging.error(f"Error in wake detection: {e}")
                        time.sleep(1)

        except Exception as e:
            logging.error(f"Error in wake detection loop: {e}")

    def start_continuous_listening(self) -> bool:
        """Start continuous listening for commands"""
        return self.voice_handler.start_listening(self.process_voice_command)

    def stop_continuous_listening(self) -> bool:
        """Stop continuous listening"""
        return self.voice_handler.stop_listening()

    def set_auto_speak(self, enabled: bool) -> None:
        """Enable/disable automatic text-to-speech"""
        self.auto_speak = enabled

    def change_avatar(self, style: str) -> None:
        """Change avatar style"""
        if style in self.avatar.AVATAR_STYLES:
            self.avatar.reset_to_default(style)
        else:
            logging.warning(f"Unknown avatar style: {style}")

    def change_voice(self, gender: str = None, rate: float = None, engine: str = None) -> None:
        """Change voice settings"""
        self.voice.set_voice(gender=gender, rate=rate, engine=engine)

    def get_voice_settings(self) -> dict[str, Any]:
        """Get current voice settings"""
        return self.voice.config

    def update_voice_settings(self, settings: dict[str, Any]) -> None:
        """Update multiple voice settings at once"""
        if "voice_gender" in settings:
            self.voice.set_voice(gender=settings["voice_gender"])

        if "speaking_rate" in settings:
            self.voice.set_voice(rate=settings["speaking_rate"])

        if "preferred_engine" in settings:
            self.voice.set_voice(engine=settings["preferred_engine"])

        if "voice_type" in settings:
            self.voice.set_voice(voice_type=settings["voice_type"])

    def cleanup(self) -> None:
        """Clean up resources"""
        self._stop_wake_detection()
        self.stop_continuous_listening()


class CommandLineVoiceInterface:
    """Simple command-line interface for testing voice features"""

    def __init__(self):
        self.voice_interface = VoiceInterface()
        self.voice_interface.set_command_callback(self.handle_voice_command)

    def start(self) -> None:
        """Start the command-line interface"""
        print("\nTriad Terminal Voice Interface")
        print("============================")
        print("Available commands:")
        print("  speak <text>     - Speak the specified text")
        print("  avatar <style>   - Change avatar style (robot, brain, ghost, pixel)")
        print("  voice <setting>  - Change voice (male, female, neutral, fast, slow)")
        print("  listen           - Start continuous listening")
        print("  stop             - Stop listening")
        print("  test             - Run voice and avatar test")
        print("  settings         - Show current settings")
        print("  exit             - Exit the program")

        # Show the avatar
        self.voice_interface.avatar.display()

        # Welcome message
        self.voice_interface.speak("Welcome to Triad Terminal Voice Interface. How can I help you?")

        # Command loop
        while True:
            try:
                cmd = input("\n> ").strip()

                if not cmd:
                    continue

                if cmd.startswith("speak "):
                    text = cmd[6:]
                    self.voice_interface.speak(text)

                elif cmd.startswith("avatar "):
                    style = cmd[7:]
                    self.voice_interface.change_avatar(style)
                    self.voice_interface.avatar.display()

                elif cmd.startswith("voice "):
                    setting = cmd[6:]
                    if setting == "male":
                        self.voice_interface.change_voice(gender="male")
                        print("Voice set to male")
                    elif setting == "female":
                        self.voice_interface.change_voice(gender="female")
                        print("Voice set to female")
                    elif setting == "neutral":
                        self.voice_interface.change_voice(gender="neutral")
                        print("Voice set to neutral")
                    elif setting == "fast":
                        self.voice_interface.change_voice(rate=1.5)
                        print("Voice set to fast")
                    elif setting == "slow":
                        self.voice_interface.change_voice(rate=0.8)
                        print("Voice set to slow")
                    else:
                        print(f"Unknown voice setting: {setting}")

                elif cmd == "listen":
                    if self.voice_interface.start_continuous_listening():
                        print("Listening for commands... (say 'stop listening' to stop)")
                    else:
                        print("Failed to start listening")

                elif cmd == "stop":
                    if self.voice_interface.stop_continuous_listening():
                        print("Stopped listening")
                    else:
                        print("Not currently listening")

                elif cmd == "test":
                    self._run_test()

                elif cmd == "settings":
                    self._show_settings()

                elif cmd == "exit":
                    self.voice_interface.speak("Goodbye!", blocking=True)
                    break

                else:
                    print(f"Unknown command: {cmd}")

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")

        # Clean up
        self.voice_interface.cleanup()

    def handle_voice_command(self, command: str) -> None:
        """Handle voice commands"""
        print(f"\nVoice command: {command}")

        # Process simple commands
        if "stop listening" in command.lower():
            self.voice_interface.speak("Stopping voice recognition")
            self.voice_interface.stop_continuous_listening()

        elif "what time" in command.lower():
            import datetime

            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.voice_interface.speak(f"The current time is {current_time}")

        elif "your name" in command.lower():
            self.voice_interface.speak("My name is Triad Terminal Assistant. I'm here to help you.")

        else:
            self.voice_interface.speak(f"I heard your command: {command}")

    def _run_test(self) -> None:
        """Run a test of voice and avatar features"""
        print("\nRunning voice and avatar test...")

        # Test avatar animation
        print("Testing avatar animation...")
        self.voice_interface.avatar.animate(duration=3.0)

        # Test different voices
        print("\nTesting different voices...")

        print("Default voice:")
        self.voice_interface.change_voice(gender="neutral", rate=1.0)
        self.voice_interface.speak(
            "This is the default voice of the Triad Terminal system.", blocking=True
        )

        print("Male voice:")
        self.voice_interface.change_voice(gender="male")
        self.voice_interface.speak("This is the male voice option.", blocking=True)

        print("Female voice:")
        self.voice_interface.change_voice(gender="female")
        self.voice_interface.speak("This is the female voice option.", blocking=True)

        print("Fast voice:")
        self.voice_interface.change_voice(rate=1.5)
        self.voice_interface.speak(
            "This is a faster speaking rate for when you need information quickly.", blocking=True
        )

        print("Slow voice:")
        self.voice_interface.change_voice(rate=0.8)
        self.voice_interface.speak(
            "This is a slower speaking rate for clearer communication.", blocking=True
        )

        # Reset to default
        self.voice_interface.change_voice(gender="neutral", rate=1.0)

        # Test speaking with avatar
        print("\nTesting speaking with avatar animation...")
        self.voice_interface.speak(
            "The Triad Terminal system integrates advanced voice synthesis with visual avatar animation to provide an intuitive and responsive interface experience.",
            with_avatar=True,
            animation=True,
            blocking=True,
        )

        print("\nVoice and avatar test complete!")

    def _show_settings(self) -> None:
        """Show current settings"""
        voice_settings = self.voice_interface.get_voice_settings()

        print("\nCurrent Voice Settings:")
        print(f"  Engine: {voice_settings.get('preferred_engine', 'auto')}")
        print(f"  Voice Type: {voice_settings.get('voice_type', 'default')}")
        print(f"  Voice Gender: {voice_settings.get('voice_gender', 'neutral')}")
        print(f"  Speaking Rate: {voice_settings.get('speaking_rate', 1.0)}")
        print(f"  Pitch: {voice_settings.get('pitch', 1.0)}")
        print(f"  Volume: {voice_settings.get('volume', 0.8)}")
        print(f"  TTS Enabled: {voice_settings.get('tts_enabled', True)}")
        print(f"  Voice Recognition: {voice_settings.get('voice_recognition_enabled', False)}")

        print("\nAvailable TTS Engines:")
        for engine_name, engine_data in self.voice_interface.voice.tts_engines.items():
            print(
                f"  - {engine_name} ({engine_data.get('type', 'unknown')}, {engine_data.get('quality', 'unknown')} quality)"
            )


def main() -> None:
    """Main entry point"""
    cli = CommandLineVoiceInterface()
    cli.start()


if __name__ == "__main__":
    main()
