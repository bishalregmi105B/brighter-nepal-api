"""
Test script — verifies brighter-nepal-chat socket URL is working.
Run: python test_chat.py

Requirements (auto-installed): requests, python-socketio[client], websocket-client
"""
import subprocess, sys

# ── Auto-install deps if missing ──────────────────────────────────────────────
for pkg in ['requests', 'python-socketio[client]', 'websocket-client']:
    try:
        __import__(pkg.split('[')[0].replace('-', '_'))
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pkg])

import requests
import json
import time
import socketio as sio_lib

from flask_jwt_extended import create_access_token
from app import create_app

CHAT_URL = 'https://brighter-nepal-chat.onrender.com'

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — HTTP health check
# ─────────────────────────────────────────────────────────────────────────────
print('\n[1] Health check ...')
try:
    r = requests.get(f'{CHAT_URL}/health', timeout=15)
    print(f'    Status : {r.status_code}')
    print(f'    Body   : {r.json()}')
    assert r.status_code == 200, 'Health check failed'
    print('    ✓ Service is up')
except Exception as e:
    print(f'    ✗ FAILED: {e}')
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Generate a real JWT for admin user (id=1)
# ─────────────────────────────────────────────────────────────────────────────
print('\n[2] Generating JWT token ...')
flask_app = create_app()
with flask_app.app_context():
    from app.models import User
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        print('    ✗ No admin user found in DB — run add_users.py first')
        sys.exit(1)
    identity = json.dumps({'id': admin.id, 'role': admin.role, 'st': admin.session_token or 'test'})
    token = create_access_token(identity=identity)
    print(f'    ✓ Token generated for: {admin.email}')

# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — WebSocket connection + join room
# ─────────────────────────────────────────────────────────────────────────────
print('\n[3] WebSocket connection test ...')

results = {'connected': False, 'history': None, 'error': None}

sio = sio_lib.Client(logger=False, engineio_logger=False)

@sio.event
def connect():
    results['connected'] = True
    print('    ✓ WebSocket connected')
    sio.emit('join', {'token': token, 'room': 'group:1'})

@sio.on('history')
def on_history(data):
    results['history'] = data
    print(f'    ✓ Received history — {len(data)} messages')
    sio.disconnect()

@sio.on('error')
def on_error(data):
    results['error'] = data.get('msg')
    print(f'    ✗ Server error: {data.get("msg")}')
    sio.disconnect()

@sio.event
def disconnect():
    print('    ✓ Disconnected cleanly')

try:
    sio.connect(CHAT_URL, transports=['websocket', 'polling'], wait_timeout=15)
    # Wait max 10s for history/error response
    deadline = time.time() + 10
    while time.time() < deadline and sio.connected:
        time.sleep(0.2)
    if sio.connected:
        print('    ✗ Timed out waiting for history/error response from server')
        sio.disconnect()
except Exception as e:
    print(f'    ✗ Connection failed: {e}')
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print('\n─── RESULTS ───────────────────────────────')
print(f'  Health check : ✓')
print(f'  Connected    : {"✓" if results["connected"] else "✗"}')
print(f'  Room joined  : {"✓ (got history)" if results["history"] is not None else "✗"}')
if results['error']:
    print(f'  Server error : {results["error"]}')
print('───────────────────────────────────────────\n')
