# React Chat UI with Ollama

A simple React-based chat interface that communicates with an Ollama language model server.

## Features

- **React Chat Interface** - Built with React 18 using CDN links (no build step required)
- **Ollama Integration** - Connects to the local Ollama API through the web server
- **Configurable Settings** - Change the model dynamically
- **Auto-scrolling** - Chat scrolls to show latest messages
- **Responsive Design** - Works on desktop and mobile devices
- **Error Handling** - Clear error messages if connection fails

## Files

- `index.html` - Main React chat component with embedded JSX
- `styles.css` - Modern gradient UI styling
- `../services/web.sh` - Python HTTP server to serve files

## Setup

### 1. Start the Web Server

```bash
./services/web.sh          # Starts on port 8000
./services/web.sh 3000     # Custom port
```

The server will output:
```
Starting web server on http://0.0.0.0:8000
Serving files from: /workspaces/robot/web
```

### 2. Start Ollama

Make sure Ollama is running on the same machine as the web server:
```bash
ollama serve          # Runs on http://localhost:11434 by default
```

### 3. Access the Chat UI

Open your browser to:
- `http://localhost:8000` (from the host machine)
- `http://127.0.0.1:8000` (from within the container)

## Using the Chat Interface

1. **Send Messages**:
   - Type your message in the input field
   - Press "Send" or hit Enter
   - Wait for the AI response

## Default Configuration

- **Ollama backend**: `http://127.0.0.1:11434` from the web server
- **Default Model**: `mistral`
- **Port**: 8000

## Modifying Models

You can change the model in the UI anytime. Common models:
- `mistral` - Fast and capable
- `llama2` - Meta's Llama 2
- `neural-chat` - Lightweight
- `orca-mini` - Smaller model

## Technical Details

### Why No Build Step?

This React app doesn't require Node.js or npm because:
- React is loaded from CDN (unpkg)
- Babel standalone transpiles JSX in the browser
- All code is in a single HTML file

### Server Implementation

The Python server uses:
- `socketserver.TCPServer` with `allow_reuse_address=True` (prevents "Address already in use" errors)
- `SimpleHTTPRequestHandler` for HTTP serving
- Automatic serving of `index.html` for the root path

## Troubleshooting

### Port Already in Use
```bash
killall python3  # Kill the server process
```

### Ollama Connection Error
- Verify Ollama is running on the server: `curl http://localhost:11434/api/tags`
- Check that the web server can reach its local Ollama service

### Styles Not Loading
- Clear browser cache (Ctrl+Shift+Delete)
- Restart the server
- Check browser console for errors

## Architecture

```
/workspaces/robot/
├── web/
│   ├── index.html      # React app + chat logic
│   └── styles.css      # UI styling
└── services/
    └── web.sh       # Python HTTP server
```
