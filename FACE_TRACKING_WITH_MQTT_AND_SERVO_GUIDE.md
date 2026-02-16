# 🎯 PHASE 1 — COMPLETE SETUP GUIDE (FULLY LOCAL)

> **Everything runs on your PC. No VPS. No cloud.**
>
> The servo will follow your face: you move left, it moves left. You move right, it moves right.

---

## WHAT HAPPENS

```
Your PC (camera + face detection + MQTT broker + dashboard)
    │
    │  MQTT messages over WiFi
    ▼
ESP8266 + Servo Motor
(rotates to follow your face)
```

Your PC does 3 things:
1. Detects your face and publishes movement commands via MQTT
2. Runs the MQTT broker (Mosquitto)
3. Runs the WebSocket relay + dashboard so you can watch status in a browser

The ESP8266 subscribes to MQTT, receives commands, and drives the servo.

---

## STEP 1 — INSTALL MOSQUITTO ON YOUR PC

Open a terminal and run:

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
```

Make Mosquitto listen on all network interfaces (so ESP8266 on WiFi can reach it):

```bash
sudo bash -c 'cat > /etc/mosquitto/conf.d/external.conf << EOF
listener 1883 0.0.0.0
allow_anonymous true
EOF'
```

Restart it:

```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

Verify it is running (you should see `:1883`):

```bash
ss -tlnp | grep 1883
```

Expected:
```
LISTEN  0  100  0.0.0.0:1883  0.0.0.0:*
```

---

## STEP 2 — FIND YOUR PC's LOCAL IP ADDRESS

Run:

```bash
hostname -I | awk '{print $1}'
```

This prints something like `192.168.1.100`. **Write this number down** — you need it in Step 6.

---

## STEP 3 — INSTALL PYTHON DEPENDENCIES

```bash
cd "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo"
source .venv/bin/activate
pip install paho-mqtt websockets
```

---

## STEP 4 — TEST MOSQUITTO IS WORKING

Open **two terminals side by side**.

**Terminal 1** — subscribe (listener):

```bash
mosquitto_sub -h 127.0.0.1 -t "vision/elvin01/movement" -v
```

**Terminal 2** — publish (sender):

```bash
mosquitto_pub -h 127.0.0.1 -t "vision/elvin01/movement" -m '{"status":"MOVE_LEFT","confidence":0.87,"timestamp":1730000000}'
```

Terminal 1 should immediately show the message. If it does — MQTT is working. ✅

Close both terminals.

---

## STEP 5 — FLASH MICROPYTHON ONTO ESP8266

Connect the ESP8266 to your PC via USB.

```bash
pip install esptool adafruit-ampy
```

Find the port:

```bash
ls /dev/ttyUSB*
```

You should see `/dev/ttyUSB0`. Use that in all commands below.

Erase the chip:

```bash
python -m esptool --port /dev/ttyUSB0 erase_flash
```

Download MicroPython from https://micropython.org/download/esp8266/ — get the latest `.bin` file. Then flash:

```bash
python -m esptool --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 ~/Downloads/ESP8266*.bin
```

---

## STEP 6 — EDIT ESP8266 CONFIG

Open the config file:

```bash
nano "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo/esp8266/config.py"
```

Change **three** values:

```python
WIFI_SSID     = "YOUR_ACTUAL_WIFI_NAME"       # ← your WiFi name
WIFI_PASSWORD = "YOUR_ACTUAL_WIFI_PASSWORD"   # ← your WiFi password
MQTT_BROKER   = "192.168.x.x"                # ← your PC's IP from Step 2
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## STEP 7 — INSTALL MQTT LIBRARY ON ESP8266

Connect to the ESP8266 REPL:

```bash
python -m serial.tools.miniterm /dev/ttyUSB0 115200
```

At the `>>>` prompt, first connect to WiFi (type each line, press Enter):

```python
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('YOUR_WIFI_SSID', 'YOUR_WIFI_PASSWORD')
```

Wait 5 seconds, then check:

```python
wlan.isconnected()
```

It must say `True`. Then install the MQTT library:

```python
import mip
mip.install('umqtt.simple')
```

Wait for it to finish. Exit miniterm: press `Ctrl+]`.

---

## STEP 8 — UPLOAD CODE TO ESP8266

```bash
python -m ampy --port /dev/ttyUSB0 put "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo/esp8266/config.py" config.py
python -m ampy --port /dev/ttyUSB0 put "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo/esp8266/boot.py" boot.py
python -m ampy --port /dev/ttyUSB0 put "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo/esp8266/main.py" main.py
```

---

## STEP 9 — WIRE THE SERVO

```
ESP8266 NodeMCU Pin          Servo Wire
─────────────────          ──────────────
D4 (GPIO2)          →     Orange/Yellow (Signal)
3V3 or VIN          →     Red           (Power)
GND                 →     Brown         (Ground)
```

If the servo jitters or resets the ESP, power the servo from a separate 5V supply and share GND with the ESP.

---

## STEP 10 — TEST ESP8266

Unplug and replug the ESP8266 USB (or press RESET). Watch:

```bash
python -m serial.tools.miniterm /dev/ttyUSB0 115200
```

You should see:

```
[WiFi] Connecting to YOUR_WIFI ...
[WiFi] Connected! IP: 192.168.x.x
[MQTT] Connecting to 192.168.x.x ...
[MQTT] Connected and subscribed to: vision/elvin01/movement
[Main] Waiting for movement commands...
```

**Test servo** — open another terminal:

```bash
mosquitto_pub -h 127.0.0.1 -t "vision/elvin01/movement" -m '{"status":"MOVE_LEFT","confidence":0.9,"timestamp":1730000000}'
```

Servo should move. Try `MOVE_RIGHT`:

```bash
mosquitto_pub -h 127.0.0.1 -t "vision/elvin01/movement" -m '{"status":"MOVE_RIGHT","confidence":0.9,"timestamp":1730000001}'
```

Exit picocom: `Ctrl+A` then `Ctrl+X`.

---

## STEP 11 — RUN EVERYTHING (3 terminals needed)

You need **3 terminal windows** open. All from the project directory:

```bash
cd "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo"
source .venv/bin/activate
```

### Terminal 1 — WebSocket Relay

```bash
cd "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo"
source .venv/bin/activate
python backend/ws_relay.py
```

Expected output:
```
MQTT → WebSocket Relay
[MQTT] Connecting to 127.0.0.1:1883 ...
[WS]   Listening on ws://0.0.0.0:9002
[Relay] Ready — MQTT → WebSocket relay active
```

Leave it running.

### Terminal 2 — Dashboard (optional but nice)

Open your browser and go to:

```
file:///home/humura/Documents/workings/Year%203/Intelligent%20Robotics/Face-Locking-with-servo/dashboard/index.html
```

You should see the dashboard with "Connected" badge.

### Terminal 3 — Vision Node (the main one)

```bash
cd "/home/humura/Documents/workings/Year 3/Intelligent Robotics/Face-Locking-with-servo"
source .venv/bin/activate
python -m pc_vision.main
```

It will show your enrolled faces. Type the name of the person to track (e.g., `Humura`) and press Enter.

A camera window opens with your face detected.

---

## STEP 12 — IT WORKS

- **Move your face left** → servo pans left + dashboard shows MOVE_LEFT
- **Move your face right** → servo pans right + dashboard shows MOVE_RIGHT
- **Stay centered** → servo goes to center (90°) + dashboard shows CENTERED
- **Leave the frame** → servo holds position + dashboard shows NO_FACE

**Controls in the camera window:**
- Press `r` to release lock
- Press `q` to quit

---

## STOPPING

- **Camera window**: press `q`
- **WebSocket relay** (Terminal 1): press `Ctrl+C`
- Mosquitto keeps running in the background (it's a system service)

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| `Connection refused` on MQTT | Run `sudo systemctl start mosquitto` |
| ESP8266 WiFi fails | Wrong SSID/password in `esp8266/config.py`. Edit, re-upload (Step 6 + Step 8) |
| ESP8266 can't reach MQTT | Wrong PC IP in `esp8266/config.py`. Re-check Step 2 |
| Dashboard says "Connecting…" | Terminal 1 (ws_relay) not running. Start it |
| Camera not found | Edit `pc_vision/config.py` — change `CAMERA_INDEX` to `0` or `1` |
| No enrolled faces | Run `python -m src.enroll` first |
| `ImportError: umqtt` on ESP | Step 7 failed. Redo it |
| Servo jitters | Power servo from external 5V, share GND with ESP |
