#!/usr/bin/env python3
"""
Upload files to ESP8266 using MicroPython RAW REPL mode.
Robust version with small chunks, GC, retries, and reconnect logic.

NOTE: main.py is uploaded as 'app.py' so it does NOT auto-run.
      This gives you the >>> prompt in miniterm.
      To start the program, type:  exec(open('app.py').read())
"""

import serial
import time
import sys
import os
import binascii


PORT = "/dev/ttyUSB0"
BAUD = 115200


def open_serial():
    """Open serial port with retry."""
    for attempt in range(5):
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            time.sleep(0.5)
            return ser
        except Exception as e:
            print(f"  Cannot open {PORT}: {e}")
            if attempt < 4:
                print(f"  Retrying in 2s... ({attempt+1}/5)")
                time.sleep(2)
    print("  FAILED to open serial port after 5 attempts.")
    sys.exit(1)


def enter_raw_repl(ser):
    """Enter MicroPython raw REPL mode."""
    ser.write(b"\x03\x03")  # Ctrl+C twice to interrupt
    time.sleep(0.5)
    ser.read(ser.in_waiting)  # flush

    ser.write(b"\x01")  # Ctrl+A = enter raw REPL
    time.sleep(0.5)
    data = ser.read(ser.in_waiting)
    if b"raw REPL" not in data:
        ser.write(b"\x03\x03")
        time.sleep(0.5)
        ser.read(ser.in_waiting)
        ser.write(b"\x01")
        time.sleep(1.0)
        data = ser.read(ser.in_waiting)
    return b"raw REPL" in data


def exec_raw(ser, code, timeout=10):
    """Execute code in raw REPL mode and return output."""
    ser.read(ser.in_waiting)  # flush

    # Send code in small pieces with delays
    encoded = code.encode()
    for i in range(0, len(encoded), 128):
        ser.write(encoded[i:i+128])
        time.sleep(0.03)

    ser.write(b"\x04")  # Ctrl+D = execute
    time.sleep(0.2)

    # Read response
    result = b""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if ser.in_waiting:
            result += ser.read(ser.in_waiting)
            if b"\x04>" in result:
                break
        time.sleep(0.05)

    text = result.decode(errors="replace")
    return text


def upload_file_raw(ser, local_path, remote_path):
    """Upload a file using raw REPL + hex encoding, with small chunks and GC."""
    with open(local_path, "rb") as f:
        content = f.read()

    hex_data = binascii.hexlify(content).decode()

    # Use SMALL chunks to avoid ESP8266 memory issues
    chunk_size = 256  # hex chars per chunk (= 128 bytes of data)

    # Run GC before starting
    exec_raw(ser, "import gc; gc.collect()")
    time.sleep(0.1)

    # Open file
    exec_raw(ser, f"_f = open('{remote_path}', 'wb')")
    time.sleep(0.1)

    total = len(hex_data)
    written = 0
    gc_counter = 0

    for i in range(0, total, chunk_size):
        chunk = hex_data[i:i+chunk_size]
        exec_raw(ser, f"_f.write(bytes.fromhex('{chunk}'))")
        written += len(chunk)
        gc_counter += 1
        time.sleep(0.05)

        # Run GC every 8 chunks to free memory
        if gc_counter >= 8:
            exec_raw(ser, "gc.collect()")
            gc_counter = 0
            time.sleep(0.1)

    exec_raw(ser, "_f.close()")
    exec_raw(ser, "gc.collect()")
    time.sleep(0.2)


def upload_one_file(ser, local_path, remote_path, label):
    """Upload a single file with retry logic."""
    for attempt in range(3):
        try:
            print(f"Uploading {label} ...", end=" ", flush=True)
            upload_file_raw(ser, local_path, remote_path)
            print("✓")
            return True
        except (OSError, serial.SerialException) as e:
            print(f"✗ (attempt {attempt+1}/3: {e})")
            if attempt < 2:
                print("  Reconnecting...", end=" ", flush=True)
                try:
                    ser.close()
                except:
                    pass
                time.sleep(2)
                try:
                    ser2 = open_serial()
                    # Re-enter raw REPL
                    enter_raw_repl(ser2)
                    # Copy the new serial object back
                    ser.__dict__.update(ser2.__dict__)
                    print("✓")
                except:
                    print("✗")
                    return False
    return False


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    esp_dir = os.path.join(base, "esp8266")
    umqtt_file = "/tmp/umqtt/simple.py"

    print("═══════════════════════════════════════")
    print("  ESP8266 Uploader (Robust)")
    print("═══════════════════════════════════════\n")

    ser = open_serial()

    print("Entering raw REPL...", end=" ", flush=True)
    if not enter_raw_repl(ser):
        print("FAILED. Trying hard reset...")
        ser.write(b"\x03\x03")
        time.sleep(1)
        ser.write(b"\x04")  # soft reboot
        time.sleep(3)
        ser.write(b"\x03")
        time.sleep(0.5)
        if not enter_raw_repl(ser):
            print("Still FAILED. Unplug/replug ESP and try again.")
            sys.exit(1)
    print("✓")

    # Delete old main.py if it exists (prevent auto-run)
    print("Removing old main.py (prevent auto-run)...", end=" ", flush=True)
    exec_raw(ser, "import gc")
    exec_raw(ser, """
try:
    import os
    os.remove('main.py')
except:
    pass
""")
    print("✓")

    # Create directories
    print("Creating directories...", end=" ", flush=True)
    exec_raw(ser, "import os")
    exec_raw(ser, "try:\n os.mkdir('lib')\nexcept:\n pass")
    exec_raw(ser, "try:\n os.mkdir('lib/umqtt')\nexcept:\n pass")
    exec_raw(ser, "_f = open('lib/umqtt/__init__.py', 'w'); _f.close()")
    exec_raw(ser, "gc.collect()")
    print("✓")

    # Upload files one by one with retries
    all_ok = True

    if os.path.exists(umqtt_file):
        if not upload_one_file(ser, umqtt_file, "lib/umqtt/simple.py", "umqtt/simple.py"):
            all_ok = False

    for fname in ["config.py", "boot.py"]:
        fpath = os.path.join(esp_dir, fname)
        if os.path.exists(fpath):
            if not upload_one_file(ser, fpath, fname, fname):
                all_ok = False

    # Upload main.py as app.py
    main_path = os.path.join(esp_dir, "main.py")
    if os.path.exists(main_path):
        if not upload_one_file(ser, main_path, "app.py", "main.py → app.py"):
            all_ok = False

    if not all_ok:
        print("\n⚠ Some uploads failed. Try unplugging/replugging and running again.")
        ser.close()
        sys.exit(1)

    # Verify
    print("\nVerifying files...", end=" ", flush=True)
    result = exec_raw(ser, "import os; print(os.listdir())")
    print("✓")
    if "OK" in result:
        parts = result.split("OK", 1)
        if len(parts) > 1:
            output = parts[1].split("\x04")[0].strip()
            print(f"  Root: {output}")

    result2 = exec_raw(ser, """
import os
try:
    print(os.listdir('lib/umqtt'))
except:
    print('lib/umqtt NOT FOUND')
""")
    if "OK" in result2:
        parts = result2.split("OK", 1)
        if len(parts) > 1:
            output = parts[1].split("\x04")[0].strip()
            print(f"  lib/umqtt: {output}")

    # Exit raw REPL and soft reset
    ser.write(b"\x02")  # Ctrl+B = exit raw REPL
    time.sleep(0.3)
    print("\n✓ Upload complete! Resetting ESP8266...\n")
    ser.write(b"\x04")  # Ctrl+D = soft reset
    time.sleep(3)

    # Read boot output
    output = b""
    t0 = time.time()
    while time.time() - t0 < 15:
        try:
            if ser.in_waiting:
                output += ser.read(ser.in_waiting)
        except:
            break
        time.sleep(0.1)

    boot_text = output.decode(errors="replace")
    print("── ESP8266 Boot Output ──")
    print(boot_text)

    if ">>>" in boot_text:
        print("\n✓ You have the >>> prompt!")
        print("\n  Now open miniterm:")
        print("    python -m serial.tools.miniterm /dev/ttyUSB1 115200")
        print("\n  Then run:")
        print("    exec(open('app.py').read())")

    ser.close()


if __name__ == "__main__":
    main()
