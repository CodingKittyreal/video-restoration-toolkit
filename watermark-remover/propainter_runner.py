"""
ProPainter Runner Module
========================
Wraps ProPainter's inference_propainter.py to process videos
with detected watermark masks. Handles temp file management,
subprocess execution, progress tracking, and audio merging.
"""

import os
import sys
import subprocess
import shutil
import tempfile
import time
import json
import re
from pathlib import Path
from typing import Optional, Callable

import cv2
import numpy as np


class ProPainterRunner:
    """Runs ProPainter video inpainting to remove watermarks."""

    # Default ProPainter directory (relative to this script)
    DEFAULT_PROPAINTER_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ProPainter"
    )

    def __init__(
        self,
        propainter_dir: Optional[str] = None,
        use_fp16: bool = True,
        subvideo_length: int = 80,
        neighbor_length: int = 10,
        ref_stride: int = 10,
        mask_dilation: int = 8,
        raft_iter: int = 20,
    ):
        """
        Initialize the ProPainter runner.

        Args:
            propainter_dir: Path to cloned ProPainter repository.
            use_fp16: Use half-precision inference (faster, less VRAM).
            subvideo_length: Length of sub-video segments for processing.
            neighbor_length: Number of local neighboring frames.
            ref_stride: Stride for global reference frames.
            mask_dilation: Dilation applied to the mask for flow masking.
            raft_iter: Number of RAFT optical flow iterations.
        """
        self.propainter_dir = propainter_dir or self.DEFAULT_PROPAINTER_DIR
        self.use_fp16 = use_fp16
        self.subvideo_length = subvideo_length
        self.neighbor_length = neighbor_length
        self.ref_stride = ref_stride
        self.mask_dilation = mask_dilation
        self.raft_iter = raft_iter

        # Verify ProPainter directory exists
        self.inference_script = os.path.join(
            self.propainter_dir, "inference_propainter.py"
        )
        if not os.path.exists(self.inference_script):
            raise FileNotFoundError(
                f"ProPainter inference script not found at: {self.inference_script}\n"
                f"Please clone ProPainter: git clone https://github.com/sczhou/ProPainter.git"
            )

    def process_video(
        self,
        video_path: str,
        mask_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_event=None,
    ) -> bool:
        """
        Process a video to remove watermark using ProPainter.

        Args:
            video_path: Path to input video file.
            mask_path: Path to binary mask PNG (255=watermark, 0=keep).
            output_path: Path for the output video file.
            progress_callback: Optional callback(progress_float, status_message).
            cancel_event: Optional threading.Event to signal cancellation.

        Returns:
            True if successful, False otherwise.
        """
        if progress_callback:
            progress_callback(0.0, "Preparing...")

        # Create a temp directory for ProPainter output
        app_dir = os.path.dirname(os.path.abspath(__file__))
        temp_base = os.path.join(app_dir, "temp")
        os.makedirs(temp_base, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=temp_base, prefix="pp_")

        try:
            # Get video info
            video_info = self._get_video_info(video_path)
            fps = video_info.get("fps", 24)
            total_frames = video_info.get("frame_count", 0)

            if progress_callback:
                progress_callback(
                    0.05,
                    f"Video: {video_info['width']}x{video_info['height']}, "
                    f"{total_frames} frames @ {fps:.1f}fps",
                )

            # Check for cancellation
            if cancel_event and cancel_event.is_set():
                return False

            # Run ProPainter inference
            if progress_callback:
                progress_callback(0.1, "Running ProPainter inpainting...")

            success = self._run_inference(
                video_path,
                mask_path,
                temp_dir,
                fps,
                progress_callback,
                cancel_event,
            )

            if not success:
                raise RuntimeError("ProPainter inference failed (unknown reason)")

            if cancel_event and cancel_event.is_set():
                return False

            # Find the output video from ProPainter
            pp_output = self._find_propainter_output(temp_dir)
            if pp_output is None:
                raise RuntimeError(
                    f"No output video found from ProPainter in {temp_dir}"
                )

            if progress_callback:
                progress_callback(0.85, "Merging audio from original video...")

            # Check if original has audio
            has_audio = self._has_audio(video_path)

            if has_audio:
                # Merge audio from original video
                self._merge_audio(pp_output, video_path, output_path, fps)
            else:
                # Just copy/re-encode to output path
                shutil.copy2(pp_output, output_path)

            if progress_callback:
                progress_callback(1.0, "Done!")

            return True

        except Exception as e:
            if progress_callback:
                progress_callback(0.0, f"Error: {str(e)}")
            raise
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def _run_inference(
        self,
        video_path: str,
        mask_path: str,
        output_dir: str,
        fps: float,
        progress_callback: Optional[Callable] = None,
        cancel_event=None,
    ) -> bool:
        """Run ProPainter's inference script as a subprocess."""
        # Get the Python executable from the current venv
        python_exe = sys.executable

        cmd = [
            python_exe,
            self.inference_script,
            "--video", video_path,
            "--mask", mask_path,
            "--output", output_dir,
            "--save_fps", str(int(round(fps))),
            "--mask_dilation", str(self.mask_dilation),
            "--subvideo_length", str(self.subvideo_length),
            "--neighbor_length", str(self.neighbor_length),
            "--ref_stride", str(self.ref_stride),
            "--raft_iter", str(self.raft_iter),
        ]

        if self.use_fp16:
            cmd.append("--fp16")

        # Run the subprocess
        env = os.environ.copy()
        env["PYTHONPATH"] = self.propainter_dir + os.pathsep + env.get("PYTHONPATH", "")
        # Force UTF-8 output so print() can handle emoji/Unicode in filenames
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.propainter_dir,
            env=env,
        )

        # Monitor output for progress
        output_lines = []
        while True:
            if cancel_event and cancel_event.is_set():
                process.terminate()
                process.wait(timeout=10)
                return False

            raw_line = process.stdout.readline()
            if not raw_line and process.poll() is not None:
                break

            # Decode bytes safely — handles emoji filenames on Windows
            line = raw_line.decode('utf-8', errors='replace').strip()
            if line:
                output_lines.append(line)

                # Parse progress from ProPainter output
                progress = self._parse_progress(line)
                if progress is not None and progress_callback:
                    # Scale progress to 0.1 - 0.85 range
                    scaled = 0.1 + progress * 0.75
                    progress_callback(scaled, line)
                elif progress_callback:
                    # Just forward the status message
                    progress_callback(None, line)

        return_code = process.returncode
        if return_code != 0:
            # Collect the last 20 lines of output for error diagnosis
            error_tail = output_lines[-20:] if output_lines else ["(no output captured)"]
            error_output = "\n".join(error_tail)
            print(f"ProPainter error output:\n{error_output}", file=sys.stderr)
            # Raise with the actual error so it shows in the GUI log
            raise RuntimeError(
                f"ProPainter exited with code {return_code}:\n"
                + "\n".join(output_lines[-10:] if output_lines else ["(no output)"])
            )

        return True

    def _parse_progress(self, line: str) -> Optional[float]:
        """
        Parse progress from ProPainter output lines.
        ProPainter prints lines like:
        - "Processing: 10/100 frames"
        - Progress bar indicators
        """
        # Try to match "X/Y" pattern for frame progress
        match = re.search(r"(\d+)\s*/\s*(\d+)", line)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            if total > 0:
                return min(current / total, 1.0)

        # Try to match percentage pattern
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
        if match:
            return min(float(match.group(1)) / 100.0, 1.0)

        return None

    def _find_propainter_output(self, output_dir: str) -> Optional[str]:
        """Find the output video file from ProPainter results."""
        # ProPainter saves to a subdirectory named after the input
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith((".mp4", ".avi", ".mkv")):
                    return os.path.join(root, f)
        return None

    def _get_video_info(self, video_path: str) -> dict:
        """Get video metadata using OpenCV."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        }
        info["duration"] = info["frame_count"] / max(info["fps"], 1)
        cap.release()
        return info

    def _has_audio(self, video_path: str) -> bool:
        """Check if a video file has an audio stream using FFmpeg."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-select_streams", "a",
                    "-show_entries", "stream=codec_type",
                    "-of", "csv=p=0",
                    video_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "audio" in result.stdout.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If ffprobe fails, assume there's audio
            return True

    def _merge_audio(
        self,
        video_no_audio: str,
        original_video: str,
        output_path: str,
        fps: float,
    ):
        """
        Merge the audio from the original video with the processed video
        using FFmpeg.
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite
            "-i", video_no_audio,    # Processed video (no audio)
            "-i", original_video,     # Original video (with audio)
            "-c:v", "libx264",        # Re-encode video with H.264
            "-preset", "medium",
            "-crf", "18",             # High quality
            "-c:a", "aac",            # AAC audio
            "-b:a", "192k",
            "-map", "0:v:0",          # Video from processed
            "-map", "1:a:0?",         # Audio from original (? = optional)
            "-r", str(fps),           # Maintain original FPS
            "-shortest",              # Match shortest stream
            "-movflags", "+faststart",
            output_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            # Fallback: try without audio
            print(f"Audio merge failed, saving without audio: {result.stderr}", file=sys.stderr)
            shutil.copy2(video_no_audio, output_path)

    # ─── ROI Crop Methods ──────────────────────────────────────────────

    MIN_CROP_SIZE = 64  # Minimum crop dimension for ProPainter

    def _get_mask_bbox(self, mask_path: str, padding: int, frame_w: int, frame_h: int):
        """
        Find bounding box of white pixels in mask, expand by padding.
        Returns (x, y, w, h) clamped to frame bounds.
        """
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise ValueError(f"Cannot read mask: {mask_path}")

        # Find non-zero pixels
        coords = cv2.findNonZero(mask)
        if coords is None:
            raise ValueError("Mask is completely black — no watermark region")

        x, y, w, h = cv2.boundingRect(coords)

        # Expand by padding
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(frame_w - x, w + 2 * padding)
        h = min(frame_h - y, h + 2 * padding)

        # Enforce minimum size
        if w < self.MIN_CROP_SIZE:
            expand = self.MIN_CROP_SIZE - w
            x = max(0, x - expand // 2)
            w = min(frame_w - x, self.MIN_CROP_SIZE)
        if h < self.MIN_CROP_SIZE:
            expand = self.MIN_CROP_SIZE - h
            y = max(0, y - expand // 2)
            h = min(frame_h - y, self.MIN_CROP_SIZE)

        # FFmpeg crop requires even dimensions
        w = w if w % 2 == 0 else w + 1
        h = h if h % 2 == 0 else h + 1
        w = min(w, frame_w - x)
        h = min(h, frame_h - y)

        return (x, y, w, h)

    def _crop_video(self, video_path: str, bbox: tuple, output_path: str, fps: float):
        """Crop video to bbox region using FFmpeg."""
        x, y, w, h = bbox
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"crop={w}:{h}:{x}:{y}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "15",
            "-an",  # Drop audio for processing
            "-r", str(int(round(fps))),
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg crop failed: {result.stderr[-500:]}")

    def _crop_mask(self, mask_path: str, bbox: tuple, output_path: str):
        """Crop mask PNG to bbox region."""
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        x, y, w, h = bbox
        cropped = mask[y:y+h, x:x+w]
        cv2.imwrite(output_path, cropped)

    def _composite_back(
        self,
        original_video: str,
        inpainted_crop: str,
        bbox: tuple,
        output_path: str,
        fps: float,
    ):
        """Overlay inpainted crop back onto original video at bbox position."""
        x, y, w, h = bbox
        has_audio = self._has_audio(original_video)

        cmd = [
            "ffmpeg", "-y",
            "-i", original_video,       # Original full-size video
            "-i", inpainted_crop,        # Small inpainted crop
            "-filter_complex",
            f"[1:v]scale={w}:{h}[crop];[0:v][crop]overlay={x}:{y}:shortest=1[out]",
            "-map", "[out]",
        ]

        if has_audio:
            cmd += ["-map", "0:a?"]

        cmd += [
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-r", str(int(round(fps))),
            "-movflags", "+faststart",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg composite failed: {result.stderr[-500:]}")

    def process_video_cropped(
        self,
        video_path: str,
        mask_path: str,
        output_path: str,
        padding: int = 20,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_event=None,
    ) -> bool:
        """
        Optimized watermark removal: crop to ROI, inpaint, composite back.
        Much faster and uses far less VRAM than full-frame processing.
        """
        if progress_callback:
            progress_callback(0.0, "Preparing ROI crop...")

        app_dir = os.path.dirname(os.path.abspath(__file__))
        temp_base = os.path.join(app_dir, "temp")
        os.makedirs(temp_base, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=temp_base, prefix="pp_crop_")

        try:
            # Step 1: Get video info
            video_info = self._get_video_info(video_path)
            fps = video_info.get("fps", 24)
            frame_w = video_info["width"]
            frame_h = video_info["height"]

            if progress_callback:
                progress_callback(0.05, f"Video: {frame_w}x{frame_h}, {video_info['frame_count']} frames")

            if cancel_event and cancel_event.is_set():
                return False

            # Step 2: Get mask bounding box
            bbox = self._get_mask_bbox(mask_path, padding, frame_w, frame_h)
            x, y, w, h = bbox

            if progress_callback:
                progress_callback(
                    0.08,
                    f"ROI: {w}x{h} at ({x},{y}) — "
                    f"{(w*h)/(frame_w*frame_h)*100:.1f}% of frame "
                    f"(padding={padding}px)"
                )

            # Step 3: Crop video to ROI
            if progress_callback:
                progress_callback(0.10, f"Cropping video to {w}x{h} ROI...")

            cropped_video = os.path.join(temp_dir, "cropped_input.mp4")
            self._crop_video(video_path, bbox, cropped_video, fps)

            if cancel_event and cancel_event.is_set():
                return False

            # Step 4: Crop mask to ROI
            cropped_mask = os.path.join(temp_dir, "cropped_mask.png")
            self._crop_mask(mask_path, bbox, cropped_mask)

            if progress_callback:
                progress_callback(0.15, f"Running ProPainter on {w}x{h} crop...")

            # Step 5: Run ProPainter on the small crop
            pp_output_dir = os.path.join(temp_dir, "pp_out")
            os.makedirs(pp_output_dir, exist_ok=True)

            def scaled_cb(progress, status):
                if progress is not None and progress_callback:
                    # Scale ProPainter progress to 0.15 - 0.80 range
                    scaled = 0.15 + (progress - 0.1) * (0.65 / 0.75)
                    progress_callback(max(0.15, scaled), status)
                elif progress_callback:
                    progress_callback(None, status)

            success = self._run_inference(
                cropped_video,
                cropped_mask,
                pp_output_dir,
                fps,
                scaled_cb,
                cancel_event,
            )

            if not success:
                raise RuntimeError("ProPainter inference failed on cropped region")

            if cancel_event and cancel_event.is_set():
                return False

            # Step 6: Find ProPainter output
            pp_output = self._find_propainter_output(pp_output_dir)
            if pp_output is None:
                raise RuntimeError(f"No ProPainter output found in {pp_output_dir}")

            # Step 7: Composite back onto original
            if progress_callback:
                progress_callback(0.85, "Compositing inpainted region back...")

            self._composite_back(video_path, pp_output, bbox, output_path, fps)

            if progress_callback:
                progress_callback(1.0, "Done!")

            return True

        except Exception as e:
            if progress_callback:
                progress_callback(0.0, f"Error: {str(e)}")
            raise
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def check_gpu(self) -> dict:
        """Check if CUDA GPU is available for ProPainter."""
        try:
            import torch

            return {
                "cuda_available": torch.cuda.is_available(),
                "gpu_name": (
                    torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
                ),
                "vram_gb": (
                    torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    if torch.cuda.is_available()
                    else 0
                ),
                "pytorch_version": torch.__version__,
                "cuda_version": (
                    torch.version.cuda if torch.cuda.is_available() else None
                ),
            }
        except ImportError:
            return {
                "cuda_available": False,
                "gpu_name": None,
                "vram_gb": 0,
                "pytorch_version": None,
                "cuda_version": None,
            }

    def check_weights(self) -> dict:
        """Check if ProPainter model weights are present."""
        weights_dir = os.path.join(self.propainter_dir, "weights")
        required = {
            "ProPainter.pth": False,
            "recurrent_flow_completion.pth": False,
            "raft-things.pth": False,
        }

        if os.path.exists(weights_dir):
            for name in required:
                if os.path.exists(os.path.join(weights_dir, name)):
                    required[name] = True

        return required

