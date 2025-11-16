# Distributed Two-Player Battleship Game System

A **real-time, turn-based Battleship game** using **microservices**, **HTTP**, and **WebSocket** — **no database**, **in-memory state**, **3 clients**, **full architecture**.

---

## Project Overview

The task is to implement a **simple, two-person, turn-based game** with a **distributed architecture**.  
The main focus is on **understanding and integrating microservices and WebSocket technology**, rather than creating a commercial product.

---

## 1. Technical Requirements and Architecture

### Backend (Microservices)
- **3 independent microservices** communicating via **HTTP**
- **No database** — data stored in **memory** (focus on architecture, not data management)

| Service | Port | Responsibility |
|--------|------|----------------|
| **User Service** | `3001` | User identification (username-based login/registration) |
| **Room Service** | `3002` | Create game rooms, connect players, manage status |
| **Game Rules Service** | `3003` | Game logic: move control, hit/miss, turn switching, win detection |

> **Inter-service communication**: HTTP (`requests.get()` / `post()`)  
> **Real-time client updates**: **WebSocket only in Game Rules Service**

---

### Clients and Communication
- **3 different platforms** communicate via **WebSocket** with **Game Rules Service**
- Real-time messages: move made, opponent joined, turn change, game over

| Client | Type | Technology |
|-------|------|------------|
| **CLI Client** | Command Line | Python + `python-socketio` |
| **Web Client** | Browser App | HTML, CSS, JavaScript + Socket.IO CDN |
| **Mobile Client** | Touch App | **Kivy** (Python GUI framework) |

> All clients connect to **Game Rules Service (3003)** via **WebSocket**

---

## 2. Architecture Diagram (Mermaid)

```mermaid
graph TD
    subgraph Clients
        CLI[CLI Client<br>Python]
        WEB[Web Client<br>HTML/JS]
        MOB[Mobile Client<br>Kivy]
    end

    subgraph Microservices
        U[User Service<br>3001<br>HTTP]
        R[Room Service<br>3002<br>HTTP]
        G[Game Rules Service<br>3003<br>HTTP + WebSocket]
    end

    CLI -->|WebSocket| G
    WEB -->|WebSocket| G
    MOB -->|WebSocket| G

    G -->|HTTP GET /users/:id| U
    G -->|HTTP GET /rooms/:id| R
    R -->|HTTP GET /users/:id| U

   3. API Documentation
Service-to-Service APIs (HTTP)
User Service (http://localhost:3001)
httpPOST /register
Content-Type: application/json

{ "username": "player1" }
→ 200 OK
{ "userId": 1, "username": "player1" }
httpPOST /login
{ "username": "player1" }
→ 200 OK
{ "userId": 1, "username": "player1" }
Room Service (http://localhost:3002)
httpPOST /rooms
→ 201 Created
{ "roomId": 1 }
httpPOST /rooms/1/join
{ "userId": 1 }
→ 200 OK
{ "roomId": 1, "status": "waiting", "yourPosition": "player1" }
Game Rules Service (http://localhost:3003)
httpPOST /games/1/start
→ 200 OK
{ "message": "Game started", "roomId": 1 }

Client-Server WebSocket Messages (JSON)

EventDirectionPayloadjoin-gameClient → Server{ "roomId": 1, "userId": 1 }joinedServer → Client{ "roomId": 1, "yourId": 1 }place-shipsClient → Server{ "roomId": 1, "userId": 1, "positions": [[0,0],[0,1],[2,2],[3,2]] }ships-placedServer → Client{ "userId": 1 }game-readyServer → Client{ "turn": 1 }fireClient → Server{ "roomId": 1, "userId": 1, "x": 2, "y": 3 }move-updateServer → Client{ "x": 2, "y": 3, "hit": true, "turn": 2 }game-overServer → Client{ "winner": 1 }

4. Technologies Used

Component,Technology
Backend,"Python, Flask, Flask-SocketIO"
CLI Client,"Python, python-socketio"
Web Client,"HTML, CSS, JavaScript, Socket.IO (CDN)"
Mobile Client,Kivy (Python GUI framework)
Communication,"HTTP (services), WebSocket (clients)"
State,In-memory (no DB)

5. How to Run
Step 1: Start Microservices (3 terminals)
bashpython services/user-service/server.py
python services/room-service/server.py
python services/game-rules-service/server.py

Step 2: Run Clients
CLI Client
bashcd clients/cli-client
python main.py
Web Client

Open clients/web-client/index.html in Chrome/Firefox
Register → Create Room → Place 4 ships → Start Game

Mobile Client (Kivy)
bashcd clients/mobile-client
pip install -r requirements.txt    # Or: pip install kivy==2.3.0 python-socketio requests
python main.py

6. Project Structure
textdistributed-two-player-battleship/
├── services/
│   ├── user-service/
│   ├── room-service/
│   └── game-rules-service/
├── clients/
│   ├── cli-client/
│   ├── web-client/
│   └── mobile-client/
├── README.md
└── .gitignore