# esp8266/main.py
"""
main.py — ESP8266 Face-Tracking Servo Controller (MicroPython)

Subscribes to MQTT topic  vision/elvin01/movement  and drives a
servo motor based on face movement commands:

    MOVE_LEFT   → proportional pan left  (bigger offset = faster move)
    MOVE_RIGHT  → proportional pan right (bigger offset = faster move)
    CENTERED    → hold current position (face is centered)
    NO_FACE     → slow sweep/scan to search for face

Servo is driven via PWM on a single GPIO pin (default GPIO14 / D5).

Architecture rule:
    ✅ MQTT only
    ❌ No WebSocket, HTTP, or browser communication
"""

import time
import json
from machine import Pin, PWM
from umqtt.simple import MQTTClient

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_TOPIC,
    CLIENT_ID,
    SERVO_PIN,
    SERVO_MIN_ANGLE,
    SERVO_MAX_ANGLE,
    SERVO_CENTER,
    SERVO_STEP_MIN,
    SERVO_STEP_MAX,
    SERVO_FREQ,
    DUTY_MIN,
    DUTY_MAX,
    SCAN_STEP,
    SCAN_DELAY_MS,
)


# ─── Servo Control ─────────────────────────────────────────────────

class Servo:
    """Simple servo driver using PWM."""

    def __init__(self, pin, freq=50, duty_min=40, duty_max=115):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(freq)
        self.duty_min = duty_min
        self.duty_max = duty_max
        self._angle = SERVO_CENTER

    def angle_to_duty(self, angle):
        """Convert angle (0-180) to PWM duty value."""
        angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
        duty = self.duty_min + (self.duty_max - self.duty_min) * angle / 180
        return int(duty)

    def set_angle(self, angle):
        """Move servo to the given angle (0-180)."""
        angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
        self._angle = angle
        self.pwm.duty(self.angle_to_duty(angle))

    def get_angle(self):
        return self._angle

    def move_proportional(self, direction, offset_abs):
        """Move by a proportional step based on offset magnitude.

        Args:
            direction: -1 for left, +1 for right
            offset_abs: absolute offset (0.0 to 0.5)
        """
        # Map offset (0.0-0.5) to step (STEP_MIN to STEP_MAX)
        t = min(offset_abs / 0.4, 1.0)  # normalize to 0-1
        step = SERVO_STEP_MIN + (SERVO_STEP_MAX - SERVO_STEP_MIN) * t
        step = int(step)
        new_angle = self._angle + direction * step
        self.set_angle(new_angle)

    def center(self):
        """Move to neutral / center position."""
        self.set_angle(SERVO_CENTER)

    def stop(self):
        """Stop PWM signal (release servo)."""
        self.pwm.duty(0)


# ─── Scanner (NO_FACE sweeping) ────────────────────────────────────

class Scanner:
    """Sweeps servo left and right when no face is detected."""

    def __init__(self):
        self._direction = 1  # +1 = sweeping right, -1 = sweeping left
        self._last_tick = 0
        self._active = False

    def start(self, servo):
        """Begin scanning from current position."""
        if not self._active:
            self._active = True
            self._last_tick = time.ticks_ms()

    def stop(self):
        """Stop scanning."""
        self._active = False

    def tick(self, servo):
        """Called from main loop. Moves servo one scan step if enough time passed."""
        if not self._active:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_tick) < SCAN_DELAY_MS:
            return
        self._last_tick = now

        angle = servo.get_angle()
        # Reverse at limits
        if angle >= SERVO_MAX_ANGLE - SCAN_STEP:
            self._direction = -1
        elif angle <= SERVO_MIN_ANGLE + SCAN_STEP:
            self._direction = 1

        servo.set_angle(angle + self._direction * SCAN_STEP)


# ─── MQTT Message Handler ──────────────────────────────────────────

servo = Servo(
    pin=SERVO_PIN,
    freq=SERVO_FREQ,
    duty_min=DUTY_MIN,
    duty_max=DUTY_MAX,
)

scanner = Scanner()

# Start at center
servo.center()
print("[Servo] Initialized at {}°".format(servo.get_angle()))


def on_message(topic, msg):
    """
    Handle incoming MQTT messages.

    Expected payload (JSON):
        {"status": "MOVE_LEFT", "confidence": 0.87, "offset": -0.25,
         "timestamp": 1730000000}
    """
    try:
        payload = json.loads(msg)
        status = payload.get("status", "")
        offset = payload.get("offset", 0.0)
    except (ValueError, KeyError):
        print("[MQTT] Bad message:", msg)
        return

    if status == "MOVE_LEFT":
        scanner.stop()
        offset_abs = abs(offset)
        servo.move_proportional(-1, offset_abs)
        print("[Servo] LEFT  -> {}° (off={})".format(servo.get_angle(), offset))

    elif status == "MOVE_RIGHT":
        scanner.stop()
        offset_abs = abs(offset)
        servo.move_proportional(1, offset_abs)
        print("[Servo] RIGHT -> {}° (off={})".format(servo.get_angle(), offset))

    elif status == "CENTERED":
        scanner.stop()
        # Hold current position — face is centered, don't move
        pass

    elif status == "NO_FACE":
        # Start scanning to find face
        scanner.start(servo)

    else:
        print("[MQTT] Unknown status:", status)


# ─── Main Loop ──────────────────────────────────────────────────────

def run():
    """Connect to MQTT and listen for movement commands forever."""

    while True:
        # ── Connect with retry ──
        client = MQTTClient(
            CLIENT_ID,
            MQTT_BROKER,
            port=MQTT_PORT,
        )
        client.set_callback(on_message)

        print("[MQTT] Connecting to", MQTT_BROKER, "...")
        try:
            client.connect()
            client.subscribe(MQTT_TOPIC)
            print("[MQTT] Connected and subscribed to:", MQTT_TOPIC)
            print("[Main] Waiting for movement commands...\n")
        except Exception as e:
            print("[MQTT] Connection failed:", e)
            print("[MQTT] Retrying in 5 seconds...")
            time.sleep(5)
            continue

        # ── Main message loop ──
        try:
            while True:
                client.check_msg()
                scanner.tick(servo)  # scan if NO_FACE active
                time.sleep_ms(50)
        except KeyboardInterrupt:
            print("\n[Main] Stopped by user")
            servo.stop()
            client.disconnect()
            print("[Main] Disconnected. Servo released.")
            return
        except Exception as e:
            print("[MQTT] Error:", e)
            print("[MQTT] Reconnecting in 3 seconds...")
            time.sleep(3)


# Entry point
run()
