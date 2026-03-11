# React Chat UI with Ollama

A simple React-based chat interface that communicates with an Ollama language model server.

## Features

- **React Chat Interface** - Built with React 18 using CDN links (no build step required)
- **Ollama Integration** - Connects to Ollama API for LLM responses
- **Configurable Settings** - Change Ollama URL and model dynamically
- **Auto-scrolling** - Chat scrolls to show latest messages
- **Responsive Design** - Works on desktop and mobile devices
- **Error Handling** - Clear error messages if connection fails

## Files

- `index.html` - Main React chat component with embedded JSX
- `styles.css` - Modern gradient UI styling
- `../bin/server.sh` - Python HTTP server to serve files

## Setup

### 1. Start the Web Server

```bash
./bin/server.sh          # Starts on port 8000
./bin/server.sh 3000     # Custom port
```

The server will output:
```
Starting web server on http://0.0.0.0:8000
Serving files from: /workspaces/robot/web
```

### 2. Start Ollama

Make sure Ollama is running on the default URL or update it in the UI:
```bash
ollama serve          # Runs on http://localhost:11434 by default
```

### 3. Access the Chat UI

Open your browser to:
- `http://localhost:8000` (from the host machine)
- `http://127.0.0.1:8000` (from within the container)

## Using the Chat Interface

1. **Configure Settings** (top of page):
   - **Ollama URL**: The address where Ollama is running (default: `http://localhost:11434`)
   - **Model**: The model to use (default: `mistral`)

2. **Send Messages**:
   - Type your message in the input field
   - Press "Send" or hit Enter
   - Wait for the AI response

## Default Configuration

- **Ollama URL**: `http://localhost:11434`
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
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check firewall settings
- Try updating the Ollama URL in the UI

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
└── bin/
    └── server.sh       # Python HTTP server
```
