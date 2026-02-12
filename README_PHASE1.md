# 🎯 Distributed Vision-Control System — Phase 1
## Face-Locked Servo (Open-Loop Actuation)

> **Team:** elvin01 · **Phase:** 1 — Open-Loop (no feedback)

---

## Architecture

```
┌──────────┐   MQTT publish    ┌────────────────────────────┐   WebSocket push   ┌───────────┐
│  PC      │ ────────────────→ │  VPS (157.173.101.159)     │ ─────────────────→ │ Dashboard │
│  Vision  │                   │  ┌─────────┐ ┌──────────┐  │                    │ (Browser) │
│  Node    │                   │  │Mosquitto│→│ws_relay  │  │                    └───────────┘
└──────────┘                   │  │ :1883   │ │ :9002    │  │
                               │  └─────────┘ └──────────┘  │
                               └────────────┬───────────────┘
                                   MQTT deliver
                                            ↓
                                      ┌──────────┐
                                      │ ESP8266  │
                                      │ + Servo  │
                                      └──────────┘
```

### Golden Rules

| Component | Speaks | Forbidden |
|-----------|--------|-----------|
| PC Vision | MQTT only | WebSocket, HTTP, direct ESP |
| ESP8266 | MQTT only | WebSocket, HTTP, browser |
| Backend (VPS) | MQTT + WebSocket relay | Business logic |
| Dashboard | WebSocket only | MQTT, polling |

---

## MQTT Topic Structure

| Topic | Publisher | Subscribers | Payload |
|-------|----------|------------|---------|
| `vision/elvin01/movement` | PC Vision | ESP8266, ws_relay | `{"status":"MOVE_LEFT","confidence":0.87,"timestamp":1730000000}` |

Movement states: `MOVE_LEFT`, `MOVE_RIGHT`, `CENTERED`, `NO_FACE`

---

## Repository Structure

```
Face-Locking-with-servo/
├── pc_vision/                 # PC Vision MQTT publisher
│   ├── __init__.py
│   ├── config.py              # Broker IP, team ID, thresholds
│   ├── movement_detector.py   # Derives movement from face position
│   ├── mqtt_publisher.py      # paho-mqtt client wrapper
│   └── main.py                # Entry point
├── esp8266/                   # ESP8266 MicroPython
│   ├── config.py              # WiFi, MQTT, servo pin settings
│   ├── boot.py                # WiFi auto-connect on power-up
│   └── main.py                # MQTT subscribe + servo control
├── backend/                   # VPS services
│   ├── ws_relay.py            # MQTT→WebSocket relay (port 9002)
│   └── requirements.txt
├── dashboard/
│   └── index.html             # Real-time web UI (WebSocket)
├── docs/
│   ├── MANUAL_CONFIGURATION.md
│   └── SETUP_COMMANDS.md
├── src/                       # Existing face-lock vision code
├── data/                      # Enrolled face data + history
├── models/                    # ArcFace ONNX model
└── README_PHASE1.md           # ← This file
```

---

## How Phase 1 Works

1. **PC captures camera frame** → runs face detection/recognition → locks onto target face
2. **MovementDetector** compares face bounding box center vs frame center:
   - Face left of center → `MOVE_LEFT`
   - Face right of center → `MOVE_RIGHT`
   - Face near center → `CENTERED`
   - No face detected → `NO_FACE`
3. **Publishes JSON to MQTT** only on state change (anti-flooding)
4. **ESP8266 receives** command → steps servo left/right/center
5. **VPS relays** MQTT to WebSocket → **Dashboard shows** real-time status

**Phase 1 is open-loop**: the camera does NOT move with the servo. The servo simply points in the direction the face moved.

---

## Setup Instructions

### 1. VPS Setup

```bash
ssh user323@157.173.101.159
# Install Mosquitto
sudo apt update && sudo apt install -y mosquitto mosquitto-clients
# Allow external connections
echo -e "listener 1883 0.0.0.0\nallow_anonymous true" | sudo tee /etc/mosquitto/conf.d/external.conf
sudo systemctl restart mosquitto

# Install Python deps for relay
pip3 install paho-mqtt websockets
# Upload ws_relay.py to VPS, then run:
python3 ws_relay.py
```

### 2. PC Setup (Kali Linux)

```bash
cd Face-Locking-with-servo
source .venv/bin/activate
pip install paho-mqtt
# Run the vision node:
python -m pc_vision.main
```

### 3. ESP8266 Setup

1. Flash MicroPython firmware onto ESP8266
2. Edit `esp8266/config.py` — set WiFi SSID/password
3. Upload `config.py`, `boot.py`, `main.py` to ESP8266 via Thonny or ampy
4. Power on — auto-connects WiFi → subscribes MQTT → drives servo

### 4. Dashboard

Open `dashboard/index.html` in any browser. It connects to `ws://157.173.101.159:9002`.

---

## Testing & Verification

```bash
# Test MQTT (from PC or VPS):
mosquitto_sub -h 157.173.101.159 -t "vision/elvin01/movement" -v

# Simulate a movement message:
mosquitto_pub -h 157.173.101.159 -t "vision/elvin01/movement" \
  -m '{"status":"MOVE_LEFT","confidence":0.87,"timestamp":1730000000}'

# Test WebSocket (open dashboard, send MQTT message, verify it appears)
```

---

## How Phase 2 Will Extend This

Phase 2 adds **closed-loop feedback**: the camera mounts on the servo, and the system adjusts until the face is centered (PID control). No architecture changes — just an ESP feedback topic and smarter servo logic.

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| MQTT connection refused | Ensure Mosquitto is running with external listener on port 1883 |
| ESP8266 WiFi fails | Check SSID/password in `esp8266/config.py` |
| Dashboard stays "Connecting" | Check VPS firewall allows port 9002; ensure `ws_relay.py` is running |
| No face detected | Enroll faces first: `python -m src.enroll` |
| Camera not available | Try changing `CAMERA_INDEX` in `pc_vision/config.py` (0, 1, or 2) |
| ESP8266 import error (`umqtt`) | Install: `upip.install('micropython-umqtt.simple')` |
