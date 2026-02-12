# DEPLOYMENT.md

# Face Locking System - Deployment & Installation Guide

## Complete Setup Instructions

This guide walks through setting up the Face Locking system from scratch.

---

## Part 1: Environment Setup

### Prerequisites
- **Python**: 3.9+ (verified with 3.11)
- **OS**: macOS, Linux, or Windows
- **Webcam**: USB or built-in camera
- **Disk Space**: 1GB for dependencies + model
- **RAM**: 2GB+ recommended

### Step 1: Clone/Initialize Repository

If starting fresh:
```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/humuraelvin/Face-Locking.git
cd Face-Locking
```

Or if continuing from existing project:
```bash
cd /path/to/Face-Locking
```

### Step 2: Create Python Virtual Environment

```bash
# Create venv
python3.11 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Or activate (Windows PowerShell)
# .venv\Scripts\Activate.ps1
```

### Step 3: Upgrade pip

```bash
python -m pip install --upgrade pip setuptools wheel
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:
```bash
pip install opencv-python==4.8.1.78 \
    numpy==1.24.3 \
    onnxruntime==1.16.3 \
    scipy==1.11.2 \
    tqdm==4.66.1 \
    mediapipe==0.10.32 \
    protobuf==4.24.0
```

**Verify Installation:**
```bash
python -c "import cv2, numpy, onnxruntime, scipy, mediapipe; print('✓ All packages installed')"
```

### Step 5: Download ArcFace ONNX Model

**Option A: Manual Download (Recommended)**

```bash
# Download from SourceForge
curl -L -o buffalo_l.zip \
  "https://sourceforge.net/projects/insightface.mirror/files/v0.7/buffalo_l.zip/download"

# Extract
unzip -o buffalo_l.zip

# Copy to project
cp w600k_r50.onnx models/embedder_arcface.onnx

# Cleanup
rm -f buffalo_l.zip w600k_r50.onnx 1k3d68.onnx 2d106det.onnx det_10g.onnx genderage.onnx
```

**Option B: Script Download**
```bash
cd models
bash download_model.sh
cd ..
```

**Verify Model:**
```bash
ls -lh models/embedder_arcface.onnx
# Should show ~345MB file
```

### Step 6: Verify Camera Access

```bash
python -m src.camera
```

**Expected:**
- Live camera window opens
- Smooth video with FPS counter
- Press **q** to exit

**If camera doesn't work:**
- **macOS**: System Settings → Privacy & Security → Camera → Allow Terminal/VS Code
- **Linux**: `sudo usermod -aG video $USER` (then logout/login)
- **Windows**: Check Device Manager for camera device

---

## Part 2: Test Individual Modules

Run in order. Each test validates one stage.

### Test 1: Face Detection
```bash
python -m src.detect
```
✓ Should see green bounding box around face

### Test 2: 5-Point Landmarks
```bash
python -m src.landmarks
```
✓ Should see 5 points on face (eyes, nose, mouth corners)

### Test 3: Face Alignment
```bash
python -m src.align
```
✓ Should see aligned 112×112 upright face on right side
- Press **s** to save sample

### Test 4: Embedding Extraction
```bash
python -m src.embed
```
✓ Should print:
```
embedding dim: 512
norm(before L2): ~20.0
cos(prev,this): ~0.99
```

If these tests pass ✓, core infrastructure is working.

---

## Part 3: Face Enrollment

### Single Person Enrollment

```bash
python -m src.enroll
```

**Interactive Steps:**
1. Enter name (e.g., "Alice")
2. Position face in camera
3. Capture samples:
   - Press **SPACE** to capture manually
   - Or press **a** to auto-capture
4. Press **s** to save enrollment

**Best Practices:**
- 20-30 samples per person
- Vary lighting and head angle
- Show different expressions
- Clear, upright faces

**Output:**
```
✓ Database saved to data/db/face_db.npz
✓ Crops saved to data/enroll/Alice/
```

### Multiple Person Enrollment

Repeat enrollment process for each person:
```bash
python -m src.enroll  # Person 1: Alice
python -m src.enroll  # Person 2: Bob
python -m src.enroll  # Person 3: Charlie
```

**Verify Enrollment:**
```bash
ls -la data/enroll/
cat data/db/face_db.json
```

---

## Part 4: Threshold Evaluation (Optional)

Determines optimal recognition threshold.

```bash
python -m src.evaluate
```

**Expected Output:**
```
Genuine (same person):  n=50 mean=0.345 std=0.087
Impostor (diff persons): n=800 mean=0.812 std=0.089
Suggested threshold: 0.34
```

**Save the suggested threshold** for later use.

---

## Part 5: Live Recognition (Baseline)

Test standard recognition before face locking.

```bash
python -m src.recognize
```

**Expected:**
- Detected faces labeled with name or "Unknown"
- Green label = recognized, Red label = unknown
- Press **+/-** to adjust threshold
- Press **q** to quit

---

## Part 6: Face Locking

The main feature!

```bash
python -m src.face_lock
```

**Interactive Steps:**
1. System lists enrolled faces
2. Enter target face name
3. System searches
4. When found → LOCKED
5. Actions detected in real-time
6. History logged to `data/face_histories/`

**Check History:**
```bash
ls -lh data/face_histories/
cat data/face_histories/alice_history_*.txt
```

---

## Directory Structure After Setup

```
Face-Locking/
├── .venv/                          # Virtual environment
├── src/
│   ├── camera.py
│   ├── detect.py
│   ├── landmarks.py
│   ├── align.py
│   ├── embed.py
│   ├── enroll.py
│   ├── evaluate.py
│   ├── recognize.py
│   ├── haar_5pt.py
│   ├── face_lock.py                # ⭐ Main locking module
│   ├── action_detector.py          # ⭐ Action detection
│   └── face_history_logger.py      # ⭐ History logging
├── data/
│   ├── enroll/
│   │   ├── Alice/                  # ✓ Created during enrollment
│   │   ├── Bob/
│   │   └── Charlie/
│   ├── db/
│   │   ├── face_db.npz             # ✓ Created during enrollment
│   │   └── face_db.json
│   └── face_histories/             # ✓ Auto-created by face_lock.py
│       ├── alice_history_*.txt
│       └── bob_history_*.txt
├── models/
│   └── embedder_arcface.onnx       # ✓ Downloaded & placed
├── requirements.txt
├── README.md
├── FACE_LOCKING_GUIDE.md
└── DEPLOYMENT.md                   # This file
```

---

## Troubleshooting Deployment

### Issue: "ModuleNotFoundError: No module named 'mediapipe'"

**Solution:**
```bash
pip uninstall -y mediapipe
pip install mediapipe==0.10.32
```

### Issue: "ONNX Runtime not installed"

**Solution:**
```bash
pip install --upgrade onnxruntime
```

### Issue: "Model file not found"

**Solution:**
```bash
ls -la models/
# Should show embedder_arcface.onnx (~345MB)
# If missing, re-download (see Part 1, Step 5)
```

### Issue: "Camera permission denied"

**macOS:**
```bash
# System Settings → Privacy & Security → Camera
# Add Terminal or VS Code to allowed apps
# Restart terminal
```

**Linux:**
```bash
sudo usermod -aG video $USER
# Then logout and login again
```

**Windows:**
- Check Device Manager for camera
- Update drivers if needed
- Try different camera index (change 0 to 1 in code)

### Issue: "Empty database" when running recognize or face_lock

**Solution:**
```bash
python -m src.enroll
# Must enroll at least one person first
```

### Issue: "Actions not detecting in face_lock"

**Solution:**
1. Check landmarks: `python -m src.landmarks`
2. Adjust thresholds in `action_detector.py`
3. Ensure good lighting
4. Move closer to camera

---

## Performance Tuning

### Increase FPS (for streaming applications)

1. **Skip frames:**
```python
# In face_lock.py, add frame skipping
if frame_count % 2 == 0:  # Process every 2 frames
    result = system.process_frame(frame)
```

2. **Lower resolution:**
```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
```

3. **Reduce detection frequency:**
```python
# In haar_5pt.py
faces = self.face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.2,  # Increase from 1.1 (coarser)
    minNeighbors=7,   # Increase from 5 (stricter)
)
```

### Expected Performance
- **Detection**: 50-100ms
- **Embedding**: 100-150ms
- **Action Detection**: 5-10ms
- **Total per frame**: 200-300ms ≈ 3-5 FPS (CPU-only)

---

## Integration with Existing Systems

### Use FaceLockSystem as Library

```python
from pathlib import Path
from src.face_lock import FaceLockSystem

system = FaceLockSystem(
    db_path=Path("data/db/face_db.npz"),
    distance_threshold=0.34,
)

if system.select_target("Alice"):
    result = system.process_frame(frame)
    print(f"State: {result['state']}")
    print(f"Actions: {result['actions']}")
```

### Custom Integration

```python
from src.action_detector import ActionDetector
from src.face_history_logger import FaceHistoryLogger

detector = ActionDetector()
logger = FaceHistoryLogger("CustomSession")

# In main loop:
actions = detector.detect(landmarks_5x2)
logger.log_actions(actions)

# At end:
logger.finalize()
```

---

## Deployment Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] ArcFace model downloaded to `models/embedder_arcface.onnx`
- [ ] Camera test passes (`python -m src.camera`)
- [ ] At least 1 person enrolled (`python -m src.enroll`)
- [ ] Face recognition works (`python -m src.recognize`)
- [ ] Face locking works (`python -m src.face_lock`)
- [ ] History files created in `data/face_histories/`

---

## Next Steps

1. **Try the Examples:**
   - Follow the Quick Start in README.md
   - Run through all 9 modules

2. **Read Documentation:**
   - [README.md](README.md) - Project overview
   - [FACE_LOCKING_GUIDE.md](FACE_LOCKING_GUIDE.md) - Detailed guide

3. **Customize for Your Use Case:**
   - Adjust action thresholds
   - Modify history format
   - Integrate with your application

4. **Optimize Performance:**
   - See Performance Tuning section above
   - Profile bottlenecks
   - Consider GPU acceleration

---

## Support

### Common Issues
1. Check [Troubleshooting](#troubleshooting-deployment) section
2. Run individual module tests
3. Verify camera and model
4. Check file permissions

### Getting Help
- Review FACE_LOCKING_GUIDE.md
- Check code comments in src/
- Run with verbose output (check action_detector.py)

---

**Installation Complete!** 🎉

You're ready to use Face Locking. Start with:
```bash
python -m src.face_lock
```

---

**Last Updated:** January 2025  
**Author:** Gabriel Baziramwabo
