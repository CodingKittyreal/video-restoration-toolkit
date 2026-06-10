# 🎬 Video Restoration Toolkit

**AI-powered tools for video upscaling workflows — watermark removal, frame extraction, and batch automation.**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![CUDA](https://img.shields.io/badge/CUDA-12.x-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-Sponsors_Only-FF6B6B)](#-license)
[![Patreon](https://img.shields.io/badge/Patreon-F96854?logo=patreon&logoColor=white)](https://www.patreon.com/posts/ai-restoration-15921195722)

*Built for content creators who restore and upscale classic sports footage, vintage clips, and retro media to 4K.*

---

## ⚡ Choose Your Subscription Tier

Select a tier below to get instant access to the source code, installers, and automation tools:

<table>
  <tr>
    <td align="center" valign="top" width="33%">
      <h3>🌱 Free Tools</h3>
      <p><b>$0 / month</b></p>
      <hr>
      <p align="left">
        ✅ <b>Batch Last-Frame Extractor</b><br>
        ✅ <b>Interval Frame Extractor</b><br>
        ✅ Step-by-step setup guides<br>
        ✅ Standard community updates
      </p>
      <br>
      <a href="https://github.com/CodingKittyreal/video-restoration-toolkit/archive/refs/heads/master.zip">
        <img src="https://img.shields.io/badge/Get_Started-Free-green?style=for-the-badge&logo=github" alt="Download Free" />
      </a>
    </td>
    <td align="center" valign="top" width="33%">
      <h3>🔥 Full Toolkit</h3>
      <p><b>$29 / month</b></p>
      <hr>
      <p align="left">
        ✅ <b>ProPainter Watermark Remover</b><br>
        ✅ Interactive Mask Editor (Zoom/Pan)<br>
        ✅ Auto-detection with adjustable sensitivity<br>
        ✅ ROI-cropped acceleration (VRAM-safe)<br>
        ✅ Batch video processing queue<br>
        ✅ All future tool updates
      </p>
      <br>
      <a href="https://www.patreon.com/posts/ai-restoration-15921195722">
        <img src="https://img.shields.io/badge/Subscribe-Patreon-orange?style=for-the-badge&logo=patreon" alt="Subscribe Patreon" />
      </a>
    </td>
    <td align="center" valign="top" width="33%">
      <h3>💎 Creator Pro</h3>
      <p><b>$49 / month</b></p>
      <hr>
      <p align="left">
        ✅ <b>Everything in Full Toolkit</b><br>
        ✅ <b>Premiere Pro Batch Exporter (AHK)</b><br>
        ✅ 1 custom feature request / month<br>
        ✅ Direct prioritize support<br>
        ✅ Early access to experimental builds
      </p>
      <br>
      <a href="https://www.patreon.com/posts/ai-restoration-15921195722">
        <img src="https://img.shields.io/badge/Subscribe-Patreon-orange?style=for-the-badge&logo=patreon" alt="Subscribe Patreon" />
      </a>
    </td>
  </tr>
</table>

---

## 🛠️ What's Inside

### 🔥 ProPainter Watermark Remover `sponsors only`

GPU-accelerated batch watermark removal powered by [ProPainter](https://github.com/sczhou/ProPainter). Features an interactive mask editor with zoom/pan, automatic watermark detection, ROI-cropped processing for massive VRAM savings, and a beautiful dark-themed GUI.

- ✅ Batch video processing queue
- ✅ Auto-detect watermarks with adjustable sensitivity
- ✅ Manual mask drawing with brush add/erase
- ✅ Multi-frame preview with zoom & pan
- ✅ ROI-cropped architecture (processes only the watermark region)
- ✅ Custom output folder & filename suffix
- ✅ Paste-list import for bulk loading

### 📸 Batch Last-Frame Extractor `free`

Extract the final frame of every video in a folder as PNG/JPG. Perfect for creating thumbnail sheets or "before/after" stills for upscaling workflows.

- ✅ Batch folder processing
- ✅ Skip existing files (resume-safe)
- ✅ FFmpeg 8.x compatible (`-sseof` + `-update 1`)
- ✅ Dark-themed GUI with progress tracking

### 🎞️ Interval Frame Extractor `free`

Extract every Nth frame from a single video. Ideal for creating training datasets, timelapse stills, or quality-check frames.

- ✅ Configurable interval (every 1–30 frames)
- ✅ PNG or JPG output with quality control
- ✅ Pause/resume support
- ✅ Unicode filename safe

---

## ⚡ Quick Start

### Frame Extractors (Free)

No setup needed — just Python 3.12+ and FFmpeg in PATH

```bash
cd frame-extractor
python batch_last_frame.py
```

### Watermark Remover (Sponsors)

```bash
cd watermark-remover
setup.bat          # One-time: creates venv, installs PyTorch + CUDA, clones ProPainter
run.bat            # Launch the GUI
```

> 📖 **Full setup guide:** [docs/SETUP.md](docs/SETUP.md)

> 📖 **Usage instructions:** [docs/USAGE.md](docs/USAGE.md)

> 📖 **Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 💻 Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 | Windows 11 |
| **Python** | 3.12 | 3.12 |
| **GPU** | NVIDIA GTX 1060 (6GB) | RTX 3060+ (8GB+) |
| **CUDA** | 12.1 | 12.8 |
| **FFmpeg** | 6.x | 8.x |
| **RAM** | 8GB | 16GB+ |

---

## 📂 Project Structure

```
video-restoration-toolkit/
├── watermark-remover/       # ProPainter-based watermark removal (sponsors)
│   ├── app.py               # Main GUI application
│   ├── watermark_detector.py
│   ├── propainter_runner.py
│   ├── verify.py            # System check script
│   ├── setup.bat            # One-click setup
│   └── run.bat              # One-click launch
│
├── frame-extractor/         # Frame extraction tools (free)
│   ├── batch_last_frame.py  # Last frame of every video in folder
│   ├── interval_extractor.py # Every Nth frame from a video
│   ├── run_batch.bat
│   └── run_interval.bat
│
└── docs/                    # Documentation
    ├── SETUP.md
    ├── USAGE.md
    └── TROUBLESHOOTING.md
```

---

## ⚠️ Disclaimer

This toolkit is provided **"as-is"** for personal and educational use. See [DISCLAIMER.md](DISCLAIMER.md) for full terms. The user is solely responsible for ensuring they have the right to process any video content.

---

## 📜 License

This repository uses a **custom sponsor-only license**. See [LICENSE.md](LICENSE.md).

- Free tools (frame extractors) are available to everyone
- Watermark remover and automation tools require an active sponsorship
- No redistribution, resale, or sublicensing permitted

---

**Built with ❤️ for the content restoration community**

[⭐ Star this repo](../../stargazers) · [🐛 Report a bug](../../issues) · [💡 Request a feature](../../issues)
