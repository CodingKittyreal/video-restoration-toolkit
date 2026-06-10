# Changelog

## v1.2 — 2026-06-10

### Watermark Remover
- **New:** Browseable output folder selector with Browse button
- **New:** Configurable output filename suffix (previously hardcoded `_nowm`)
- **Fix:** Mask preview dialog crash when closing during detection (TclError: bad window path name)
- **Fix:** Thread-safe destruction guards on all background callbacks

### Frame Extractors
- **Fix:** FFmpeg 8.x compatibility with `-update 1` flag
- **Fix:** Replaced `ffprobe` duration lookup with `-sseof -0.1` for reliable last-frame seeking
- **New:** Detailed FFmpeg stderr logging on failures
- **New:** `CREATE_NO_WINDOW` flag prevents console flickering on Windows

## v1.1 — 2026-06-01

### Watermark Remover
- **New:** Paste List dialog for bulk-loading video filenames
- **New:** Zoom & pan in mask preview (mouse scroll + spacebar)
- **New:** Multi-frame navigation in mask editor
- **New:** ROI-cropped processing architecture for VRAM savings

## v1.0 — 2026-05-15

- Initial release
- ProPainter Watermark Remover with GUI
- Batch Last-Frame Extractor
- Interval Frame Extractor
