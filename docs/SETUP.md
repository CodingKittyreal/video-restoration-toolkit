# 📦 Setup Guide

## Prerequisites

Before you begin, make sure you have:

| Requirement | How to Check | Install Link |
|------------|-------------|-------------|
| **Python 3.12+** | `python --version` | [python.org](https://python.org/downloads/) |
| **Git** | `git --version` | [git-scm.com](https://git-scm.com/) |
| **FFmpeg** | `ffmpeg -version` | [ffmpeg.org](https://ffmpeg.org/download.html) |
| **NVIDIA GPU Driver** | Device Manager → Display | [nvidia.com/drivers](https://nvidia.com/drivers) |

> ⚠️ **FFmpeg must be in your system PATH.** After installing, open a new terminal and type `ffmpeg` to verify.

---

## 🎞️ Frame Extractor (Free Tools)

These require only Python — no GPU or special setup needed.

```bash
# 1. Clone the repo
git clone https://github.com/nftmoondogs/video-restoration-toolkit.git
cd video-restoration-toolkit/frame-extractor

# 2. Run the batch last-frame extractor
python batch_last_frame.py

# 3. Or run the interval extractor
python interval_extractor.py
```

Alternatively, double-click `run_batch.bat` or `run_interval.bat`.

---

## 🔥 Watermark Remover (Sponsors Only)

### Step 1: Clone the Repository

```bash
git clone https://github.com/nftmoondogs/video-restoration-toolkit.git
cd video-restoration-toolkit/watermark-remover
```

### Step 2: Run Setup

Double-click `setup.bat` or run it from the terminal:

```bash
setup.bat
```

This will automatically:
1. ✅ Create a Python 3.12 virtual environment (`.venv/`)
2. ✅ Install PyTorch with CUDA 12.8 support
3. ✅ Install all Python dependencies
4. ✅ Clone the ProPainter repository

> ⏱️ First-time setup takes ~5–10 minutes depending on internet speed.

### Step 3: Verify Installation

```bash
.venv\Scripts\python.exe verify.py
```

You should see:
```
Python: 3.12.x
PyTorch: 2.8.x
CUDA available: True
GPU: NVIDIA GeForce RTX XXXX
...
✅ All checks passed!
```

### Step 4: Launch

Double-click `run.bat` or:

```bash
.venv\Scripts\python.exe app.py
```

---

## 🔄 Updating

```bash
cd video-restoration-toolkit
git pull origin main
```

---

## ❓ Need Help?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues, or [open an issue](https://github.com/nftmoondogs/video-restoration-toolkit/issues).
