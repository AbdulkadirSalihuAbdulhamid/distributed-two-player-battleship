from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
import requests
import socketio
import threading

# === CONFIG ===
USER_URL = "http://localhost:3001"
ROOM_URL = "http://localhost:3002"
GAME_URL = "http://localhost:3003"
WS_URL = "http://localhost:3003"

sio = socketio.Client()
user_id = None
username = None
room_id = None
my_board = [['~'] * 5 for _ in range(5)]
opponent_board = [['~'] * 5 for _ in range(5)]
placing = False
ship_cells = []

class Board(GridLayout):
    def __init__(self, is_player=True, **kwargs):
        super().__init__(**kwargs)
        self.cols = 5
        self.is_player = is_player
        self.cells = {}
        for i in range(5):
            for j in range(5):
                btn = Button(text='~', font_size=20, background_normal='', background_color=(0.1, 0.3, 0.5, 1))
                btn.bind(on_press=lambda b, x=i, y=j: self.on_cell_press(b, x, y))
                self.add_widget(btn)
                self.cells[(i, j)] = btn

    def on_cell_press(self, btn, x, y):
        if not self.is_player:
            if btn.text == '~' and App.get_running_app().can_fire:
                sio.emit('fire', {'roomId': room_id, 'userId': user_id, 'x': x, 'y': y})
                btn.text = '?'
        else:
            if placing and len(ship_cells) < 4 and btn.text == '~':
                btn.text = 'S'
                btn.background_color = (0, 0.8, 0, 1)
                ship_cells.append([x, y])
                if len(ship_cells) == 4:
                    sio.emit('place-ships', {'roomId': room_id, 'userId': user_id, 'positions': ship_cells})
                    App.get_running_app().status.text = "Waiting for opponent..."

class BattleshipApp(App):
    def build(self):
        self.can_fire = False
        self.title = "Battleship Mobile"

        self.root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Login
        login_box = BoxLayout(orientation='vertical', size_hint_y=None, height=150)
        self.username_input = TextInput(hint_text='Username', multiline=False)
        login_box.add_widget(self.username_input)
        btn_box = BoxLayout(spacing=10)
        btn_box.add_widget(Button(text='Register', on_press=self.register))
        btn_box.add_widget(Button(text='Login', on_press=self.login))
        login_box.add_widget(btn_box)
        self.root.add_widget(login_box)

        # Lobby
        self.lobby = BoxLayout(orientation='vertical', size_hint_y=None, height=100)
        self.lobby.add_widget(Button(text='Create Room', on_press=self.create_room))
        join_box = BoxLayout()
        self.room_input = TextInput(hint_text='Room ID', multiline=False, size_hint_x=0.6)
        join_box.add_widget(self.room_input)
        join_box.add_widget(Button(text='Join', on_press=self.join_room, size_hint_x=0.4))
        self.lobby.add_widget(join_box)
        self.root.add_widget(self.lobby)
        self.lobby.opacity = 0
        self.lobby.disabled = True

        # Game
        game_box = BoxLayout(orientation='vertical')
        self.status = Label(text='Waiting...', size_hint_y=None, height=50, color=(1,1,0,1))
        game_box.add_widget(self.status)

        boards = BoxLayout(spacing=20)
        self.player_board = Board(is_player=True)
        self.opponent_board = Board(is_player=False)
        boards.add_widget(self.player_board)
        boards.add_widget(self.opponent_board)
        game_box.add_widget(boards)
        self.root.add_widget(game_box)
        self.game_box = game_box
        self.game_box.opacity = 0
        self.game_box.disabled = True

        return self.root

    def register(self, *args):
        self.auth('register')

    def login(self, *args):
        self.auth('login')

    def auth(self, mode):
        name = self.username_input.text.strip()
        if not name:
            self.popup("Error", "Enter username")
            return
        try:
            resp = requests.post(f"{USER_URL}/{mode}", json={"username": name})
            if resp.status_code in (200, 201):
                global user_id, username
                data = resp.json()
                user_id = data["userId"]
                username = name
                self.show_lobby()
                self.connect_socket()
            else:
                self.popup("Error", resp.json().get("error", "Failed"))
        except:
            self.popup("Error", "Cannot reach server")

    def show_lobby(self):
        self.root.children[2].opacity = 0
        self.root.children[2].disabled = True
        self.lobby.opacity = 1
        self.lobby.disabled = False

    def connect_socket(self):
        def run():
            try:
                sio.connect(WS_URL)
            except:
                pass
        threading.Thread(target=run, daemon=True).start()

    def create_room(self, *args):
        try:
            resp = requests.post(f"{ROOM_URL}/rooms")
            global room_id
            room_id = resp.json()["roomId"]
            self.start_game_flow()
        except:
            self.popup("Error", "Failed to create room")

    def join_room(self, *args):
        try:
            rid = int(self.room_input.text)
            global room_id
            room_id = rid
            resp = requests.post(f"{ROOM_URL}/rooms/{rid}/join", json={"userId": user_id})
            if resp.status_code == 200:
                self.start_game_flow()
            else:
                self.popup("Error", "Cannot join room")
        except:
            self.popup("Error", "Invalid room ID")

    def start_game_flow(self):
        self.lobby.opacity = 0
        self.lobby.disabled = True
        self.game_box.opacity = 1
        self.game_box.disabled = False
        self.status.text = "Waiting for opponent..."
        sio.emit('join-game', {'roomId': room_id, 'userId': user_id})
        requests.post(f"{GAME_URL}/games/{room_id}/start")

    def popup(self, title, msg):
        Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.4)).open()

# === SOCKET EVENTS ===
@sio.on('joined')
def on_joined(data):
    Clock.schedule_once(lambda dt: setattr(BattleshipApp.get_running_app().status, 'text', 'Opponent joined!'))

@sio.on('game-ready')
def on_ready(data):
    global placing
    placing = True
    ship_cells.clear()
    Clock.schedule_once(lambda dt: BattleshipApp.get_running_app().status.update_text("Place 4 ship cells"))

@sio.on('move-update')
def on_move(data):
    x, y, hit = data['x'], data['y'], data['hit']
    marker = 'X' if hit else 'O'
    color = (1, 0, 0, 1) if hit else (0.7, 0.7, 0.7, 1)
    app = BattleshipApp.get_running_app()
    cell = app.opponent_board.cells[(x, y)]
    Clock.schedule_once(lambda dt: [setattr(cell, 'text', marker), setattr(cell, 'background_color', color)])
    turn_text = "Your turn!" if data['turn'] == user_id else "Opponent turn"
    Clock.schedule_once(lambda dt: setattr(app.status, 'text', turn_text))
    app.can_fire = data['turn'] == user_id

@sio.on('game-over')
def on_over(data):
    msg = "YOU WIN!" if data['winner'] == user_id else "You lost."
    Clock.schedule_once(lambda dt: setattr(BattleshipApp.get_running_app().status, 'text', msg))

if __name__ == '__main__':
    BattleshipApp().run()