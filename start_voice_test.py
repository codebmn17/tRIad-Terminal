# Double-click this file to hear the voice say 'Triad online'
from voice_interface_Version2 import VoiceManager

if __name__ == "__main__":
    vm = VoiceManager()
    vm.speak("Triad online", blocking=True)
    print("If you heard 'Triad online', your TTS is working.")
