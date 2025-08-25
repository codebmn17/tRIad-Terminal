#!/usr/bin/env python3

"""
Triad Terminal Enhanced Voice Interface
Provides high-quality text-to-speech and voice recognition
"""

import os
import sys
import json
import time
import logging
import threading
import tempfile
import subprocess
import queue
from typing import Dict, List, Any, Optional, Callable, Union

logger = logging.getLogger("triad.voice")

class EnhancedVoice:
    """Enhanced voice capabilities with multiple TTS engines and voice options"""
    
    def __init__(self, config_dir: str = "~/.triad/voice"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "voice_config.json")
        
        # Default configuration
        self.default_config = {
            "tts_enabled": True,
            "voice_recognition_enabled": False,
            "preferred_engine": "auto",  # auto, pyttsx3, gtts, espeak, mimic3, azure, elevenlabs
            "voice_type": "default",     # voice id/name for the selected engine
            "voice_gender": "neutral",   # male, female, neutral
            "speaking_rate": 1.0,        # Speed multiplier: 0.5 to 2.0
            "pitch": 1.0,                # Pitch multiplier: 0.5 to 2.0
            "volume": 0.8,               # Volume: 0.0 to 1.0
            "api_keys": {                # API keys for cloud services
                "azure": "",
                "elevenlabs": ""
            },
            "auto_caption": True,        # Show text when speaking
            "audio_effects": {           # Audio post-processing
                "reverb": 0.0,           # 0.0 to 1.0
                "echo": 0.0,             # 0.0 to 1.0
                "equalization": "neutral" # bass, neutral, treble
            }
        }
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize TTS engines
        self.tts_engines = {}
        self.speech_queue = queue.Queue()
        self.speaking_thread = None
        self.stop_speaking = threading.Event()
        
        # Start speech thread
        self._start_speech_thread()
        
        # Initialize available engines
        self._initialize_engines()
    
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
                    elif key == "api_keys" and isinstance(value, dict):
                        for api, default_key in value.items():
                            if api not in config[key]:
                                config[key][api] = default_key
                return config
            except Exception as e:
                logger.error(f"Error loading voice config: {e}")
        
        # If no config file or error, use defaults and create config
        self._save_config(self.default_config)
        return self.default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save voice configuration"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving voice config: {e}")
    
    def _initialize_engines(self) -> None:
        """Initialize available TTS engines"""
        # Try to initialize pyttsx3 (offline TTS)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Configure the engine
            engine.setProperty('rate', int(self.config["speaking_rate"] * 200))
            engine.setProperty('volume', self.config["volume"])
            
            # Set voice type if available
            voices = engine.getProperty('voices')
            
            # Try to find appropriate voice based on gender preference
            gender = self.config["voice_gender"]
            voice_type = self.config["voice_type"]
            
            # Default to first voice
            selected_voice = voices[0].id if voices else None
            
            # Try to match gender and/or name
            for voice in voices:
                voice_name = voice.name.lower()
                
                # Match specific voice if requested
                if voice_type != "default" and voice_type.lower() in voice_name:
                    selected_voice = voice.id
                    break
                    
                # Otherwise match gender
                elif gender == "male" and ("male" in voice_name or "david" in voice_name or "george" in voice_name):
                    selected_voice = voice.id
                    break
                elif gender == "female" and ("female" in voice_name or "zira" in voice_name or "heera" in voice_name):
                    selected_voice = voice.id
                    break
            
            if selected_voice:
                engine.setProperty('voice', selected_voice)
            
            self.tts_engines["pyttsx3"] = {
                "engine": engine,
                "type": "offline",
                "quality": "medium"
            }
            logger.info("Initialized pyttsx3 TTS engine")
        except ImportError:
            logger.warning("pyttsx3 not available")
        except Exception as e:
            logger.error(f"Error initializing pyttsx3: {e}")
        
        # Try to initialize gTTS (online Google TTS)
        try:
            from gtts import gTTS
            import playsound
            
            self.tts_engines["gtts"] = {
                "engine": "gtts",
                "type": "online",
                "quality": "high",
                "dependencies": {
                    "gtts": gTTS,
                    "playsound": playsound
                }
            }
            logger.info("Initialized Google TTS engine")
        except ImportError:
            logger.warning("gtts not available")
        except Exception as e:
            logger.error(f"Error initializing gtts: {e}")
        
        # Try to check for eSpeak (command-line TTS)
        try:
            result = subprocess.run(['espeak', '--version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            if result.returncode == 0:
                self.tts_engines["espeak"] = {
                    "engine": "espeak",
                    "type": "offline",
                    "quality": "low"
                }
                logger.info("Initialized eSpeak TTS engine")
        except Exception:
            logger.warning("espeak not available")
        
        # Try to check for Mimic3 (high quality offline TTS)
        try:
            result = subprocess.run(['mimic3', '--version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            if result.returncode == 0:
                self.tts_engines["mimic3"] = {
                    "engine": "mimic3",
                    "type": "offline",
                    "quality": "high"
                }
                logger.info("Initialized Mimic3 TTS engine")
        except Exception:
            logger.warning("mimic3 not available")
        
        # Check for ElevenLabs API key (premium quality voice)
        if self.config["api_keys"]["elevenlabs"]:
            self.tts_engines["elevenlabs"] = {
                "engine": "elevenlabs",
                "type": "online",
                "quality": "premium"
            }
            logger.info("ElevenLabs TTS available")
        
        # Check for Azure API key (high quality voice)
        if self.config["api_keys"]["azure"]:
            self.tts_engines["azure"] = {
                "engine": "azure",
                "type": "online",
                "quality": "high"
            }
            logger.info("Azure TTS available")
        
        logger.info(f"Initialized {len(self.tts_engines)} TTS engines")
    
    def _start_speech_thread(self) -> None:
        """Start the background speech processing thread"""
        self.stop_speaking.clear()
        self.speaking_thread = threading.Thread(target=self._speech_worker)
        self.speaking_thread.daemon = True
        self.speaking_thread.start()
    
    def _speech_worker(self) -> None:
        """Background worker that processes the speech queue"""
        while not self.stop_speaking.is_set():
            try:
                # Get next item with a timeout to allow checking stop flag
                item = self.speech_queue.get(timeout=0.5)
                
                if item is None:
                    continue
                    
                text = item.get("text", "")
                engine_name = item.get("engine")
                blocking = item.get("blocking", False)
                
                if not text:
                    continue
                    
                # Speak the text
                self._speak_with_engine(text, engine_name)
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in speech worker: {e}")
    
    def _speak_with_engine(self, text: str, engine_name: Optional[str] = None) -> None:
        """Speak text using specified or default engine"""
        if not self.config["tts_enabled"]:
            return
            
        # Select appropriate engine
        if not engine_name or engine_name == "auto":
            engine_name = self.config["preferred_engine"]
            
            # If still auto, select best available
            if engine_name == "auto":
                # Check for premium quality first
                for name, engine in self.tts_engines.items():
                    if engine.get("quality") == "premium":
                        engine_name = name
                        break
                        
                # Then high quality
                if engine_name == "auto":
                    for name, engine in self.tts_engines.items():
                        if engine.get("quality") == "high":
                            engine_name = name
                            break
                            
                # Then any available
                if engine_name == "auto" and self.tts_engines:
                    engine_name = list(self.tts_engines.keys())[0]
        
        # If specified engine not available, use first available
        if engine_name not in self.tts_engines and self.tts_engines:
            engine_name = list(self.tts_engines.keys())[0]
        
        # If no engines available, return silently
        if not self.tts_engines:
            logger.warning("No TTS engines available")
            return
        
        # Get the engine
        engine_data = self.tts_engines[engine_name]
        
        try:
            # Apply text preprocessing
            text = self._preprocess_text(text)
            
            # Speak with appropriate engine
            if engine_name == "pyttsx3":
                engine = engine_data["engine"]
                engine.say(text)
                engine.runAndWait()
                
            elif engine_name == "gtts":
                # Use Google TTS
                gTTS = engine_data["dependencies"]["gtts"]
                playsound = engine_data["dependencies"]["playsound"]
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    temp_filename = tmp_file.name
                
                try:
                    # Generate speech
                    tts = gTTS(text=text, lang='en', slow=(self.config["speaking_rate"] < 0.9))
                    tts.save(temp_filename)
                    
                    # Play the audio
                    playsound.playsound(temp_filename, True)
                finally:
                    # Clean up
                    if os.path.exists(temp_filename):
                        os.unlink(temp_filename)
                        
            elif engine_name == "espeak":
                # Use espeak command line
                gender_flag = ""
                if self.config["voice_gender"] == "male":
                    gender_flag = "-m"
                elif self.config["voice_gender"] == "female":
                    gender_flag = "-f"
                    
                rate = int(175 * self.config["speaking_rate"])
                
                cmd = ["espeak"]
                if gender_flag:
                    cmd.append(gender_flag)
                    
                cmd.extend([
                    "-a", str(int(self.config["volume"] * 100)),
                    "-s", str(rate),
                    "-p", str(int(50 * self.config["pitch"])),
                    text
                ])
                
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            elif engine_name == "mimic3":
                # Use mimic3 command line
                voice = self.config["voice_type"]
                if voice == "default":
                    voice = "en_US/cmu-arctic_low"  # Default voice
                    
                cmd = [
                    "mimic3",
                    "--voice", voice,
                    "--length-scale", str(1.0 / self.config["speaking_rate"]),
                    text
                ]
                
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            elif engine_name == "elevenlabs":
                # Use ElevenLabs API
                self._speak_with_elevenlabs(text)
                
            elif engine_name == "azure":
                # Use Azure API
                self._speak_with_azure(text)
                
        except Exception as e:
            logger.error(f"Error speaking with {engine_name}: {e}")
    
    def _speak_with_elevenlabs(self, text: str) -> None:
        """Speak using ElevenLabs API"""
        try:
            import requests
            
            api_key = self.config["api_keys"]["elevenlabs"]
            voice_id = self.config["voice_type"]
            
            # Use a default voice if not specified
            if voice_id == "default":
                voice_id = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs default voice ID
            
            # API endpoint
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            # Request headers
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            # Request body
            body = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            # Make request
            response = requests.post(url, json=body, headers=headers)
            
            if response.status_code == 200:
                # Create temporary file for audio
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    temp_filename = tmp_file.name
                
                try:
                    # Play the audio
                    if sys.platform == 'darwin':  # macOS
                        subprocess.run(["afplay", temp_filename], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
                    elif sys.platform == 'win32':  # Windows
                        from playsound import playsound
                        playsound(temp_filename)
                    else:  # Linux and others
                        subprocess.run(["mpg123", "-q", temp_filename], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
                finally:
                    # Clean up
                    if os.path.exists(temp_filename):
                        os.unlink(temp_filename)
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error using ElevenLabs TTS: {e}")
    
    def _speak_with_azure(self, text: str) -> None:
        """Speak using Azure Cognitive Services"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            api_key = self.config["api_keys"]["azure"]
            region = "eastus"  # Default region
            
            # Configure speech config
            speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
            
            # Set speech synthesis voice
            voice = self.config["voice_type"]
            if voice == "default":
                if self.config["voice_gender"] == "male":
                    voice = "en-US-GuyNeural"
                elif self.config["voice_gender"] == "female":
                    voice = "en-US-JennyNeural"
                else:
                    voice = "en-US-AriaNeural"
                    
            speech_config.speech_synthesis_voice_name = voice
            
            # Configure speech synthesis
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
            
            # Add SSML for rate and pitch control
            rate = self.config["speaking_rate"]
            pitch = self.config["pitch"]
            
            ssml_text = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{voice}">
                    <prosody rate="{rate*100:.0f}%" pitch="{pitch*100:.0f}%">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Synthesize speech
            result = speech_synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("Azure speech synthesis completed")
            else:
                logger.error(f"Azure speech synthesis failed: {result.reason}")
                
        except Exception as e:
            logger.error(f"Error using Azure TTS: {e}")
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better speech quality"""
        # Replace common abbreviations and symbols
        replacements = {
            "e.g.": "for example",
            "i.e.": "that is",
            "etc.": "et cetera",
            "vs.": "versus",
            "approx.": "approximately",
            "@": "at",
            "URLs": "U R Ls",
            "URL": "U R L",
            "APIs": "A P Is",
            "API": "A P I",
            "UI": "U I",
            "JSON": "Jason",
            "YAML": "Yammel",
            "SQL": "sequel",
            "NoSQL": "No sequel",
            "GPIO": "G P I O",
            "MQTT": "M Q T T"
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        # Add pauses with commas for long sentences without punctuation
        words = text.split()
        if len(words) > 15 and text.count(',') < len(words) / 15:
            new_text = []
            for i in range(0, len(words), 8):
                chunk = words[i:i+8]
                new_text.append(" ".join(chunk))
            text = ", ".join(new_text)
        
        return text
    
    def speak(self, text: str, blocking: bool = False, engine: str = None) -> None:
        """Speak text using configured TTS engine"""
        if not self.config["tts_enabled"]:
            return
            
        # Add to speech queue
        self.speech_queue.put({
            "text": text,
            "engine": engine,
            "blocking": blocking
        })
        
        # If blocking, wait for speech to complete
        if blocking:
            self.speech_queue.join()
    
    def set_voice(self, gender: str = None, voice_type: str = None, 
                 rate: float = None, pitch: float = None,
                 engine: str = None) -> None:
        """Update voice settings"""
        changed = False
        
        if gender and gender in ["male", "female", "neutral"]:
            self.config["voice_gender"] = gender
            changed = True
            
        if voice_type:
            self.config["voice_type"] = voice_type
            changed = True
            
        if rate is not None and 0.5 <= rate <= 2.0:
            self.config["speaking_rate"] = rate
            changed = True
            
        if pitch is not None and 0.5 <= pitch <= 2.0:
            self.config["pitch"] = pitch
            changed = True
            
        if engine:
            if engine == "auto" or engine in self.tts_engines:
                self.config["preferred_engine"] = engine
                changed = True
        
        # Save config if changed
        if changed:
            self._save_config(self.config)
            
            # Update engine settings
            if "pyttsx3" in self.tts_engines:
                engine = self.tts_engines["pyttsx3"]["engine"]
                engine.setProperty('rate', int(self.config["speaking_rate"] * 200))
                engine.setProperty('volume', self.config["volume"])
    
    def get_available_voices(self) -> Dict[str, List[Dict[str, str]]]:
        """Get available voices for all engines"""
        available_voices = {}
        
        # Get pyttsx3 voices
        if "pyttsx3" in self.tts_engines:
            try:
                engine = self.tts_engines["pyttsx3"]["engine"]
                voices = engine.getProperty('voices')
                
                available_voices["pyttsx3"] = []
                for voice in voices:
                    gender = "unknown"
                    if "male" in voice.name.lower():
                        gender = "male"
                    elif "female" in voice.name.lower():
                        gender = "female"
                        
                    available_voices["pyttsx3"].append({
                        "id": voice.id,
                        "name": voice.name,
                        "gender": gender,
                        "languages": voice.languages
                    })
            except Exception as e:
                logger.error(f"Error getting pyttsx3 voices: {e}")
        
        # Add standard voices for other engines
        if "gtts" in self.tts_engines:
            available_voices["gtts"] = [
                {"id": "default", "name": "Google TTS Default", "gender": "female"}
            ]
            
        if "espeak" in self.tts_engines:
            available_voices["espeak"] = [
                {"id": "default", "name": "eSpeak Default", "gender": "neutral"},
                {"id": "male", "name": "eSpeak Male", "gender": "male"},
                {"id": "female", "name": "eSpeak Female", "gender": "female"}
            ]
            
        if "mimic3" in self.tts_engines:
            available_voices["mimic3"] = [
                {"id": "en_US/cmu-arctic_low", "name": "CMU Arctic", "gender": "male"},
                {"id": "en_US/ljspeech_low", "name": "LJ Speech", "gender": "female"},
                {"id": "en_UK/apope_low", "name": "APope", "gender": "male"}
            ]
        
        # ElevenLabs and Azure have many voices, but require API calls to get them all
        # For simplicity, just list a few common ones
        if "elevenlabs" in self.tts_engines:
            available_voices["elevenlabs"] = [
                {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
                {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female"},
                {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female"},
                {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male"},
                {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female"},
                {"id": "VR6AewLTigWG4xSOukaG", "name": "Adam", "gender": "male"},
                {"id": "pNInz6obpgDQGcFmaJgB", "name": "Sam", "gender": "male"}
            ]
            
        if "azure" in self.tts_engines:
            available_voices["azure"] = [
                {"id": "en-US-AriaNeural", "name": "Aria", "gender": "female"},
                {"id": "en-US-GuyNeural", "name": "Guy", "gender": "male"},
                {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female"},
                {"id": "en-GB-RyanNeural", "name": "Ryan (British)", "gender": "male"},
                {"id": "en-GB-SoniaNeural", "name": "Sonia (British)", "gender": "female"},
                {"id": "en-AU-NatashaNeural", "name": "Natasha (Australian)", "gender": "female"},
                {"id": "en-AU-WilliamNeural", "name": "William (Australian)", "gender": "male"}
            ]
        
        return available_voices
    
    def set_api_key(self, service: str, key: str) -> bool:
        """Set API key for a service"""
        if service not in ["azure", "elevenlabs"]:
            return False
            
        self.config["api_keys"][service] = key
        self._save_config(self.config)
        
        # Reinitialize engines to pick up new API key
        self._initialize_engines()
        
        return True
    
    def test_voice(self, text: str = "Hello, I am the Triad Terminal voice assistant. How can I help you today?") -> None:
        """Test current voice settings"""
        self.speak(text, blocking=True)

class VoiceCommandHandler:
    """Handles voice commands and recognition"""
    
    def __init__(self, voice_engine: EnhancedVoice):
        self.voice = voice_engine
        self.listening = False
        self.recognition_thread = None
        self.stop_recognition = threading.Event()
    
    def start_listening(self, callback: Callable[[str], None]) -> bool:
        """Start listening for voice commands"""
        if self.listening:
            return False
            
        # Check if we have speech recognition
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
        except ImportError:
            logger.error("SpeechRecognition package not installed")
            return False
            
        # Start listening thread
        self.stop_recognition.clear()
        self.recognition_thread = threading.Thread(
            target=self._recognition_loop,
            args=(callback,)
        )
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        
        self.listening = True
        return True
    
    def stop_listening(self) -> bool:
        """Stop listening for voice commands"""
        if not self.listening:
            return False
            
        self.stop_recognition.set()
        
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2.0)
            
        self.listening = False
        return True
    
    def _recognition_loop(self, callback: Callable[[str], None]) -> None:
        """Background thread for continuous speech recognition"""
        import speech_recognition as sr
        
        # Announce we're listening
        self.voice.speak("Voice recognition activated. Speak commands clearly.")
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                while not self.stop_recognition.is_set():
                    try:
                        # Listen for audio
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                        
                        # Use Google's speech recognition
                        text = self.recognizer.recognize_google(audio)
                        
                        if text:
                            # Alert user we heard them
                            logger.info(f"Voice command recognized: {text}")
                            
                            # Call the callback with recognized text
                            callback(text)
                            
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        logger.error(f"Recognition service error: {e}")
                        time.sleep(3)  # Wait before retrying
                    except Exception as e:
                        logger.error(f"Recognition error: {e}")
                        
        except Exception as e:
            logger.error(f"Error in recognition loop: {e}")
        finally:
            self.voice.speak("Voice recognition deactivated.")

def main():
    """Test the enhanced voice capabilities"""
    voice = EnhancedVoice()
    
    print("Enhanced Voice System Test")
    print("=========================")
    
    # List available engines
    print("\nAvailable TTS engines:")
    for name, engine in voice.tts_engines.items():
        print(f"- {name} ({engine['type']}, {engine['quality']} quality)")
    
    # Test default voice
    print("\nTesting default voice...")
    voice.test_voice()
    
    # Test different voices if available
    if "pyttsx3" in voice.tts_engines:
        print("\nTesting male voice...")
        voice.set_voice(gender="male")
        voice.speak("This is the male voice test.", blocking=True)
        
        print("\nTesting female voice...")
        voice.set_voice(gender="female")
        voice.speak("This is the female voice test.", blocking=True)
        
        print("\nTesting different speeds...")
        voice.set_voice(rate=0.8)
        voice.speak("This is a slower voice test.", blocking=True)
        
        voice.set_voice(rate=1.5)
        voice.speak("This is a faster voice test.", blocking=True)
    
    # Reset to default
    voice.set_voice(gender="neutral", rate=1.0, pitch=1.0)
    
    print("\nVoice test complete!")

if __name__ == "__main__":
    main()