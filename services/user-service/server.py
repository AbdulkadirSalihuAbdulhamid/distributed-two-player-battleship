from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage
users = {}  # username -> {id, status}
next_id = 1

@app.route('/register', methods=['POST'])
def register():
    global next_id
    data = request.get_json()
    username = data.get('username')
    if not username or username in users:
        return jsonify({"error": "Invalid or existing username"}), 400
    users[username] = {"id": next_id, "status": "online"}
    user_id = next_id
    next_id += 1
    return jsonify({"userId": user_id, "username": username})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    return jsonify(users[username])

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    for user in users.values():
        if user['id'] == user_id:
            return jsonify(user)
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    print("User Service running on http://localhost:3001")
    app.run(port=3001, debug=True)