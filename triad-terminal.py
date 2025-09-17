            elif choice == '7':
                # Preferred engine
                print("\nAvailable engines:")
                engines = list(self.voice_interface.voice.tts_engines.keys())
                print("0. Auto (use best available)")

                for i, engine in enumerate(engines):
                    engine_data = self.voice_interface.voice.tts_engines[engine]
                    print(f"{i+1}. {engine} ({engine_data.get('type', 'unknown')}, {engine_data.get('quality', 'unknown')} quality)")

                engine_choice = input("\nSelect engine number: ")

                if engine_choice == '0':
                    settings['preferred_engine'] = 'auto'
                    self.voice_interface.update_voice_settings(settings)
                    print("Voice engine set to auto")
                    self.voice_interface.voice.test_voice("This is a test using the auto engine selection.")
                elif engine_choice.isdigit() and 1 <= int(engine_choice) <= len(engines):
                    selected_engine = engines[int(engine_choice) - 1]
                    settings['preferred_engine'] = selected_engine
                    self.voice_interface.update_voice_settings(settings)
                    print(f"Voice engine set to {selected_engine}")
                    self.voice_interface.voice.test_voice("This is a test using the selected voice engine.")
                else:
                    print("Invalid choice")

            elif choice == '8':
                # Configure API keys
                print("\nConfigure API keys:")
                print("1. Azure Speech Services")
                print("2. ElevenLabs")
                print("0. Back")

                api_choice = input("\nEnter choice: ")

                if api_choice == '1':
                    key = input("Enter Azure Speech Services API key (leave empty to skip): ")
                    if key:
                        self.voice_interface.voice.set_api_key('azure', key)
                        print("Azure Speech Services API key updated")
                elif api_choice == '2':
                    key = input("Enter ElevenLabs API key (leave empty to skip): ")
                    if key:
                        self.voice_interface.voice.set_api_key('elevenlabs', key)
                        print("ElevenLabs API key updated")

            elif choice == '9':
                # Test voice
                self.voice_interface.voice.test_voice("This is a test of the Triad Terminal voice system. If you can hear this, your voice settings are working correctly.")

            elif choice == '0':
                break

            else:
                print("Invalid choice")

    def run_help(self) -> None:
        """Display help information"""
        print("\nTriad Terminal Help")
        print("==================")

        print("\nMain components:")
        print("1. Shell Interface - Interactive command line with enhanced features")
        print("2. Database Manager - Manage SQLite databases and execute SQL queries")
        print("3. Repository Manager - Git and GitHub integration")
        print("4. Voice Assistant - Voice control and text-to-speech")
        print("5. AI Tools - Intelligent assistance for development tasks")

        print("\nKey shortcuts:")
        print("Ctrl+C - Interrupt current operation")
        print("Ctrl+D - Exit current interface")

        print("\nGetting started:")
        print("- Use the main menu to access different components")
        print("- Configure your settings from the Settings menu")
        print("- Repository Manager helps you work with Git repositories")
        print("- Use the Voice Assistant for hands-free operation")
        print("- AI Tools provide intelligent assistance for coding tasks")

        print("\nFor more information, visit: https://github.com/yourusername/triad-terminal")

        input("\nPress Enter to continue...")

    def handle_voice_command(self, command: str) -> None:
        """Handle voice command"""
        if not command:
            return

        command_lower = command.lower()

        # Process basic system commands
        if "exit" in command_lower or "quit" in command_lower:
            self.voice_interface.speak("Exiting voice mode")
            return

        elif "hello" in command_lower or "hi" in command_lower:
            self.voice_interface.speak(f"Hello {self.username or ''}! How can I help you today?")
            return

        # Process component commands
        if "open shell" in command_lower or "start shell" in command_lower:
            self.voice_interface.speak("Opening shell interface")
            self.run_shell()

        elif "database" in command_lower:
            self.voice_interface.speak("Opening database manager")
            self.run_database_manager()

        elif "repository" in command_lower or "git" in command_lower:
            self.voice_interface.speak("Opening repository manager")
            self.run_repository_manager()

        # Process AI-based commands
        elif self.initialized["ai"] and self.ai_integration:
            result = self.ai_integration.process_natural_language(command)

            if result["success"]:
                self.voice_interface.speak(f"I'll run: {result['command']}")

                # Execute the command if shell is initialized
                if self.initialized["shell"] and self.shell:
                    self.shell.execute_command(result["command"])
            else:
                self.voice_interface.speak("I'm not sure how to process that command")
        else:
            self.voice_interface.speak("I'm sorry, I don't understand that command")

    def run(self) -> None:
        """Run the Triad Terminal application"""
        try:
            # Make sure config directory exists
            os.makedirs(os.path.join(self.config_dir, "logs"), exist_ok=True)

            # Authenticate user
            if not self.authenticate():
                print("Authentication failed. Exiting...")
                sys.exit(1)

            # Display welcome message
            self.welcome()

            # Start initializing components in background
            threading.Thread(target=self.initialize_all, daemon=True).start()

            # Main loop
            self.running = True
            while self.running:
                self.display_main_menu()

                try:
                    choice = input("\nEnter your choice: ")

                    if choice == '1':
                        self.run_shell()
                    elif choice == '2':
                        self.run_database_manager()
                    elif choice == '3':
                        self.run_repository_manager()
                    elif choice == '4':
                        self.run_voice_assistant()
                    elif choice == '5':
                        self.run_ai_tools()
                    elif choice == '6':
                        self.run_settings()
                    elif choice == '7':
                        self.run_help()
                    elif choice == '0':
                        confirm = input("Are you sure you want to exit? (y/n): ")
                        if confirm.lower().startswith('y'):
                            self.running = False
                    else:
                        print("Invalid choice")

                except KeyboardInterrupt:
                    print("\nOperation interrupted")
                except Exception as e:
                    print(f"Error: {e}")
                    logger.error(f"Error in main loop: {e}")

            # Logout and exit
            print("\nLogging out...")
            self.logout()
            print("Goodbye!")

        except KeyboardInterrupt:
            print("\nOperation interrupted")
            self.logout()
            print("Goodbye!")

        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            print(f"An error occurred: {e}")
            self.logout()
            sys.exit(1)

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Triad Terminal")
    parser.add_argument("--no-auth", action="store_true", help="Skip authentication (for development)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run terminal
    terminal = TriadTerminal()

    # Skip authentication if requested
    if args.no_auth:
        terminal.authenticated = True
        terminal.username = "dev_user"

    terminal.run()

if __name__ == "__main__":
    main()
