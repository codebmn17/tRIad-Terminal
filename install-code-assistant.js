#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

async function installCodeAssistants() {
  console.log('\x1b[36m%s\x1b[0m', '╔══════════════════════════════════════════════╗');
  console.log('\x1b[36m%s\x1b[0m', '║      DevPod Code Assistant Setup             ║');
  console.log('\x1b[36m%s\x1b[0m', '╚══════════════════════════════════════════════╝');

  try {
    // Get config directory
    const configDir = path.join(process.cwd(), 'config');
    const extensionsDir = path.join(configDir, 'code-server', 'extensions');

    if (!fs.existsSync(extensionsDir)) {
      fs.mkdirSync(extensionsDir, { recursive: true });
    }

    console.log('Installing code assistance extensions...');

    // Create a custom settings file to enable extensions
    const settingsPath = path.join(configDir, 'code-server', 'User', 'settings.json');
    const settingsDir = path.dirname(settingsPath);

    if (!fs.existsSync(settingsDir)) {
      fs.mkdirSync(settingsDir, { recursive: true });
    }

    // Basic settings for code completion and assistance
    const settings = {
      "editor.snippetSuggestions": "top",
      "editor.suggestSelection": "first",
      "editor.tabCompletion": "on",
      "editor.quickSuggestions": {
        "other": true,
        "comments": true,
        "strings": true
      },
      "editor.acceptSuggestionOnEnter": "on",
      "editor.suggest.showMethods": true,
      "editor.suggest.showFunctions": true,
      "editor.suggest.showVariables": true,
      "editor.suggest.showClasses": true,
      "editor.suggest.showKeywords": true,
      "editor.wordBasedSuggestions": true
    };

    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));

    console.log('Code assistant settings configured');
    console.log('\nTo enhance your coding experience:');
    console.log('1. Open VS Code in the browser (http://localhost:8080)');
    console.log('2. Install these extensions from the marketplace:');
    console.log('   - TabNine (AI code completion)');
    console.log('   - GitHub Copilot (if you have a subscription)');
    console.log('   - Kite (another AI assistant option)');
    console.log('   - IntelliCode');

    // Create a helper script to install models
    const modelScript = `#!/bin/bash
echo "Setting up local machine learning models for code completion..."
mkdir -p ./models
cd ./models

echo "This script would normally download and configure local language models."
echo "Due to size constraints, you'd typically set up:"
echo "1. A smaller code-optimized model (e.g., CodeLLaMa or similar)"
echo "2. Syntax-aware completion engines"
echo "3. Local embedding models for code search"

echo "These components require significant disk space (5-20GB)."
echo "For production use, consider connecting to external API services."
`;

    const modelScriptPath = path.join(process.cwd(), 'scripts', 'setup-models.sh');
    const scriptsDir = path.dirname(modelScriptPath);

    if (!fs.existsSync(scriptsDir)) {
      fs.mkdirSync(scriptsDir, { recursive: true });
    }

    fs.writeFileSync(modelScriptPath, modelScript);
    fs.chmodSync(modelScriptPath, '755');

    console.log('\nAdditionally, a script has been created at scripts/setup-models.sh');
    console.log('This is a placeholder for setting up local ML models if desired.');

  } catch (error) {
    console.error('Error setting up code assistants:', error);
  }
}

installCodeAssistants();
