import requests
import socketio
import threading
import time

# === CONFIG ===
USER_URL = "http://localhost:3001"
ROOM_URL = "http://localhost:3002"
GAME_URL = "http://localhost:3003"
WS_URL = "http://localhost:3003"

sio = socketio.Client()
user_id = None
username = None
room_id = None

# Game boards (5x5)
my_board = [['~' for _ in range(5)] for _ in range(5)]
opponent_board = [['~' for _ in range(5)] for _ in range(5)]

# === WEBSOCKET EVENT HANDLERS ===
@sio.event
def connect():
    print("Connected to Game Server via WebSocket")

@sio.event
def disconnect():
    print("Disconnected from Game Server")

@sio.on('joined')
def on_joined(data):
    print(f"Joined game room {data['roomId']} as user {data['yourId']}")

@sio.on('ships-placed')
def on_ships_placed(data):
    print(f"Player {data['userId']} has placed their ships.")

@sio.on('game-ready')
def on_game_ready(data):
    global my_board, opponent_board
    print("\n" + "="*50)
    print("BOTH PLAYERS READY! GAME STARTING...")
    print(f"Current turn: Player {data['turn']}")
    my_board = [['~' for _ in range(5)] for _ in range(5)]
    opponent_board = [['~' for _ in range(5)] for _ in range(5)]
    display_boards()
    if data['turn'] == user_id:
        take_turn()

@sio.on('move-update')
def on_move_update(data):
    x, y = data['x'], data['y']
    marker = 'X' if data['hit'] else 'O'
    opponent_board[x][y] = marker
    result = "HIT!" if data['hit'] else "MISS"
    print(f"\nOpponent fired at ({x},{y}) → {result}")
    display_boards()
    if data['turn'] == user_id:
        take_turn()

@sio.on('game-over')
def on_game_over(data):
    print(f"\n{'='*50}")
    print(f"GAME OVER! Winner: Player {data['winner']}")
    if data['winner'] == user_id:
        print("YOU WIN!")
    else:
        print("You lost.")
    print("="*50)
    sio.disconnect()

@sio.on('error')
def on_error(data):
    print(f"Error: {data.get('message', 'Unknown error')}")

# === HELPER FUNCTIONS ===
def display_boards():
    print("\n" + "YOUR BOARD".center(25) + "OPPONENT BOARD".center(25))
    print("-" * 50)
    header = "  " + " ".join(str(i) for i in range(5))
    print(header + "    " + header)
    for i in range(5):
        my_row = " ".join(my_board[i])
        opp_row = " ".join(opponent_board[i])
        print(f"{i} {my_row}  | {i} {opp_row}")
    print("-" * 50)

def take_turn():
    while True:
        try:
            coord = input("\nYour turn! Fire position (x y): ").strip()
            if not coord:
                continue
            x, y = map(int, coord.split())
            if 0 <= x < 5 and 0 <= y < 5 and opponent_board[x][y] == '~':
                sio.emit('fire', {
                    'roomId': room_id,
                    'userId': user_id,
                    'x': x,
                    'y': y
                })
                opponent_board[x][y] = '?'  # Mark as pending
                display_boards()
                break
            else:
                print("Invalid position or already fired there!")
        except ValueError:
            print("Enter two numbers: x y (0-4)")
        except Exception as e:
            print(f"Input error: {e}")

# === MAIN GAME FLOW ===
def main():
    global user_id, username, room_id

    print("BATTLESHIP CLI CLIENT")
    print("1. Register")
    print("2. Login")
    choice = input("Choose (1 or 2): ").strip()

    if choice == "1":
        username = input("Enter username: ").strip()
        resp = requests.post(f"{USER_URL}/register", json={"username": username})
    else:
        username = input("Enter username: ").strip()
        resp = requests.post(f"{USER_URL}/login", json={"username": username})

    if resp.status_code != 200:
        print("Authentication failed:", resp.json().get("error", "Unknown"))
        return

    user_data = resp.json()
    user_id = user_data["userId"]
    print(f"Logged in as {username} (ID: {user_id})")

    # Connect to WebSocket
    try:
        sio.connect(WS_URL)
        print("Connecting to game server...")
        time.sleep(1)
    except Exception as e:
        print(f"WebSocket connection failed: {e}")
        return

    print("\n1. Create Room")
    print("2. Join Room")
    choice = input("Choose (1 or 2): ").strip()

    if choice == "1":
        resp = requests.post(f"{ROOM_URL}/rooms")
        if resp.status_code != 201:
            print("Failed to create room:", resp.json())
            return
        room_id = resp.json()["roomId"]
        print(f"Room created: {room_id}")
    else:
        try:
            room_id = int(input("Enter Room ID: ").strip())
        except:
            print("Invalid room ID")
            return
        resp = requests.post(f"{ROOM_URL}/rooms/{room_id}/join", json={"userId": user_id})
        if resp.status_code != 200:
            print("Failed to join room:", resp.json().get("error", "Unknown"))
            return
        print(f"Joined room {room_id}")

    # Join game via WebSocket
    sio.emit('join-game', {'roomId': room_id, 'userId': user_id})

    # Start game (only after both joined)
    print("Waiting for opponent...")
    start_resp = requests.post(f"{GAME_URL}/games/{room_id}/start")
    if start_resp.status_code != 200:
        print("Could not start game:", start_resp.json())
        return

    # === SHIP PLACEMENT ===
    print("\nPlace your 2 ships (each 2 cells, horizontal or vertical)")
    ships = []
    for ship_num in range(1, 3):
        while True:
            pos_input = input(f"Ship {ship_num} (x1 y1 x2 y2): ").strip()
            try:
                x1, y1, x2, y2 = map(int, pos_input.split())
                # Must be adjacent and in bounds
                if (abs(x1 - x2) + abs(y1 - y2) == 1 and
                    0 <= x1 < 5 and 0 <= x2 < 5 and
                    0 <= y1 < 5 and 0 <= y2 < 5):
                    ships.append([[x1, y1], [x2, y2]])
                    # Mark on local board
                    my_board[x1][y1] = 'S'
                    my_board[x2][y2] = 'S'
                    display_boards()
                    break
                else:
                    print("Ships must be adjacent (horizontal/vertical) and within 0–4!")
            except:
                print("Enter 4 numbers: x1 y1 x2 y2")

    # Send ship positions to server
    all_positions = [pos for ship in ships for pos in ship]
    sio.emit('place-ships', {
        'roomId': room_id,
        'userId': user_id,
        'positions': all_positions
    })

    print("Waiting for opponent to place ships...")
    sio.wait()

if __name__ == "__main__":
    main()