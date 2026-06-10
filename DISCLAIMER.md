# ⚠️ Disclaimer

## General

This toolkit is provided **"as-is"** without any warranty, express or implied. The author makes no guarantees regarding the accuracy, reliability, or suitability of the output for any particular purpose.

## AI-Generated Output

The watermark removal tool uses **AI-based video inpainting** (ProPainter). AI processing may:

- Introduce visual artifacts, distortions, or color shifts
- Produce inconsistent results across different video types
- Fail on certain video formats, resolutions, or codecs
- Require significant GPU memory (VRAM) and processing time

**No guarantee is made regarding output quality.** Always review processed videos before publishing.

## Copyright & Legal Responsibility

- **You are solely responsible** for ensuring you have the legal right to process, modify, and distribute any video content.
- Removing watermarks from copyrighted content without authorization may violate copyright laws in your jurisdiction.
- This tool is intended for use on **your own content** or content you have explicit permission to modify.
- The author assumes **no liability** for misuse of this tool.

## Hardware Requirements

- A **CUDA-compatible NVIDIA GPU** is required for the watermark remover
- Processing times vary significantly based on GPU performance, video length, and resolution
- Insufficient VRAM may cause crashes or out-of-memory errors

## Third-Party Dependencies

This toolkit depends on external open-source projects:

- **[ProPainter](https://github.com/sczhou/ProPainter)** — Video inpainting model (cloned during setup)
- **[FFmpeg](https://ffmpeg.org)** — Video/image processing (must be installed separately)
- **[PyTorch](https://pytorch.org)** — Deep learning framework (installed during setup)

The author is not responsible for changes, bugs, or license modifications in third-party dependencies.

## Data Privacy

- All processing is performed **locally on your machine**
- No video data is uploaded to any server
- No telemetry, analytics, or tracking is included in this toolkit
