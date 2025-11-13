from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# In-memory storage
rooms = {}  # room_id -> {player1_id: int, player2_id: int or None, status: 'waiting'|'full'}
next_room_id = 1

USER_SERVICE_URL = "http://localhost:3001"

@app.route('/rooms', methods=['POST'])
def create_room():
    global next_room_id
    room_id = next_room_id
    rooms[room_id] = {
        "player1_id": None,
        "player2_id": None,
        "status": "waiting"
    }
    next_room_id += 1
    return jsonify({"roomId": room_id}), 201

@app.route('/rooms/<int:room_id>/join', methods=['POST'])
def join_room(room_id):
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404

    data = request.get_json()
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "userId required"}), 400

    # Validate user exists via User Service
    user_resp = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
    if user_resp.status_code != 200:
        return jsonify({"error": "Invalid userId"}), 400

    room = rooms[room_id]

    if room["status"] == "full":
        return jsonify({"error": "Room is full"}), 400

    if room["player1_id"] is None:
        room["player1_id"] = user_id
    elif room["player2_id"] is None:
        room["player2_id"] = user_id
        room["status"] = "full"
    else:
        return jsonify({"error": "Room full"}), 400

    return jsonify({
        "roomId": room_id,
        "status": room["status"],
        "yourPosition": "player1" if room["player1_id"] == user_id else "player2"
    })

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404
    return jsonify(rooms[room_id])

if __name__ == '__main__':
    print("Room Service running on http://localhost:3002")
    app.run(port=3002, debug=True)