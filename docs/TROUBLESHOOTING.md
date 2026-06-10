# 🔧 Troubleshooting

## Common Issues

### ❌ "CUDA not available" / "No CUDA GPU detected"

**Symptoms:** Watermark remover shows warning, processing is extremely slow.

**Fix:**
1. Make sure you have an **NVIDIA GPU** (AMD/Intel not supported)
2. Install the latest **NVIDIA drivers**: [nvidia.com/drivers](https://nvidia.com/drivers)
3. Re-run `setup.bat` — it installs PyTorch with CUDA 12.8
4. Verify: `.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"`

---

### ❌ "ProPainter not found"

**Symptoms:** App starts but warns about missing ProPainter.

**Fix:**
```bash
cd watermark-remover
git clone https://github.com/sczhou/ProPainter.git ProPainter
```

---

### ❌ FFmpeg "not found" or frame extraction fails

**Symptoms:** Batch extractor can't find FFmpeg, or extraction produces no output.

**Fix:**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to a folder (e.g., `C:\ffmpeg\`)
3. Add `C:\ffmpeg\bin\` to your system PATH
4. Open a **new** terminal and type `ffmpeg -version` to verify

---

### ❌ Mask preview crash / "bad window path name"

**Symptoms:** App crashes with `TclError` when opening or closing the mask editor.

**Fix:** This was fixed in **v1.2**. Make sure you have the latest version:
```bash
cd video-restoration-toolkit
git pull origin main
```

---

### ❌ Out of Memory (VRAM)

**Symptoms:** Processing fails with CUDA out-of-memory error.

**Fix:**
- Close other GPU-intensive applications
- Reduce video resolution before processing
- The ROI-cropped architecture already minimizes VRAM usage — if you still run out, your GPU may not have enough VRAM (minimum 6GB recommended)

---

### ❌ "Python was not found" on Windows

**Symptoms:** `.bat` files fail with Python not found.

**Fix:**
1. Install Python 3.12 from [python.org](https://python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Open a new terminal and verify: `python --version`

---

### ❌ Videos load but no watermark detected

**Symptoms:** Detection finds 0 pixels.

**Fix:**
- Increase the **Sensitivity** slider (try 2.0x–3.0x)
- Some watermarks are too transparent for auto-detection — use **manual drawing** instead
- Click "Re-detect" after adjusting sensitivity

---

## Still Stuck?

[Open an issue](https://github.com/CodingKittyreal/video-restoration-toolkit/issues) with:
1. Your OS version
2. Python version (`python --version`)
3. GPU model
4. Full error traceback
