# Triad Terminal UI Theme

This document provides comprehensive instructions for integrating the Triad Terminal dark cyberpunk theme into web, Electron, and PyWebView applications.

## Overview

The Triad Terminal theme provides:
- Dark cyberpunk background with optional wallpaper overlay
- Neon green color scheme matching terminal themes
- Header with left mask icon, center title, and right triangle emblem
- Responsive design and accessibility features
- Graceful fallbacks for missing assets

## Quick Start

### 1. Basic HTML Integration

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Triad Terminal App</title>
  
  <!-- Include the theme CSS -->
  <link rel="stylesheet" href="/web/ui/theme/theme-triad.css">
</head>
<body class="triad-theme" data-triad-auto-header="true">
  
  <!-- Your content -->
  <main class="triad-panel">
    <h1>Welcome to Triad Terminal</h1>
    <p>Your cyberpunk interface is ready.</p>
  </main>
  
  <!-- Include the theme JavaScript -->
  <script src="/web/ui/theme/init-triad-theme.js"></script>
</body>
</html>
```

### 2. Manual Header Integration

If you prefer to manually include the header:

```html
<body class="triad-theme">
  <!-- Copy this header from /web/ui/components/header.html -->
  <header class="triad-header">
    <div class="header-left">
      <img src="/assets/images/anon-mask.svg" alt="Anonymous Mask" class="mask-icon">
    </div>
    <div class="header-center">
      <h1 class="title">TRIAD TERMINAL</h1>
    </div>
    <div class="header-right">
      <img src="/assets/images/triad-triangle.svg" alt="Triad Triangle" class="triangle-icon">
    </div>
  </header>
  
  <!-- Your content -->
  <main>
    <!-- ... -->
  </main>
</body>
```

## Asset Setup

### Required Images

Place these images in `/assets/images/`:

1. **triad-terminal-bg.png** - Background wallpaper (1920x1080+ recommended)
2. **triad-triangle.svg** - Neon triangle emblem (32x32 to 64x64 px)
3. **anon-mask.svg** (optional) - Anonymous mask icon

### Fallback Behavior

- Missing background: Falls back to dark gradient
- Missing triangle: Uses provided placeholder triangle with reduced opacity
- Missing mask: Left header section remains empty

## Framework Integration

### Electron Application

```javascript
// main.js
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    // Dark theme for native window chrome
    backgroundColor: '#0a0a0a',
    titleBarStyle: 'hidden' // Optional: hide default title bar
  });

  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();
});
```

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Triad Terminal</title>
  <link rel="stylesheet" href="web/ui/theme/theme-triad.css">
  <style>
    /* Electron-specific adjustments */
    body.triad-theme {
      -webkit-app-region: no-drag;
    }
    
    .triad-header {
      -webkit-app-region: drag; /* Make header draggable */
    }
    
    .triad-header .mask-icon,
    .triad-header .triangle-icon {
      -webkit-app-region: no-drag; /* Keep icons clickable */
    }
  </style>
</head>
<body class="triad-theme" data-triad-auto-header="true">
  <main class="triad-panel">
    <h2>Electron Triad Terminal</h2>
    <p>Running in desktop mode</p>
  </main>
  
  <script src="web/ui/theme/init-triad-theme.js"></script>
</body>
</html>
```

### PyWebView Application

```python
# app.py
import webview
import os

def create_window():
    # Serve static files from current directory
    webview.create_window(
        'Triad Terminal',
        'index.html',
        width=1200,
        height=800,
        background_color='#0a0a0a',
        text_select=False
    )
    webview.start(debug=True)

if __name__ == '__main__':
    create_window()
```

### Flask/Django Integration

#### Flask Example

```python
# app.py
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Serve static theme files
@app.route('/web/<path:filename>')
def web_static(filename):
    return send_from_directory('web', filename)

@app.route('/assets/<path:filename>')
def assets_static(filename):
    return send_from_directory('assets', filename)

if __name__ == '__main__':
    app.run(debug=True)
```

```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Triad Terminal - Flask</title>
  <link rel="stylesheet" href="/web/ui/theme/theme-triad.css">
</head>
<body class="triad-theme" data-triad-auto-header="true">
  
  <div class="triad-panel">
    <h2>Flask Triad Terminal</h2>
    <p>Web-based terminal interface</p>
  </div>
  
  <script src="/web/ui/theme/init-triad-theme.js"></script>
</body>
</html>
```

## Customization

### Color Scheme

Override CSS variables to customize colors:

```css
:root {
  --triad-bg-primary: #001122;      /* Custom dark blue */
  --triad-fg-primary: #ff6600;      /* Custom orange */
  --triad-accent: #ffcc00;          /* Custom yellow */
}
```

### Custom Title

```javascript
// Change title after page load
document.querySelector('.triad-header .title').textContent = 'MY CUSTOM TERMINAL';
```

### Additional Icons

```html
<!-- Add status indicators to header-right -->
<div class="header-right">
  <span class="status-indicator online">●</span>
  <img src="/assets/images/triad-triangle.svg" alt="Triad Triangle" class="triangle-icon">
</div>
```

## Advanced Usage

### Multiple Themes

```javascript
// Switch between themes
function switchTheme(themeName) {
  document.body.className = `${themeName}-theme`;
}

// Available: triad-theme, matrix-theme, cyberpunk-theme
switchTheme('triad'); // Apply triad theme
```

### Event Handling

```javascript
// Listen for theme initialization
document.addEventListener('DOMContentLoaded', function() {
  if (window.TriadTheme) {
    console.log('Triad theme loaded');
    
    // Manually enhance specific headers
    const customHeader = document.querySelector('#my-header');
    if (customHeader) {
      window.TriadTheme.enhanceHeader(customHeader);
    }
  }
});
```

### Content Panels

Use the provided panel classes for consistent styling:

```html
<div class="triad-panel">
  <h3>Terminal Output</h3>
  <pre>$ ls -la
drwxr-xr-x  5 user user 4096 Dec  1 10:30 .</pre>
</div>

<div class="triad-panel glow">
  <h3>System Status</h3>
  <p>All systems operational</p>
</div>
```

## Accessibility

The theme includes several accessibility features:

- High contrast mode support
- Reduced motion support for users with vestibular disorders
- Proper ARIA labels (add your own for dynamic content)
- Keyboard navigation support

### Adding ARIA Labels

```html
<header class="triad-header" role="banner">
  <div class="header-left">
    <img src="/assets/images/anon-mask.svg" 
         alt="Anonymous Mask" 
         class="mask-icon"
         role="img"
         aria-label="Application logo">
  </div>
  <!-- ... -->
</header>
```

## Troubleshooting

### Common Issues

1. **Images not loading**: Check file paths and ensure web server can serve static files
2. **Theme not applying**: Verify CSS file is loaded and body has `triad-theme` class
3. **JavaScript errors**: Check browser console and ensure JS file is loaded

### Browser Compatibility

- Chrome/Chromium 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Performance Tips

- Optimize background image size (compress PNG, consider WebP)
- Use vector SVG icons when possible
- Enable gzip compression on your web server
- Consider lazy loading for large background images

## License

This theme is part of the Triad Terminal project. Use according to your project's license terms.