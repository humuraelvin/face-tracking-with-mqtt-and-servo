# Face Recognition & Locking with ArcFace ONNX and 5-Point Alignment

A **research-grade, CPU-first face recognition system** with **advanced face locking and behavior tracking**. Implements ArcFace embeddings with 5-point facial landmark alignment, real-time action detection, and persistent behavior logging.

Built for clarity, stability, and practical deployment on laptops without GPU acceleration.

**Based on:** *Face Recognition with ArcFace ONNX and 5-Point Alignment* by Gabriel Baziramwabo (Rwanda Coding Academy)

**Extended with:** Face Locking, Action Detection, and Behavior History Tracking

---

## 📋 Table of Contents

1. [Features](#features)
2. [What's New: Face Locking](#whats-new-face-locking)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Project Structure](#project-structure)
6. [Quick Start](#quick-start)
7. [Detailed Usage Guide](#detailed-usage-guide)
8. [Face Locking Guide](#face-locking-guide)
9. [Pipeline Architecture](#pipeline-architecture)
10. [Troubleshooting](#troubleshooting)

---

## ✨ Features

### Face Recognition Core
- ✅ **CPU-Only Inference**: Runs efficiently on laptops without GPU
- ✅ **5-Point Alignment**: Haar cascade detection + MediaPipe landmark extraction
- ✅ **ArcFace ONNX Model**: 512-dimensional L2-normalized embeddings
- ✅ **Modular Design**: Each stage testable independently
- ✅ **Real-Time Recognition**: Multi-face detection with threshold-based matching
- ✅ **Threshold Evaluation**: Data-driven FAR/FRR analysis
- ✅ **Open-Set Recognition**: Rejects unknown faces automatically
- ✅ **Database Persistence**: JSON metadata + NPZ embeddings

### Face Locking (NEW)
- ✅ **Identity-Specific Tracking**: Lock onto a single enrolled identity
- ✅ **Stable Tracking**: Follow face across frames with timeout protection
- ✅ **Action Detection**: Real-time blink, movement, and expression detection
- ✅ **Behavior History**: Persistent logging of all detected actions to timestamped files
- ✅ **State Machine**: SEARCHING → LOCKED → LOST with automatic recovery
- ✅ **Configurable Sensitivity**: Adjust detection thresholds per use case

---

## 🔒 What's New: Face Locking

Face Locking is a major extension that transforms the system from **recognition** to **tracking & behavior analysis**.

### Core Capability
When an enrolled identity appears, the system:
1. **Recognizes who they are**
2. **Locks onto their face**
3. **Tracks movements** in real-time
4. **Detects actions** (blinks, head movement, smiles)
5. **Records everything** to a timestamped history file

### Use Cases
- **Security**: Track suspects/intruders with action timeline
- **HCI Research**: Monitor user attention and engagement
- **Interview Analysis**: Record behavioral cues
- **Accessibility**: Head tracking for disabled users
- **Entertainment**: Real-time reaction detection

### Detected Actions
- **Eye Blinks**: Rapid eye closure/opening
- **Head Movement**: Left/right motion tracking
- **Smiles/Laughs**: Mouth height increase
- **Face Distance**: Moving closer/farther from camera

### Output Example
```
[00:00:05.234] BLINK       | Eye blink detected | conf=0.85 | val=0.45
[00:00:06.567] MOVE_RIGHT  | Head movement right (12.5px) | conf=0.92 | val=12.5
[00:00:07.890] SMILE       | Smile detected (ratio: 1.15) | conf=0.88 | val=1.15
```

**👉 See [FACE_LOCKING_GUIDE.md](FACE_LOCKING_GUIDE.md) for detailed documentation**

---

## 🖥️ System Requirements

- **Python**: 3.9+ (tested on Python 3.11)
- **OS**: macOS, Linux, or Windows
- **Webcam**: Required for camera input
- **RAM**: 2GB+ recommended
- **Storage**: ~500MB for ONNX model + dependencies

### Python Version Check

```bash
python3 --version  # Should show Python 3.9+
```

---

## 📦 Installation

### Step 1: Clone Repository

```bash
cd /path/to/your/workspace
git clone https://github.com/humuraelvin/Face-Recog-onnx.git
cd Face-Recog-onnx
```

### Step 2: Create Virtual Environment

```bash
python3.11 -m venv .venv
```

### Step 3: Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate
```

### Step 4: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 5: Install Dependencies

Using `requirements.txt`:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install opencv-python numpy onnxruntime scipy tqdm mediapipe protobuf
```

### Step 6: Download ArcFace ONNX Model

```bash
# From project root directory
curl -L -o buffalo_l.zip "https://sourceforge.net/projects/insightface.mirror/files/v0.7/buffalo_l.zip/download"

unzip -o buffalo_l.zip

cp w600k_r50.onnx models/embedder_arcface.onnx

# Cleanup
rm -f buffalo_l.zip w600k_r50.onnx 1k3d68.onnx 2d106det.onnx det_10g.onnx genderage.onnx
```

✅ **Installation complete!**

---

## 📁 Project Structure

```
Face-Locking/
├── src/
│   ├── camera.py                # Camera capture validation
│   ├── detect.py                # Haar face detection testing
│   ├── landmarks.py             # MediaPipe 5-point landmark extraction
│   ├── align.py                 # Face alignment to 112×112
│   ├── embed.py                 # ArcFace ONNX embedding extraction
│   ├── enroll.py                # Enrollment tool (build database)
│   ├── evaluate.py              # Threshold evaluation (FAR/FRR analysis)
│   ├── recognize.py             # Real-time recognition pipeline
│   ├── haar_5pt.py              # Reusable Haar + 5pt detector class
│   ├── face_lock.py             # ⭐ Main face locking system
│   ├── action_detector.py       # ⭐ Action detection (blink, smile, movement)
│   └── face_history_logger.py   # ⭐ Behavior history logging
├── data/
│   ├── enroll/                  # Aligned 112×112 enrollment crops (per person)
│   │   ├── Person1/
│   │   ├── Person2/
│   │   └── ...
│   ├── db/                      # Recognition database
│   │   ├── face_db.npz          # Embeddings (name → vector)
│   │   └── face_db.json         # Metadata
│   └── face_histories/          # ⭐ Action history logs (auto-created)
│       ├── person1_history_*.txt
│       ├── person2_history_*.txt
│       └── ...
├── models/
│   └── embedder_arcface.onnx    # ArcFace model (w600k_r50)
├── book/                        # Reference materials
├── FACE_LOCKING_GUIDE.md        # ⭐ Comprehensive face locking documentation
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── init_project.py              # Project initialization script
```

**⭐ = New files for Face Locking feature**

---

## 🚀 Quick Start (5 Minutes)

### Test Each Module

```bash
# 1. Verify camera access
python -m src.camera

# 2. Test face detection
python -m src.detect

# 3. Test 5-point landmarks
python -m src.landmarks

# 4. Test face alignment
python -m src.align

# 5. Test embedding extraction (requires model)
python -m src.embed
```

### Enroll & Recognize

```bash
# 6. Enroll people (run multiple times for different people)
python -m src.enroll

# 7. Evaluate threshold
python -m src.evaluate

# 8. Start live recognition
python -m src.recognize
```

### 🔒 Face Locking (NEW)

```bash
# 9. Start face locking with action detection
python -m src.face_lock

# When prompted:
# 1. Select an enrolled face (e.g., "Gabi")
# 2. System searches for that face
# 3. When found → lock acquired
# 4. Watch as actions are detected and logged
# 5. Press 'r' to release, 'q' to quit
# 6. History automatically saved to data/face_histories/
```

**Check History:**
```bash
ls -lh data/face_histories/
cat data/face_histories/gabi_history_*.txt
```

---

## 📖 Detailed Usage Guide

### 1️⃣ Camera Validation

**Purpose:** Verify webcam access and framerate

```bash
python -m src.camera
```

**Expected Output:**
- Live camera window opens
- Smooth motion visible
- FPS counter displayed
- Press **q** to exit

**Troubleshooting:**
- If camera doesn't open, try changing camera index in code (0→1 or 0→2)
- Check camera permissions (macOS: System Settings → Privacy & Security → Camera)

---

### 2️⃣ Face Detection

**Purpose:** Validate Haar cascade face detection

```bash
python -m src.detect
```

**Expected Output:**
- Face appears in bounding box (green rectangle)
- Box follows face movement
- Press **q** to exit

---### 3️⃣ 5-Point Landmarks

**Purpose:** Verify facial landmark extraction

```bash
python -m src.landmarks
```

**Expected Output:**
- Green bounding box around face
- 5 green points: left eye, right eye, nose, left mouth, right mouth
- Press **q** to exit

---

### 4️⃣ Face Alignment

**Purpose:** Test 112×112 alignment warping

```bash
python -m src.align
```

**Expected Output:**
- Left window: Original face with landmarks
- Right window: Aligned 112×112 upright face
- Press **q** to quit
- Press **s** to save aligned image for debugging

**What's Happening:**
- Similarity transform (rotation + scale + translation) applied
- Face rotated to canonical pose
- Output always 112×112 pixels

---

### 5️⃣ Embedding Extraction

**Purpose:** Validate ArcFace ONNX model and embedding generation

```bash
python -m src.embed
```

**Expected Output:**
```
embedding dim: 512
norm(before L2): 21.85
cos(prev,this): 0.988
```

**Meaning:**
- `embedding dim: 512` → ResNet-50 output size
- `norm(before L2): 21.85` → Raw vector magnitude
- `cos(prev,this): 0.988` → Cosine similarity between consecutive frames (should be ~0.99)

**Controls:**
- Press **q** to quit
- Press **p** to print embedding statistics

---

### 6️⃣ Enrollment

**Purpose:** Build face recognition database

```bash
python -m src.enroll
```

**Workflow:**
1. Enter person's name (e.g., "Alice", "Bob")
2. Position face in camera
3. Capture samples using controls below
4. Press **s** to save and finalize enrollment

**Controls:**
- **SPACE** → Capture one sample manually
- **a** → Toggle auto-capture (every 0.25 seconds)
- **s** → Save enrollment (after ≥15 samples recommended)
- **r** → Reset new samples (keeps existing crops)
- **q** → Quit without saving

**Best Practices:**
- Use consistent lighting
- Vary head angle slightly (left/right/up/down)
- Show different expressions (neutral, smile, serious)
- Capture at least 15 samples per person
- Enroll at least 10 different people for meaningful evaluation

**Output:**
- Aligned 112×112 crops saved to `data/enroll/<name>/`
- Mean embedding saved to `data/db/face_db.npz`
- Metadata saved to `data/db/face_db.json`

---

### 7️⃣ Threshold Evaluation

**Purpose:** Find optimal recognition threshold using data-driven analysis

```bash
python -m src.evaluate
```

**Expected Output:**
```
=== Distance Distributions (cosine distance = 1 - cosine similarity) ===
Genuine (same person):  n=50 mean=0.345 std=0.087 p05=0.210 p50=0.328 p95=0.502
Impostor (diff persons): n=800 mean=0.812 std=0.089 p05=0.641 p50=0.821 p95=0.951

=== Threshold Sweep ===
thr=0.10 FAR=  0.00%  FRR= 98.00%
thr=0.35 FAR=  1.25%  FRR=  8.00%
thr=0.60 FAR= 12.50%  FRR=  2.00%

Suggested threshold (target FAR 1.0%): thr=0.34 FAR=1.00% FRR=10.00%

(Equivalent cosine similarity threshold ~ 0.66, since sim = 1 - dist)
```

**Interpretation:**
- **Genuine distances** = same person pairs (should be small)
- **Impostor distances** = different person pairs (should be large)
- **FAR** (False Accept Rate) = wrongly accepting impostor as genuine
- **FRR** (False Reject Rate) = wrongly rejecting genuine face
- **Suggested threshold** = balances FAR/FRR

**Note:** Use the suggested threshold in `recognize.py` (see code: `dist_thresh=0.34`)

---

### 8️⃣ Live Recognition

**Purpose:** Real-time face recognition with live camera input

```bash
python -m src.recognize
```

**Expected Output:**
- Live camera feed with detected faces
- Each face labeled with name or "Unknown"
- Confidence score and similarity displayed
- FPS counter in top-left

**Controls:**
- **q** → Quit
- **r** → Reload database from disk
- **+** → Loosen threshold (more accepts, more false positives)
- **-** → Tighten threshold (fewer accepts, fewer false positives)
- **d** → Toggle debug overlay

**Behavior:**
- Green box + green label = recognized (accepted)
- Green box + red label = unknown (rejected)
- Confidence bar shows similarity score
- Temporal smoothing prevents flickering

---

### 9️⃣ Face Locking & Action Detection (NEW)

**Purpose:** Lock onto an enrolled identity and track behavior in real-time

```bash
python -m src.face_lock
```

**Workflow:**
1. System shows available enrolled faces
2. You select target identity (e.g., "Gabi")
3. System enters **SEARCHING** state
4. When target appears with high confidence → **LOCKED**
5. While locked, system detects and logs actions:
   - Eye blinks
   - Head movement (left/right)
   - Smiles/laughs
   - Face distance changes (closer/farther)
6. Actions logged to timestamped history file in `data/face_histories/`
7. If face disappears briefly, lock held in **LOST** state
8. Lock released if face absent too long, or press **r**

**Controls:**
- **r** → Release lock manually
- **q** → Quit and save history

**Example Output:**
```
Lock: LOCKED | Target: Gabi
Conf: 0.92 | Time: 15.3s
Actions: blink | move_right | smile
```

**History File Example:**
```
[00:00:05.234] BLINK       | Eye blink detected | conf=0.85 | val=0.45
[00:00:06.567] MOVE_RIGHT  | Head movement right (12.5px) | conf=0.92 | val=12.5
[00:00:07.890] SMILE       | Smile detected (ratio: 1.15) | conf=0.88 | val=1.15
```

**Check History:**
```bash
# List all history files
ls -lh data/face_histories/

# View latest session
cat data/face_histories/gabi_history_*.txt
```

**👉 For detailed Face Locking documentation, see [FACE_LOCKING_GUIDE.md](FACE_LOCKING_GUIDE.md)**

---

## 🏗️ Pipeline Architecture

### Enrollment Pipeline

```
Camera Frame
    ↓
Haar Face Detection
    ↓
MediaPipe 5-Point Landmarks
    ↓
Face Alignment (112×112)
    ↓
ArcFace ONNX Embedding (512-dim)
    ↓
L2 Normalization
    ↓
Mean Pooling (multiple samples)
    ↓
Database Storage (face_db.npz)
```

### Recognition Pipeline

```
Camera Frame
    ↓
Haar Face Detection
    ↓
MediaPipe 5-Point Landmarks
    ↓
Face Alignment (112×112)
    ↓
ArcFace ONNX Embedding (512-dim)
    ↓
L2 Normalization
    ↓
Cosine Distance to DB Templates
    ↓
Threshold Decision
    ↓
Accept/Reject + Display Label
```

### Face Locking Pipeline (NEW)

```
Camera Frame
    ↓
Detection & Recognition (as above)
    ↓
State Machine (SEARCHING → LOCKED → LOST)
    ↓
Action Detection (blink, movement, smile)
    ↓
History Logging
    ↓
Persistent File Storage
```

### Key Concepts

**5-Point Alignment:**
- Extracts: left eye, right eye, nose tip, left mouth, right mouth
- Applies similarity transform (rotation + scale + translation)
- Ensures consistent input to embedding model
- Reduces intra-class variance, improves recognition

**L2 Normalization:**
- Embedding vector divided by its L2 norm
- Results in unit vector (length = 1.0)
- Enables cosine similarity = dot product

**Cosine Distance:**
- Distance = 1 - cosine_similarity
- Range: 0 (identical) to 2 (opposite)
- Threshold ~0.34 means similarity ~0.66

---

## 🐛 Troubleshooting

### Issue: Camera doesn't open

**Solution:**
```bash
# Try different camera index
python -m src.camera  # Try 0, 1, 2
```

**macOS Fix:**
- System Settings → Privacy & Security → Camera
- Add Terminal or VS Code to allowed apps
- Restart terminal

**Linux Fix:**
```bash
# Check camera permissions
ls -la /dev/video0
# Grant permissions if needed
sudo usermod -aG video $USER
```

---

### Issue: "No module named mediapipe"

**Solution:**
```bash
pip uninstall -y mediapipe
pip install mediapipe==0.10.32
```

---

### Issue: "Model not found: embedder_arcface.onnx"

**Solution:**
```bash
# Re-download and extract model
curl -L -o buffalo_l.zip "https://sourceforge.net/projects/insightface.mirror/files/v0.7/buffalo_l.zip/download"
unzip -o buffalo_l.zip
cp w600k_r50.onnx models/embedder_arcface.onnx
rm -f buffalo_l.zip w600k_r50.onnx 1k3d68.onnx 2d106det.onnx det_10g.onnx genderage.onnx
```

---

### Issue: Recognition accuracy is poor

**Solutions:**
1. Enroll more samples (target: 20-30 per person)
2. Vary lighting conditions during enrollment
3. Re-evaluate threshold with more data
4. Check alignment visually (`python -m src.align`)
5. Verify model is real ArcFace (check embedding norm values in `embed.py`)

---

### Issue: "Embedding norm is 1.0 but values seem wrong"

**Check:**
```bash
python -m src.embed
# Press 'p' to print embedding details
# Values should be between -1 and +1
# Norm should be ~1.0
```

---

## 📊 Database Format

### `face_db.npz`
- NumPy archive storing name → embedding pairs
- Each embedding is 512-dimensional, L2-normalized float32
- Load with: `np.load('data/db/face_db.npz', allow_pickle=True)`

### `face_db.json`
- Metadata file with enrollment info
- Contains: timestamp, embedding dimension, enrolled names, sample counts

---

## 🔧 Configuration

To adjust recognition parameters, edit `src/recognize.py`:

```python
matcher = FaceDBMatcher(
    db=db, 
    dist_thresh=0.34  # ← Change this threshold
)
```

Lower threshold = more strict (fewer false accepts, more false rejects)
Higher threshold = more lenient (more false accepts, fewer false rejects)

---

## 📝 Notes

- **All embeddings are L2-normalized** (norm = 1.0)
- **Similarity matching uses cosine distance** (dot product of normalized vectors)
- **CPU-only design** ensures reproducibility and accessibility
- **Modular architecture** allows replacing any stage independently
- **No GPU required** for deployment

---

## 📚 References

1. Deng et al. (2019). ArcFace: Additive Angular Margin Loss for Deep Face Recognition. CVPR 2019.
2. InsightFace Project. https://github.com/deepinsight/insightface
3. MediaPipe. https://mediapipe.dev/
4. ONNX Runtime. https://onnxruntime.ai/

---

## 📄 License

Educational use. Based on Gabriel Baziramwabo's Face Recognition course.

---

## ❓ FAQ

**Q: Can I use this for production?**
A: Yes, with proper consent and legal framework. CPU performance is ~10-20 FPS.

**Q: How many faces can I enroll?**
A: Theoretically unlimited; practically tested up to 100+ identities.

**Q: Can I add GPU acceleration?**
A: Yes, change ONNX Runtime provider from `CPUExecutionProvider` to `CUDAExecutionProvider`.

**Q: What's the recognition accuracy?**
A: ~95%+ verification accuracy at 1% FAR with well-enrolled database. Depends on enrollment quality and threshold tuning.

**Q: Can I use this on mobile?**
A: ONNX Runtime supports mobile; would require porting to appropriate framework (TFLite, Core ML, etc.).

---

**Ready to build your face recognition system?** Start with Step 1 in the [Installation](#installation) section! 🚀
