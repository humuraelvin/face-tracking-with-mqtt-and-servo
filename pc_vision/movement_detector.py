# pc_vision/movement_detector.py
"""
Derives movement state from the face-lock bounding box.

Movement states:
    MOVE_LEFT   – face is to the LEFT of frame center  (servo should pan left)
    MOVE_RIGHT  – face is to the RIGHT of frame center (servo should pan right)
    CENTERED    – face is roughly centred
    NO_FACE     – no face detected / lock lost

Includes hysteresis to prevent rapid toggling at the dead-zone boundary,
and sends a proportional offset so the ESP can make proportional moves.
"""

from __future__ import annotations
import time
from typing import Dict, Optional, Tuple

from .config import DEAD_ZONE_RATIO, HYSTERESIS_RATIO, MIN_PUBLISH_INTERVAL


# Movement states (matches spec)
MOVE_LEFT = "MOVE_LEFT"
MOVE_RIGHT = "MOVE_RIGHT"
CENTERED = "CENTERED"
NO_FACE = "NO_FACE"


class MovementDetector:
    """Converts face-lock frame results into discrete movement commands."""

    def __init__(self, dead_zone_ratio: float = DEAD_ZONE_RATIO,
                 hysteresis_ratio: float = HYSTERESIS_RATIO):
        """
        Args:
            dead_zone_ratio: fraction of frame width (each side of center)
                             within which the face is considered CENTERED.
            hysteresis_ratio: extra band outside dead zone – once CENTERED,
                              the face must exceed dead_zone + hysteresis
                              before switching to MOVE_LEFT/RIGHT.
        """
        self.dead_zone_ratio = float(dead_zone_ratio)
        self.hysteresis_ratio = float(hysteresis_ratio)
        self._prev_state: Optional[str] = None
        self._last_publish_time: float = 0.0

    def compute(
        self,
        frame_result: Dict,
        frame_width: int,
    ) -> Optional[Dict]:
        """
        Analyse a single frame result from FaceLockSystem.process_frame().

        Returns:
            A dict ready for MQTT publishing if the state changed (or
            MIN_PUBLISH_INTERVAL elapsed), otherwise None (skip publish).
            Format: {"status": "...", "confidence": 0.87, "offset": 0.25,
                     "timestamp": 1730...}
        """
        now = time.time()
        state = frame_result.get("state", "searching")
        face_box = frame_result.get("face_box")  # (x1, y1, x2, y2) or None
        confidence = frame_result.get("lock_confidence", 0.0)

        # ── Determine movement status ───────────────────────────────
        offset = 0.0  # proportional offset (-0.5 to +0.5)

        if state == "searching" or face_box is None:
            movement = NO_FACE
            confidence = 0.0
        else:
            x1, y1, x2, y2 = face_box
            face_cx = (x1 + x2) / 2.0
            frame_cx = frame_width / 2.0

            # Offset as fraction of frame width (-0.5 = far left, +0.5 = far right)
            offset = (face_cx - frame_cx) / frame_width

            # ── Hysteresis logic ────────────────────────────────────
            # If currently CENTERED, require exceeding dead_zone + hysteresis
            # to switch to MOVE. Otherwise, just use dead_zone to return
            # to CENTERED.
            if self._prev_state == CENTERED:
                threshold = self.dead_zone_ratio + self.hysteresis_ratio
            else:
                threshold = self.dead_zone_ratio

            if abs(offset) <= threshold:
                movement = CENTERED
            elif offset < 0:
                movement = MOVE_LEFT
            else:
                movement = MOVE_RIGHT

        # ── Anti-flooding: publish only on change or periodic refresh ─
        state_changed = (movement != self._prev_state)
        interval_elapsed = (now - self._last_publish_time) >= MIN_PUBLISH_INTERVAL

        if not state_changed and not interval_elapsed:
            return None  # skip — nothing new to report

        self._prev_state = movement
        self._last_publish_time = now

        return {
            "status": movement,
            "confidence": round(float(confidence), 3),
            "offset": round(float(offset), 4),
            "timestamp": int(now),
        }
