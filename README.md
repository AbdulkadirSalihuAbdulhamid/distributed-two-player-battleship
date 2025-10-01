# Distributed Two-Person Battleship Game System

A simple, turn-based two-player Battleship game implemented with a distributed microservices architecture. Players take turns placing ships and firing shots on a 5x5 grid. Focus: Microservices (HTTP inter-comms) + WebSockets (real-time updates like "shot fired" or "ship hit"). Data stored in-memory (no DB). Single GitHub monorepo for all components.

## Technology Summary (My Choices)
- **User Service**: Python 3 + Flask (Port 3001) - Handles simple username-based login/registration with in-memory dict storage.
- **Room Service**: Python 3 + Flask + Requests library (Port 3002) - Manages room creation, player joining, and status checks; calls User Service via HTTP.
- **Game Rules Service**: Python 3 + Flask + Flask-SocketIO (Port 3003) - Enforces Battleship logic (ship placement, move validation, win conditions like all ships sunk); broadcasts real-time updates via WebSocket.
- **CLI Client**: Python 3 (using requests for HTTP calls and python-socketio for WebSocket) - Text-based command-line app for login, room ops, and grid input.
- **Web Client**: HTML/CSS/JavaScript (vanilla JS, no framework) + Socket.IO client library - Browser app with a clickable 5x5 grid for moves.
- **Mobile Client**: Kivy (Python-based UI framework) - Simple hybrid mobile app for Android (touch-based grid; easy to build APK).

**Rationale for Choices**: Python/Flask for readability and minimal boilerplate—quick to prototype services without complex setup (vs. Node.js async callbacks). Flask-SocketIO adds WebSockets with ~5 lines of code. Kivy for mobile keeps everything in Python (unified lang). This stack is specific/lightweight to avoid common similarities (e.g., no Java/Spring).

## Project Structure
- `services/`: Backend microservices (user-service, room-service, game-rules-service) – Each has `server.py` + deps.
- `clients/`: 3 clients (cli-client with `main.py`; web-client with `index.html`/`script.js`; mobile-client with Kivy `main.py`).

## Service-to-Service APIs (HTTP/REST – My Custom Endpoints)
Services communicate via simple POST/GET (JSON payloads). Example flows:
- **Room Service → User Service**: GET `/users/{userId}` – Fetches player info for validation (e.g., status='available'). Response: `{"userId": 1, "username": "player1", "status": "available"}` or 404 error.
- **Game Rules Service → Room Service**: GET `/rooms/{roomId}` – Checks if room is full/ongoing. Response: `{"roomId": 1, "player1Id": 1, "player2Id": 2, "status": "full"}` or 404 error.
- Other: POST `/rooms` (create room) → `{"roomId": 1}`; POST `/rooms/{roomId}/join` { "userId": 1 } → `{"status": "full"}`.

Full schemas: All requests use `Content-Type: application/json`. Errors: `{"error": "Message"}` with 4xx status.

## Client-Server APIs (WebSocket via Flask-SocketIO – JSON Format)
All messages are JSON objects. Clients connect to `ws://localhost:3003` (Game Service). HTTP for setup (login/join via fetch/requests); WS for real-time (e.g., shot results).

**Client → Server Messages** (Emitted events):
- `{"type": "join-room", "roomId": 1, "userId": 1}` – Joins room for broadcasts.
- `{"type": "place-ship", "roomId": 1, "positions": [[1,1],[1,2]]}` – Places a ship (array of [row,col]).
- `{"type": "fire-shot", "roomId": 1, "position": [2,3]}` – Fires at grid spot.

**Server → Client Messages** (Emitted to room):
- `{"type": "status", "message": "Opponent joined – Place your ships!", "roomId": 1}` – Room updates.
- `{"type": "move-update", "roomId": 1, "board": [["~","S","~"],["M","~","~"],["~","~","X"]], "turn": "Player2", "winner": null}` – Real-time grid sync (~=empty, S=ship, M=miss, X=hit). "winner": "Player1" or "Draw".
- `{"type": "error", "message": "Invalid shot – Try again"}` – Validation feedback.

## Setup & Run (Basic – Full Code Coming)
1. Install Python 3 + deps: `pip install flask flask-socketio requests python-socketio` (root or per folder).
2. Start services: Open 3 terminals, `cd services/user-service && python server.py` (similar for others; logs show "Running on port 3001").
3. Run CLI: `cd clients/cli-client && python main.py` – Prompts for username/room/move.
4. Web: Open `clients/web-client/index.html` in browser (connects via JS).
5. Mobile: `cd clients/mobile-client && kivy main.py` (or build APK).

## Architecture Overview
[Placeholder: Add diagram.png later – Draw in Draw.io: User/Room/Game boxes (HTTP arrows between); CLI/Web/Mobile → WS arrows to Game Service.]

Repo submitted by Abdulkadir Salihu Abdulhamid. Full demo video + presentation to follow.
