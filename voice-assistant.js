#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function setupVoiceInterface() {
  console.log('\x1b[36m%s\x1b[0m', '╔══════════════════════════════════════════════╗');
  console.log('\x1b[36m%s\x1b[0m', '║      DevPod Voice Interface Setup            ║');
  console.log('\x1b[36m%s\x1b[0m', '╚══════════════════════════════════════════════╝');

  try {
    // Create a docker-compose file for the voice interface
    const voiceComposeFile = path.join(process.cwd(), 'docker-compose.voice.yml');
    
    const voiceComposeContent = `version: '3'
services:
  voice-interface:
    image: python:3.9-slim
    restart: unless-stopped
    volumes:
      - ./voice-assistant:/app
    working_dir: /app
    ports:
      - "5000:5000"
    command: >
      bash -c "pip install flask speechrecognition pyaudio pyttsx3 requests &&
               python app.py"
`;
    
    fs.writeFileSync(voiceComposeFile, voiceComposeContent);
    
    // Create voice assistant directory and app
    const voiceDir = path.join(process.cwd(), 'voice-assistant');
    if (!fs.existsSync(voiceDir)) {
      fs.mkdirSync(voiceDir, { recursive: true });
    }
    
    // Create a simple Flask app for voice commands
    const flaskApp = `from flask import Flask, request, jsonify
import speech_recognition as sr
import pyttsx3
import json
import os

app = Flask(__name__)

# Initialize speech engine
engine = pyttsx3.init()

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DevPod Voice Assistant</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            h1 { color: #333; }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
            }
            #output {
                margin-top: 20px;
                padding: 15px;
                background: white;
                border-radius: 4px;
                min-height: 100px;
            }
            .command { font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>DevPod Voice Assistant</h1>
        <p>Click the button and speak a command</p>
        
        <button id="recordBtn">Start Recording</button>
        
        <div id="output">
            <p>Command output will appear here...</p>
        </div>
        
        <h2>Available Commands:</h2>
        <ul>
            <li><span class="command">open editor</span> - Opens the code editor</li>
            <li><span class="command">list projects</span> - Lists all projects</li>
            <li><span class="command">create project</span> - Starts the project creation wizard</li>
            <li><span class="command">deploy</span> - Shows deployment options</li>
        </ul>
        
        <script>
            const recordBtn = document.getElementById('recordBtn');
            const output = document.getElementById('output');
            
            recordBtn.addEventListener('click', async () => {
                recordBtn.disabled = true;
                recordBtn.textContent = 'Listening...';
                output.innerHTML = '<p>Listening for command...</p>';
                
                try {
                    const response = await fetch('/listen', { method: 'POST' });
                    const data = await response.json();
                    
                    output.innerHTML = `
                        <p>I heard: "${data.text}"</p>
                        <p>Response: ${data.response}</p>
                    `;
                } catch (error) {
                    output.innerHTML = `<p>Error: ${error.message}</p>`;
                } finally {
                    recordBtn.disabled = false;
                    recordBtn.textContent = 'Start Recording';
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/listen', methods=['POST'])
def listen():
    recognizer = sr.Recognizer()
    
    # This would use the microphone in a real setup
    # In this demo, we'll simulate voice recognition
    
    # Simulated recognized text - in real app this would come from microphone
    text = "open editor"
    
    # Process commands
    response = process_command(text)
    
    return jsonify({
        "text": text,
        "response": response
    })

def process_command(text):
    text = text.lower()
    
    if "open editor" in text:
        return "Opening code editor. You can access it at http://localhost:8080"
    
    elif "list projects" in text:
        # In a real app, this would scan the workspace directory
        return "You have the following projects: project1, project2"
    
    elif "create project" in text:
        return "To create a new project, please use the create-devenv.js script"
    
    elif "deploy" in text:
        return "To deploy your project, use the deploy.js script"
    
    else:
        return "I didn't understand that command. Please try again."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
`;
    
    fs.writeFileSync(path.join(voiceDir, 'app.py'), flaskApp);
    
    // Create README for voice interface
    const voiceReadme = `# DevPod Voice Assistant

This is a simple voice interface for controlling your DevPod environment.

## Features
- Voice command recognition
- Basic project management commands
- System navigation

## Usage
1. Start the voice interface:
   \`\`\`
   docker-compose -f docker-compose.voice.yml up -d
   \`\`\`
2. Open http://localhost:5000 in your browser
3. Click "Start Recording" and speak a command

## Available Commands
- "open editor" - Opens the code editor
- "list projects" - Lists all projects
- "create project" - Starts the project creation wizard
- "deploy" - Shows deployment options

## Note
This is a simple demo implementation. In a production environment, you would:
- Use WebSockets for real-time communication
- Implement proper microphone access
- Add more sophisticated command parsing
- Connect to DevPod's APIs for real functionality
`;
    
    fs.writeFileSync(path.join(voiceDir, 'README.md'), voiceReadme);
    
    console.log('Voice interface setup complete!');
    console.log('\nTo start the voice interface:');
    console.log('1. Run: docker-compose -f docker-compose.voice.yml up -d');
    console.log('2. Open http://localhost:5000 in your browser');
    console.log('\nNote: This is a basic implementation. A production-ready');
    console.log('voice interface would require additional components and permissions.');
    
  } catch (error) {
    console.error('Error setting up voice interface:', error);
  }
}

setupVoiceInterface();