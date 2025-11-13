from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory games
games = {}  # room_id -> game state
ROOM_SERVICE_URL = "http://localhost:3002"

# 5x5 empty board
EMPTY = 0
SHIP = 1
HIT = 2
MISS = 3

def create_board():
    return [[EMPTY for _ in range(5)] for _ in range(5)]

def place_ship(board, positions):
    for x, y in positions:
        board[x][y] = SHIP

def is_valid_placement(board, positions):
    for x, y in positions:
        if not (0 <= x < 5 and 0 <= y < 5) or board[x][y] != EMPTY:
            return False
    return True

def fire(board, x, y):
    if board[x][y] == SHIP:
        board[x][y] = HIT
        return True
    elif board[x][y] == EMPTY:
        board[x][y] = MISS
        return False
    return None  # Already fired

def all_ships_sunk(board):
    return all(cell != SHIP for row in board for cell in row)

@app.route('/games/<int:room_id>/start', methods=['POST'])
def start_game(room_id):
    # Validate room exists and is full
    resp = requests.get(f"{ROOM_SERVICE_URL}/rooms/{room_id}")
    if resp.status_code != 200:
        return jsonify({"error": "Room not found"}), 404
    room = resp.json()
    if room.get("status") != "full":
        return jsonify({"error": "Room not full"}), 400

    p1 = room["player1_id"]
    p2 = room["player2_id"]

    games[room_id] = {
        "board1": create_board(),  # Player 1
        "board2": create_board(),  # Player 2
        "ships1": None,
        "ships2": None,
        "current_turn": p1,
        "winner": None
    }
    return jsonify({"message": "Game started", "roomId": room_id})

@socketio.on('join-game')
def on_join(data):
    room_id = data['roomId']
    user_id = data['userId']
    if room_id not in games:
        emit('error', {'message': 'Game not started'})
        return
    join_room(str(room_id))
    emit('joined', {'roomId': room_id, 'yourId': user_id})

@socketio.on('place-ships')
def on_place_ships(data):
    room_id = data['roomId']
    user_id = data['userId']
    positions = data['positions']  # [[x,y], [x,y]]

    if room_id not in games:
        emit('error', {'message': 'Game not found'})
        return

    game = games[room_id]
    board = game['board1'] if user_id == game['current_turn'] else game['board2']

    if not is_valid_placement(board, positions):
        emit('error', {'message': 'Invalid ship placement'})
        return

    place_ship(board, positions)
    if user_id == list(game.keys())[2]:  # p1
        game['ships1'] = positions
    else:
        game['ships2'] = positions

    emit('ships-placed', {'userId': user_id}, room=str(room_id))

    # Check if both placed
    if game['ships1'] and game['ships2']:
        emit('game-ready', {'turn': game['current_turn']}, room=str(room_id))

@socketio.on('fire')
def on_fire(data):
    room_id = data['roomId']
    user_id = data['userId']
    x, y = data['x'], data['y']

    if room_id not in games:
        return
    game = games[room_id]
    if user_id != game['current_turn']:
        emit('error', {'message': 'Not your turn'})
        return

    opponent_board = game['board2'] if user_id == list(game.keys())[2] else game['board1']
    result = fire(opponent_board, x, y)
    if result is None:
        emit('error', {'message': 'Already fired here'})
        return

    hit = result
    # Switch turn
    game['current_turn'] = game['board2'] if user_id == list(game.keys())[2] else list(game.keys())[2]

    # Check win
    if all_ships_sunk(opponent_board):
        game['winner'] = user_id
        emit('game-over', {'winner': user_id}, room=str(room_id))
    else:
        emit('move-update', {
            'hit': hit,
            'x': x, 'y': y,
            'turn': game['current_turn']
        }, room=str(room_id))

if __name__ == '__main__':
    print("Game Rules Service running on http://localhost:3003 (WebSocket)")
    socketio.run(app, port=3003, debug=True)