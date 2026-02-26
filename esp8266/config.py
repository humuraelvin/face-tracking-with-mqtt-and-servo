# esp8266/config.py
"""
ESP8266 Configuration — MicroPython
Edit BEFORE uploading to the board.
"""

# ─── WiFi ───────────────────────────────────────────────────────────
WIFI_SSID     = "London is Red"       # ← CHANGE THIS
WIFI_PASSWORD = "london123@"   # ← CHANGE THIS

# ─── MQTT Broker (your PC's local IP — NOT localhost) ──────────────
MQTT_BROKER   = "192.168.0.193"         
MQTT_PORT     = 1883
TEAM_ID       = "elvin01"
MQTT_TOPIC    = "vision/{}/movement".format(TEAM_ID)
CLIENT_ID     = "esp8266_{}".format(TEAM_ID)

# ─── Servo ──────────────────────────────────────────────────────────
SERVO_PIN     = 14         # GPIO14 (D5 on NodeMCU)
SERVO_MIN_ANGLE = 0        # degrees (physical limit)
SERVO_MAX_ANGLE = 180      # degrees (physical limit)
SERVO_CENTER    = 90       # neutral / centered position

# Proportional step: larger offset → larger step
SERVO_STEP_MIN  = 1        # degrees for smallest offset
SERVO_STEP_MAX  = 8        # degrees for largest offset

# Scanning (NO_FACE): slow sweep back and forth
SCAN_STEP       = 2        # degrees per scan tick
SCAN_DELAY_MS   = 100      # ms between scan ticks

# ─── PWM (50 Hz standard servo) ────────────────────────────────────
SERVO_FREQ    = 50         # Hz
# Duty range for 0-180 deg (typical SG90):
#   0°   →  duty ~  40  (0.5 ms pulse)
#   180° →  duty ~ 115  (2.5 ms pulse)
DUTY_MIN      = 40         # duty for 0°
DUTY_MAX      = 115        # duty for 180°
