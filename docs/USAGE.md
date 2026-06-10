# 📖 Usage Guide

## 🔥 ProPainter Watermark Remover

### Loading Videos

1. **Click "Add Videos"** to browse and select video files, or
2. **Click "Paste List"** to paste a list of filenames from a specific folder
3. Videos appear in the queue with status indicators

### Detecting & Editing Masks

1. Select a video in the queue
2. Click **"Preview Mask"** to open the mask editor
3. The tool auto-detects watermark regions (shown in red)
4. Adjust **Sensitivity** slider and click **Re-detect** if needed
5. **Draw to add** mask regions (left-click + drag)
6. **Erase** to remove mask regions
7. Use **mouse scroll** to zoom, **spacebar + drag** to pan
8. Navigate frames with the **◀ ▶** buttons
9. Click **"Accept Mask"** when satisfied

### Processing

1. Configure settings in the top panel:
   - **Sensitivity** — Watermark detection sensitivity (higher = more aggressive)
   - **ROI Padding** — Extra pixels around detected watermark (default: 20px)
   - **Output Folder** — Click "Browse" to change
   - **Suffix** — Added to output filenames (leave blank for no suffix, or type `_clean` etc.)
2. Click **"Process All"** to start batch processing
3. Progress is shown per-video and in the log panel
4. Click **"Open Output"** to view results

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Sensitivity | 1.5x | How aggressively watermarks are detected |
| ROI Padding | 20px | Extra margin around the detected watermark region |
| Output Folder | Configurable | Where processed videos are saved |
| Suffix | *(empty)* | Text appended to output filenames |

---

## 📸 Batch Last-Frame Extractor

1. Launch: double-click `run_batch.bat`
2. **Input Folder** — Select the folder containing your videos
3. **Output Folder** — Where PNG/JPG stills will be saved
4. **Format** — PNG (lossless) or JPG (smaller files)
5. Click **Start**
6. Each video's last frame is extracted and saved with the same filename

> 💡 **Resume-safe:** If you stop and restart, existing files are automatically skipped.

---

## 🎞️ Interval Frame Extractor

1. Launch: double-click `run_interval.bat`
2. **Input Video** — Select a single video file
3. **Output Folder** — Auto-created as `{video_name}_frames/`
4. **Extract every N frame(s)** — Set the interval (1 = every frame, 2 = every other, etc.)
5. **Format** — PNG or JPG
6. **JPG Quality** — 50–100 (only applies to JPG)
7. Click **Start**
8. Supports **Pause** and **Stop** during extraction
