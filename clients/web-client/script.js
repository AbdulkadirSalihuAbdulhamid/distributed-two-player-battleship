const socket = io('http://localhost:3003');
let userId, username, roomId;
let placingShips = false;
let shipPositions = [];

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const lobby = document.getElementById('lobby');
const game = document.getElementById('game');
const playerBoard = document.getElementById('player-board');
const opponentBoard = document.getElementById('opponent-board');
const status = document.getElementById('status');
const startBtn = document.getElementById('start-game');

// API URLs
const USER_URL = 'http://localhost:3001';
const ROOM_URL = 'http://localhost:3002';
const GAME_URL = 'http://localhost:3003';

// === AUTH ===
function register() {
  const name = document.getElementById('username').value.trim();
  if (!name) return alert('Enter username');
  fetch(`${USER_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: name })
  })
  .then(r => r.json())
  .then(data => {
    userId = data.userId; username = name;
    loginScreen.classList.add('hidden');
    lobby.classList.remove('hidden');
    connectSocket();
  })
  .catch(() => alert('Register failed'));
}

function login() {
  const name = document.getElementById('username').value.trim();
  if (!name) return alert('Enter username');
  fetch(`${USER_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: name })
  })
  .then(r => r.json())
  .then(data => {
    userId = data.userId; username = name;
    loginScreen.classList.add('hidden');
    lobby.classList.remove('hidden');
    connectSocket();
  })
  .catch(() => alert('Login failed'));
}

// === SOCKET ===
function connectSocket() {
  socket.emit('join-game', { roomId: null, userId });
}

// === ROOM ===
function createRoom() {
  fetch(`${ROOM_URL}/rooms`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      roomId = data.roomId;
      joinGame();
    });
}

function joinRoom() {
  roomId = parseInt(document.getElementById('roomId').value);
  fetch(`${ROOM_URL}/rooms/${roomId}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId })
  })
  .then(r => r.json())
  .then(() => joinGame())
  .catch(() => alert('Failed to join room'));
}

function joinGame() {
  lobby.classList.add('hidden');
  game.classList.remove('hidden');
  renderBoard(playerBoard, true);
  renderBoard(opponentBoard, false);
  socket.emit('join-game', { roomId, userId });
  status.textContent = 'Waiting for opponent...';
}

// === BOARD ===
function renderBoard(boardEl, isPlayer) {
  boardEl.innerHTML = '';
  for (let i = 0; i < 5; i++) {
    for (let j = 0; j < 5; j++) {
      const cell = document.createElement('div');
      cell.classList.add('cell');
      cell.dataset.x = i;
      cell.dataset.y = j;
      if (isPlayer) {
        cell.onclick = () => placeShip(i, j);
      } else {
        cell.onclick = () => fire(i, j);
      }
      boardEl.appendChild(cell);
    }
  }
}

function placeShip(x, y) {
  if (!placingShips || shipPositions.length >= 4) return;
  const cell = playerBoard.querySelector(`[data-x="${x}"][data-y="${y}"]`);
  if (cell.classList.contains('ship')) return;

  cell.classList.add('ship');
  cell.textContent = 'S';
  shipPositions.push([x, y]);

  if (shipPositions.length === 4) {
    socket.emit('place-ships', { roomId, userId, positions: shipPositions });
    placingShips = false;
    status.textContent = 'Waiting for opponent...';
  }
}

function fire(x, y) {
  const cell = opponentBoard.querySelector(`[data-x="${x}"][data-y="${y}"]`);
  if (cell.textContent) return;
  socket.emit('fire', { roomId, userId, x, y });
  cell.textContent = '?';
}

// === START GAME ===
function startGame() {
  fetch(`${GAME_URL}/games/${roomId}/start`, { method: 'POST' });
  placingShips = true;
  status.textContent = 'Place 4 ship cells (click on your board)';
  startBtn.classList.add('hidden');
}

// === SOCKET EVENTS ===
socket.on('joined', data => {
  if (data.roomId === roomId) {
    status.textContent = 'Opponent joined! Click "Start Game"';
    startBtn.classList.remove('hidden');
  }
});

socket.on('ships-placed', () => {
  status.textContent = 'Opponent placed ships...';
});

socket.on('game-ready', data => {
  status.textContent = `Game started! ${data.turn === userId ? 'Your turn!' : 'Opponent turn'}`;
});

socket.on('move-update', data => {
  const { x, y, hit, turn } = data;
  const cell = opponentBoard.querySelector(`[data-x="${x}"][data-y="${y}"]`);
  cell.textContent = hit ? 'X' : 'O';
  cell.classList.add(hit ? 'hit' : 'miss');
  status.textContent = turn === userId ? 'Your turn!' : 'Opponent turn';
});

socket.on('game-over', data => {
  status.textContent = data.winner === userId ? 'YOU WIN!' : 'You lost.';
  opponentBoard.querySelectorAll('.cell').forEach(c => c.onclick = null);
});