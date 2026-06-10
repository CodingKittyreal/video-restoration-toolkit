"""
ProPainter Watermark Remover — GUI Application
================================================
A modern desktop application for batch video watermark removal
using ProPainter AI inpainting with auto watermark detection.

Features:
- Batch video selection and processing
- Auto watermark detection with preview
- Manual mask editing via drawing
- Real-time progress tracking
- GPU status monitoring
- Configurable settings
"""

import os
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Optional, List, Dict

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np

from watermark_detector import WatermarkDetector
from propainter_runner import ProPainterRunner


# ─── Constants ────────────────────────────────────────────────────────────
APP_TITLE = "ProPainter Watermark Remover"
APP_VERSION = "1.1"
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SUPPORTED_FORMATS = (
    ("Video Files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v"),
    ("All Files", "*.*"),
)

# Color palette
ACCENT = "#00D4AA"
ACCENT_HOVER = "#00F0C0"
ACCENT_DARK = "#009977"
DANGER = "#FF4D6A"
DANGER_HOVER = "#FF6B84"
WARNING = "#FFB020"
BG_DARK = "#0D1117"
BG_CARD = "#161B22"
BG_ELEVATED = "#1C2333"
TEXT_PRIMARY = "#E6EDF3"
TEXT_SECONDARY = "#8B949E"
TEXT_DIM = "#484F58"
BORDER = "#30363D"
SUCCESS = "#3FB950"


# ─── Main Application ────────────────────────────────────────────────────
class WatermarkRemoverApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Window setup
        self.title(f"ProPainter Watermark Remover")
        self.geometry("1100x820")
        self.minsize(900, 700)
        self.configure(fg_color=BG_DARK)

        # State
        self.video_queue: List[Dict] = []  # [{path, status, mask_path, ...}]
        self.is_processing = False
        self.cancel_event = threading.Event()
        self.detector = WatermarkDetector()
        self.runner = None
        self._init_runner()

        # Build UI
        self._build_header()
        self._build_toolbar()
        self._build_video_list()
        self._build_settings_panel()
        self._build_progress_panel()
        self._build_log_panel()
        self._build_status_bar()

        # Check GPU on startup
        self.after(500, self._check_gpu_status)

    def _init_runner(self):
        """Initialize ProPainter runner."""
        try:
            self.runner = ProPainterRunner()
        except FileNotFoundError as e:
            self.runner = None

    # ─── UI Building ─────────────────────────────────────────────────

    def _build_header(self):
        """Build the app header/title bar."""
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            title_frame,
            text="ProPainter Watermark Remover",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text=f"  v{APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(5, 0))

        # GPU status indicator
        self.gpu_frame = ctk.CTkFrame(header, fg_color="transparent")
        self.gpu_frame.pack(side="right", padx=20, pady=10)

        self.gpu_indicator = ctk.CTkLabel(
            self.gpu_frame,
            text="Checking GPU...",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        )
        self.gpu_indicator.pack(side="right")

    def _build_toolbar(self):
        """Build the toolbar with action buttons."""
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=50)
        toolbar.pack(fill="x", padx=20, pady=(15, 5))

        # Add Videos button
        self.btn_add = ctk.CTkButton(
            toolbar,
            text="+  Add Videos",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#000000",
            corner_radius=8,
            height=38,
            width=160,
            command=self._add_videos,
        )
        self.btn_add.pack(side="left", padx=(0, 8))

        # Paste List button
        self.btn_paste_list = ctk.CTkButton(
            toolbar,
            text="Paste List",
            font=ctk.CTkFont(size=13),
            fg_color=BG_ELEVATED,
            hover_color=ACCENT_DARK,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            height=38,
            width=120,
            command=self._paste_list,
        )
        self.btn_paste_list.pack(side="left", padx=(0, 8))

        # Clear button
        self.btn_clear = ctk.CTkButton(
            toolbar,
            text="Clear All",
            font=ctk.CTkFont(size=13),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            height=38,
            width=120,
            command=self._clear_queue,
        )
        self.btn_clear.pack(side="left", padx=(0, 8))

        # Open output folder button
        self.btn_output = ctk.CTkButton(
            toolbar,
            text="Output Folder",
            font=ctk.CTkFont(size=13),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            height=38,
            width=150,
            command=self._open_output_dir,
        )
        self.btn_output.pack(side="left", padx=(0, 8))

        # Video count label
        self.lbl_count = ctk.CTkLabel(
            toolbar,
            text="0 videos in queue",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_DIM,
        )
        self.lbl_count.pack(side="right", padx=10)

    def _build_video_list(self):
        """Build the scrollable video queue list."""
        list_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        list_frame.pack(fill="both", expand=True, padx=20, pady=8)

        # Header
        list_header = ctk.CTkFrame(list_frame, fg_color="transparent", height=35)
        list_header.pack(fill="x", padx=15, pady=(10, 5))
        list_header.pack_propagate(False)

        ctk.CTkLabel(
            list_header,
            text="VIDEO QUEUE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(side="left")

        # Scrollable frame for video cards
        self.video_scroll = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_DIM,
        )
        self.video_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Placeholder text
        self.placeholder_label = ctk.CTkLabel(
            self.video_scroll,
            text="Drop videos here or click 'Add Videos'\n\nSupported: MP4, AVI, MKV, MOV, WMV, FLV, WebM",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_DIM,
            justify="center",
        )
        self.placeholder_label.pack(expand=True, pady=60)

        # Store video card widgets
        self.video_cards: List[ctk.CTkFrame] = []

    def _build_settings_panel(self):
        """Build the collapsible settings panel."""
        settings_outer = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        settings_outer.pack(fill="x", padx=20, pady=4)

        # Settings header
        settings_header = ctk.CTkFrame(settings_outer, fg_color="transparent")
        settings_header.pack(fill="x", padx=15, pady=(8, 0))

        ctk.CTkLabel(
            settings_header,
            text="SETTINGS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(side="left")

        # Settings content
        settings_content = ctk.CTkFrame(settings_outer, fg_color="transparent")
        settings_content.pack(fill="x", padx=15, pady=(5, 10))

        # Row 1: FP16, Mask Dilation, Sensitivity
        row1 = ctk.CTkFrame(settings_content, fg_color="transparent")
        row1.pack(fill="x", pady=3)

        # FP16 toggle
        ctk.CTkLabel(
            row1, text="FP16 Mode:", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        self.var_fp16 = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            row1,
            text="",
            variable=self.var_fp16,
            onvalue=True,
            offvalue=False,
            progress_color=ACCENT,
            width=40,
        ).pack(side="left", padx=(0, 20))

        # Mask dilation
        ctk.CTkLabel(
            row1, text="Mask Dilation:", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        self.var_dilation = ctk.IntVar(value=8)
        ctk.CTkOptionMenu(
            row1,
            values=["4", "6", "8", "10", "12", "16"],
            variable=self.var_dilation,
            font=ctk.CTkFont(size=12),
            fg_color=BG_ELEVATED,
            button_color=BORDER,
            button_hover_color=TEXT_DIM,
            width=70,
            height=28,
            command=lambda v: self.var_dilation.set(int(v)),
        ).pack(side="left", padx=(0, 20))

        # Detection sensitivity
        ctk.CTkLabel(
            row1, text="Detection Sensitivity:", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        self.var_sensitivity = ctk.DoubleVar(value=1.0)
        self.sensitivity_slider = ctk.CTkSlider(
            row1,
            from_=0.3,
            to=3.0,
            number_of_steps=27,
            variable=self.var_sensitivity,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            width=150,
            height=16,
        )
        self.sensitivity_slider.pack(side="left", padx=(0, 5))
        self.lbl_sensitivity = ctk.CTkLabel(
            row1, text="1.0x", font=ctk.CTkFont(size=12), text_color=ACCENT, width=40
        )
        self.lbl_sensitivity.pack(side="left")
        self.var_sensitivity.trace_add(
            "write", lambda *_: self.lbl_sensitivity.configure(text=f"{self.var_sensitivity.get():.1f}x")
        )

        # Row 2: Crop Mode + ROI Padding
        row2 = ctk.CTkFrame(settings_content, fg_color="transparent")
        row2.pack(fill="x", pady=3)

        # Crop Mode toggle
        ctk.CTkLabel(
            row2, text="Crop Mode:", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        self.var_crop_mode = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            row2,
            text="",
            variable=self.var_crop_mode,
            onvalue=True,
            offvalue=False,
            progress_color=ACCENT,
            width=40,
        ).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(
            row2, text="(faster, less VRAM)", font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(0, 20))

        # ROI Padding
        ctk.CTkLabel(
            row2, text="ROI Padding:", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        self.var_roi_padding = ctk.IntVar(value=20)
        self.roi_padding_slider = ctk.CTkSlider(
            row2,
            from_=0,
            to=100,
            number_of_steps=20,
            variable=self.var_roi_padding,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            width=150,
            height=16,
        )
        self.roi_padding_slider.pack(side="left", padx=(0, 5))
        self.lbl_roi_padding = ctk.CTkLabel(
            row2, text="20px", font=ctk.CTkFont(size=12), text_color=ACCENT, width=50
        )
        self.lbl_roi_padding.pack(side="left")
        self.var_roi_padding.trace_add(
            "write", lambda *_: self.lbl_roi_padding.configure(text=f"{int(self.var_roi_padding.get())}px")
        )

        # Row 3: Output directory
        row3 = ctk.CTkFrame(settings_content, fg_color="transparent")
        row3.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row3, text="Output:", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(
            row3,
            text=OUTPUT_DIR,
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color=ACCENT,
        ).pack(side="left")

    def _build_progress_panel(self):
        """Build the progress tracking panel."""
        progress_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        progress_frame.pack(fill="x", padx=20, pady=4)

        inner = ctk.CTkFrame(progress_frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=10)

        # Start/Cancel button
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 8))

        self.btn_process = ctk.CTkButton(
            btn_frame,
            text=">>  Start Batch Processing",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#000000",
            corner_radius=10,
            height=44,
            command=self._toggle_processing,
        )
        self.btn_process.pack(fill="x")

        # Current video progress
        self.lbl_current = ctk.CTkLabel(
            inner,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        self.lbl_current.pack(fill="x")

        self.progress_current = ctk.CTkProgressBar(
            inner,
            progress_color=ACCENT,
            fg_color=BG_ELEVATED,
            height=8,
            corner_radius=4,
        )
        self.progress_current.pack(fill="x", pady=(2, 6))
        self.progress_current.set(0)

        # Overall progress
        self.lbl_overall = ctk.CTkLabel(
            inner,
            text="Overall: 0 / 0 videos",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        self.lbl_overall.pack(fill="x")

        self.progress_overall = ctk.CTkProgressBar(
            inner,
            progress_color=ACCENT_DARK,
            fg_color=BG_ELEVATED,
            height=6,
            corner_radius=3,
        )
        self.progress_overall.pack(fill="x", pady=(2, 0))
        self.progress_overall.set(0)

    def _build_log_panel(self):
        """Build the scrollable log output panel."""
        log_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        log_frame.pack(fill="x", padx=20, pady=(4, 8))

        header = ctk.CTkFrame(log_frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(8, 0))

        ctk.CTkLabel(
            header,
            text="LOG",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(side="left")

        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=100,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="x", padx=10, pady=(5, 10))

    def _build_status_bar(self):
        """Build the bottom status bar."""
        status = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=28)
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            status,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
        )
        self.lbl_status.pack(side="left", padx=15)

    # ─── Actions ────────────────────────────────────────────────────

    def _add_videos(self):
        """Open file dialog to select videos."""
        files = filedialog.askopenfilenames(
            title="Select Videos to Remove Watermarks",
            filetypes=SUPPORTED_FORMATS,
        )

        if not files:
            return

        added = 0
        for f in files:
            # Avoid duplicates
            if any(v["path"] == f for v in self.video_queue):
                continue
            self.video_queue.append(
                {
                    "path": f,
                    "status": "queued",
                    "mask_path": None,
                    "mask_data": None,
                    "progress": 0.0,
                }
            )
            added += 1

        self._refresh_video_list()
        self._log(f"Added {added} video(s) to queue.")

    def _clear_queue(self):
        """Clear all videos from the queue."""
        if self.is_processing:
            messagebox.showwarning("Warning", "Cannot clear queue while processing.")
            return

        self.video_queue.clear()
        self._refresh_video_list()
        self._log("Queue cleared.")

    def _remove_video(self, index: int):
        """Remove a single video from the queue."""
        if self.is_processing:
            messagebox.showwarning("Warning", "Cannot remove videos while processing.")
            return

        if 0 <= index < len(self.video_queue):
            removed = self.video_queue.pop(index)
            self._refresh_video_list()
            self._log(f"Removed: {os.path.basename(removed['path'])}")

    def _preview_mask(self, index: int):
        """Preview auto-detected watermark mask for a video."""
        if 0 <= index < len(self.video_queue):
            video = self.video_queue[index]
            MaskPreviewDialog(self, video, self.detector, self.var_sensitivity.get())

    def _paste_list(self):
        """Open a dialog to paste a list of filenames and add them from a selected folder."""
        PasteListDialog(self)

    def _open_output_dir(self):
        """Open the output directory in file explorer."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.startfile(OUTPUT_DIR)

    def _refresh_video_list(self):
        """Refresh the video list display."""
        # Remove existing cards
        for card in self.video_cards:
            card.destroy()
        self.video_cards.clear()

        # Update count
        count = len(self.video_queue)
        self.lbl_count.configure(text=f"{count} video{'s' if count != 1 else ''} in queue")

        # Show/hide placeholder
        if count == 0:
            self.placeholder_label.pack(expand=True, pady=60)
            return
        else:
            self.placeholder_label.pack_forget()

        # Create cards
        for i, video in enumerate(self.video_queue):
            card = self._create_video_card(i, video)
            self.video_cards.append(card)

    def _create_video_card(self, index: int, video: dict) -> ctk.CTkFrame:
        """Create a video card widget for the queue list."""
        card = ctk.CTkFrame(
            self.video_scroll,
            fg_color=BG_ELEVATED,
            corner_radius=8,
            height=48,
        )
        card.pack(fill="x", pady=2, padx=2)
        card.pack_propagate(False)

        # Status icon
        status_icons = {
            "queued": ("[ ]", TEXT_DIM),
            "detecting": ("[~]", WARNING),
            "processing": ("[>]", ACCENT),
            "done": ("[OK]", SUCCESS),
            "error": ("[!]", DANGER),
        }
        icon, color = status_icons.get(video["status"], ("[ ]", TEXT_DIM))

        ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color=color,
            width=35,
        ).pack(side="left", padx=(10, 5))

        # Filename
        filename = os.path.basename(video["path"])
        name_label = ctk.CTkLabel(
            card,
            text=filename,
            font=ctk.CTkFont(size=13),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        name_label.pack(side="left", fill="x", expand=True, padx=5)

        # Mask indicator — show green checkmark if mask_data has been manually set
        if video.get("mask_data") is not None:
            ctk.CTkLabel(
                card,
                text="✓ Mask",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=SUCCESS,
                width=60,
            ).pack(side="right", padx=(2, 5))

        # Status text
        status_text = video["status"].capitalize()
        if video["status"] == "processing":
            status_text = f"Processing ({video['progress']:.0%})"

        ctk.CTkLabel(
            card,
            text=status_text,
            font=ctk.CTkFont(size=11),
            text_color=color,
            width=100,
        ).pack(side="right", padx=5)

        # Preview mask button
        btn_preview = ctk.CTkButton(
            card,
            text="Mask",
            font=ctk.CTkFont(size=11),
            fg_color=BG_CARD,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            width=70,
            height=28,
            command=lambda idx=index: self._preview_mask(idx),
        )
        btn_preview.pack(side="right", padx=2)

        # Remove button
        btn_remove = ctk.CTkButton(
            card,
            text="X",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="transparent",
            hover_color=DANGER,
            text_color=TEXT_DIM,
            corner_radius=6,
            width=30,
            height=28,
            command=lambda idx=index: self._remove_video(idx),
        )
        btn_remove.pack(side="right", padx=2)

        return card

    # ─── Processing ──────────────────────────────────────────────────

    def _toggle_processing(self):
        """Start or cancel batch processing."""
        if self.is_processing:
            self._cancel_processing()
        else:
            self._start_processing()

    def _start_processing(self):
        """Start batch processing all queued videos."""
        if not self.video_queue:
            messagebox.showinfo("Info", "No videos in queue. Add videos first.")
            return

        if self.runner is None:
            self._init_runner()
            if self.runner is None:
                messagebox.showerror(
                    "Error",
                    "ProPainter not found!\n\n"
                    "Please clone ProPainter into the app directory:\n"
                    "git clone https://github.com/sczhou/ProPainter.git",
                )
                return

        self.is_processing = True
        self.cancel_event.clear()

        # Update UI
        self.btn_process.configure(
            text="Stop Processing",
            fg_color=DANGER,
            hover_color=DANGER_HOVER,
        )
        self.btn_add.configure(state="disabled")
        self.btn_clear.configure(state="disabled")

        # Start processing thread
        thread = threading.Thread(target=self._process_batch, daemon=True)
        thread.start()

    def _cancel_processing(self):
        """Cancel the current batch processing."""
        self.cancel_event.set()
        self._log("Cancellation requested... waiting for current video to finish.")

    def _process_batch(self):
        """Process all videos in the queue (runs in background thread)."""
        total = len(self.video_queue)
        completed = 0

        self._log(f"=== Starting batch processing: {total} videos ===")

        # Update runner settings from GUI
        self.runner.use_fp16 = self.var_fp16.get()
        self.runner.mask_dilation = self.var_dilation.get()

        for i, video in enumerate(self.video_queue):
            if self.cancel_event.is_set():
                self._log("Processing cancelled by user.")
                break

            filename = os.path.basename(video["path"])
            self._log(f"\n-- [{i+1}/{total}] Processing: {filename}")

            # Update status
            video["status"] = "detecting"
            self._safe_ui(self._refresh_video_list)
            self._safe_ui(
                lambda c=completed, t=total: self.lbl_overall.configure(
                    text=f"Overall: {c} / {t} videos"
                )
            )
            self._safe_ui(
                lambda val=completed / total: self.progress_overall.set(val)
            )

            try:
                # Step 1: Detect watermark if no mask provided
                if video["mask_data"] is None:
                    self._safe_ui(
                        lambda fn=filename: self.lbl_current.configure(
                            text=f"Detecting watermark in {fn}..."
                        )
                    )
                    self._safe_ui(lambda: self.progress_current.set(0))

                    mask = self.detector.detect(
                        video["path"],
                        sensitivity=self.var_sensitivity.get(),
                    )
                    video["mask_data"] = mask

                    # Check if any watermark was detected
                    if np.sum(mask > 0) < 100:
                        self._log(f"  No significant watermark detected in {filename}, skipping.")
                        video["status"] = "done"
                        completed += 1
                        continue

                    self._log(f"  Watermark detected ({np.sum(mask > 0)} pixels)")
                else:
                    mask = video["mask_data"]
                    self._log(f"  Using pre-configured mask")

                # Step 2: Save mask to temp file
                mask_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "temp", "masks"
                )
                os.makedirs(mask_dir, exist_ok=True)
                mask_path = os.path.join(mask_dir, f"mask_{i:04d}.png")
                cv2.imwrite(mask_path, mask)
                video["mask_path"] = mask_path

                # Step 3: Run ProPainter
                video["status"] = "processing"
                self._safe_ui(self._refresh_video_list)

                # Determine output filename
                name_base = Path(filename).stem
                name_ext = Path(filename).suffix or ".mp4"
                output_path = os.path.join(OUTPUT_DIR, f"{name_base}_nowm{name_ext}")

                # Handle existing files
                counter = 1
                while os.path.exists(output_path):
                    output_path = os.path.join(
                        OUTPUT_DIR, f"{name_base}_nowm_{counter}{name_ext}"
                    )
                    counter += 1

                def progress_cb(progress, status, fn=filename):
                    if progress is not None:
                        video["progress"] = progress
                        self._safe_ui(
                            lambda p=progress: self.progress_current.set(p)
                        )
                    self._safe_ui(
                        lambda s=status, f=fn: self.lbl_current.configure(
                            text=f"[{f}] {s}"
                        )
                    )

                # Use crop mode (ROI) or full-frame mode
                use_crop = self.var_crop_mode.get()
                if use_crop:
                    roi_padding = int(self.var_roi_padding.get())
                    self._log(f"  Crop mode: ON (padding={roi_padding}px)")
                    success = self.runner.process_video_cropped(
                        video["path"],
                        mask_path,
                        output_path,
                        padding=roi_padding,
                        progress_callback=progress_cb,
                        cancel_event=self.cancel_event,
                    )
                else:
                    self._log(f"  Crop mode: OFF (full frame)")
                    success = self.runner.process_video(
                        video["path"],
                        mask_path,
                        output_path,
                        progress_callback=progress_cb,
                        cancel_event=self.cancel_event,
                    )

                if success:
                    video["status"] = "done"
                    video["progress"] = 1.0
                    self._log(f"  Saved: {os.path.basename(output_path)}")
                    completed += 1
                else:
                    if self.cancel_event.is_set():
                        video["status"] = "queued"
                    else:
                        video["status"] = "error"
                        self._log(f"  Failed to process {filename} (see [ERR] lines above for details)")

            except Exception as e:
                video["status"] = "error"
                self._log(f"  Error: {str(e)}")
                traceback.print_exc()

            self._safe_ui(self._refresh_video_list)

        # Finished
        self._safe_ui(
            lambda: self.progress_overall.set(completed / max(total, 1))
        )
        self._safe_ui(
            lambda c=completed, t=total: self.lbl_overall.configure(
                text=f"Overall: {c} / {t} videos completed"
            )
        )
        self._log(f"\n=== Batch complete: {completed}/{total} videos processed ===")

        self.is_processing = False
        self._safe_ui(self._reset_process_button)

        # Cleanup temp masks
        try:
            mask_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "temp", "masks"
            )
            if os.path.exists(mask_dir):
                import shutil
                shutil.rmtree(mask_dir, ignore_errors=True)
        except Exception:
            pass

    def _reset_process_button(self):
        """Reset the process button to its default state."""
        self.btn_process.configure(
            text=">>  Start Batch Processing",
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
        )
        self.btn_add.configure(state="normal")
        self.btn_clear.configure(state="normal")

    # ─── GPU Check ──────────────────────────────────────────────────

    def _check_gpu_status(self):
        """Check GPU status and update the indicator."""
        def check():
            try:
                import torch

                if torch.cuda.is_available():
                    gpu_name = torch.cuda.get_device_name(0)
                    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    self._safe_ui(
                        lambda: self.gpu_indicator.configure(
                            text=f"GPU: {gpu_name} ({vram:.0f}GB)",
                            text_color=SUCCESS,
                        )
                    )
                    self._log(f"GPU: {gpu_name} ({vram:.0f}GB VRAM) -- CUDA {torch.version.cuda}")
                else:
                    self._safe_ui(
                        lambda: self.gpu_indicator.configure(
                            text="No CUDA GPU detected",
                            text_color=DANGER,
                        )
                    )
                    self._log("WARNING: No CUDA GPU detected. Processing will be very slow!")
            except ImportError:
                self._safe_ui(
                    lambda: self.gpu_indicator.configure(
                        text="PyTorch not installed",
                        text_color=DANGER,
                    )
                )
                self._log("ERROR: PyTorch not found. Please run setup.bat first.")

            # Also check ProPainter
            if self.runner:
                weights = self.runner.check_weights()
                missing = [k for k, v in weights.items() if not v]
                if missing:
                    self._log(
                        f"ProPainter weights will be downloaded on first run: {', '.join(missing)}"
                    )
                else:
                    self._log("ProPainter model weights found.")
            else:
                self._log("WARNING: ProPainter not found. Please clone the repository.")

        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    # ─── Utilities ──────────────────────────────────────────────────

    def _log(self, message: str):
        """Add a message to the log panel (thread-safe)."""
        def update():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.after(0, update)

    def _safe_ui(self, func):
        """Schedule a UI update on the main thread."""
        try:
            self.after(0, func)
        except Exception:
            pass


# ─── Mask Preview Dialog ─────────────────────────────────────────────────
class MaskPreviewDialog(ctk.CTkToplevel):
    """Dialog for previewing and editing watermark detection masks."""

    def __init__(
        self,
        parent: WatermarkRemoverApp,
        video: dict,
        detector: WatermarkDetector,
        sensitivity: float,
    ):
        super().__init__(parent)

        self.parent_app = parent
        self.video = video
        self.detector = detector
        self.sensitivity = sensitivity

        self.title(f"Mask Preview - {os.path.basename(video['path'])}")
        self.geometry("1100x680")
        self.configure(fg_color=BG_DARK)
        self.transient(parent)
        self.grab_set()

        # State
        self.original_frame = None
        self.current_mask = None
        self.display_scale = 1.0
        self.is_drawing = False
        self.draw_mode = "add"  # "add" or "erase"
        self._img_offset_x = 0
        self._img_offset_y = 0
        self._img_original = None  # prevent GC
        self._img_overlay = None   # prevent GC
        self._draw_update_pending = False
        self._detection_running = False

        # Zoom & Pan state
        self._zoom_level = 1.0
        self._pan_x = 0.0  # pan offset in original image pixels
        self._pan_y = 0.0
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        self._space_held = False

        # Read video info for frame navigation
        self.total_frames = 1
        self.current_frame_idx = 0
        self._read_video_info()

        self._build_ui()

        # Wait for the window to fully render, then run detection
        self.after(500, self._run_detection)

    def _build_ui(self):
        """Build the mask preview UI."""
        # Top: sensitivity controls
        control_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        control_bar.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            control_bar,
            text="Sensitivity:",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 5), pady=8)

        self.var_preview_sensitivity = ctk.DoubleVar(value=self.sensitivity)
        self.preview_slider = ctk.CTkSlider(
            control_bar,
            from_=0.3,
            to=3.0,
            number_of_steps=27,
            variable=self.var_preview_sensitivity,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            width=200,
            height=16,
        )
        self.preview_slider.pack(side="left", padx=5, pady=8)

        self.lbl_sens_val = ctk.CTkLabel(
            control_bar,
            text=f"{self.sensitivity:.1f}x",
            font=ctk.CTkFont(size=12),
            text_color=ACCENT,
            width=40,
        )
        self.lbl_sens_val.pack(side="left", padx=(0, 15))
        self.var_preview_sensitivity.trace_add(
            "write",
            lambda *_: self.lbl_sens_val.configure(
                text=f"{self.var_preview_sensitivity.get():.1f}x"
            ),
        )

        self.btn_redetect = ctk.CTkButton(
            control_bar,
            text="Re-detect",
            font=ctk.CTkFont(size=12),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            height=30,
            width=110,
            command=self._run_detection,
        )
        self.btn_redetect.pack(side="left", padx=5, pady=8)

        # Separator
        sep = ctk.CTkFrame(control_bar, fg_color=BORDER, width=1, height=20)
        sep.pack(side="left", padx=10, pady=8)

        # Draw controls
        ctk.CTkLabel(
            control_bar,
            text="Draw:",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 5))

        self.btn_draw_add = ctk.CTkButton(
            control_bar,
            text="+ Add",
            font=ctk.CTkFont(size=11),
            fg_color=ACCENT_DARK,
            hover_color=ACCENT,
            text_color=TEXT_PRIMARY,
            corner_radius=6,
            height=28,
            width=70,
            command=lambda: self._set_draw_mode("add"),
        )
        self.btn_draw_add.pack(side="left", padx=2)

        self.btn_draw_erase = ctk.CTkButton(
            control_bar,
            text="- Erase",
            font=ctk.CTkFont(size=11),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            height=28,
            width=70,
            command=lambda: self._set_draw_mode("erase"),
        )
        self.btn_draw_erase.pack(side="left", padx=2)

        # Brush size
        ctk.CTkLabel(
            control_bar,
            text="  Brush:",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(5, 3))

        self.var_brush = ctk.IntVar(value=15)
        ctk.CTkSlider(
            control_bar,
            from_=5,
            to=50,
            number_of_steps=45,
            variable=self.var_brush,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            width=100,
            height=14,
        ).pack(side="left", padx=3)

        self.lbl_brush_val = ctk.CTkLabel(
            control_bar,
            text="15",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
            width=25,
        )
        self.lbl_brush_val.pack(side="left")
        self.var_brush.trace_add(
            "write",
            lambda *_: self.lbl_brush_val.configure(text=str(self.var_brush.get())),
        )

        # ── Frame navigation bar ──
        frame_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        frame_bar.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            frame_bar,
            text="Frame:",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 5), pady=6)

        # Previous frame button
        ctk.CTkButton(
            frame_bar,
            text="◀",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_PRIMARY,
            corner_radius=6,
            width=32,
            height=28,
            command=self._prev_frame,
        ).pack(side="left", padx=2, pady=6)

        # Frame slider
        self.var_frame = ctk.IntVar(value=self.current_frame_idx)
        self.frame_slider = ctk.CTkSlider(
            frame_bar,
            from_=0,
            to=max(self.total_frames - 1, 1),
            number_of_steps=max(self.total_frames - 1, 1),
            variable=self.var_frame,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            width=350,
            height=16,
            command=lambda v: self._goto_frame(int(float(v))),
        )
        self.frame_slider.pack(side="left", padx=5, pady=6)

        # Next frame button
        ctk.CTkButton(
            frame_bar,
            text="▶",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_PRIMARY,
            corner_radius=6,
            width=32,
            height=28,
            command=self._next_frame,
        ).pack(side="left", padx=2, pady=6)

        # Frame number label
        self.lbl_frame_val = ctk.CTkLabel(
            frame_bar,
            text=f"{self.current_frame_idx} / {self.total_frames - 1}",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color=ACCENT,
            width=100,
        )
        self.lbl_frame_val.pack(side="left", padx=(5, 10), pady=6)

        # Jump-by-10 buttons for faster scrubbing
        ctk.CTkButton(
            frame_bar,
            text="◀◀ -10",
            font=ctk.CTkFont(size=11),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            width=65,
            height=26,
            command=lambda: self._goto_frame(self.current_frame_idx - 10),
        ).pack(side="left", padx=2, pady=6)

        ctk.CTkButton(
            frame_bar,
            text="+10 ▶▶",
            font=ctk.CTkFont(size=11),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            width=65,
            height=26,
            command=lambda: self._goto_frame(self.current_frame_idx + 10),
        ).pack(side="left", padx=2, pady=6)

        # Main content: side-by-side canvases with fixed sizes
        canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        canvas_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Left: Original frame
        left_frame = ctk.CTkFrame(canvas_frame, fg_color=BG_CARD, corner_radius=8)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            left_frame,
            text="Original Frame",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(pady=(8, 4))

        self.canvas_original = tk.Canvas(
            left_frame,
            bg="#0D1117",
            highlightthickness=0,
            width=480,
            height=360,
        )
        self.canvas_original.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Right: Overlay (frame + mask) — this is the drawable canvas
        right_frame = ctk.CTkFrame(canvas_frame, fg_color=BG_CARD, corner_radius=8)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            right_frame,
            text="Detected Watermark (red = will be removed) -- Draw here to edit",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(pady=(8, 4))

        self.canvas_overlay = tk.Canvas(
            right_frame,
            bg="#0D1117",
            highlightthickness=0,
            cursor="crosshair",
            width=480,
            height=360,
        )
        self.canvas_overlay.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Bind drawing events on the overlay canvas
        self.canvas_overlay.bind("<ButtonPress-1>", self._on_draw_start)
        self.canvas_overlay.bind("<B1-Motion>", self._on_draw_move)
        self.canvas_overlay.bind("<ButtonRelease-1>", self._on_draw_end)

        # Bind zoom (mouse scroll) on both canvases
        self.canvas_overlay.bind("<MouseWheel>", self._on_zoom)
        self.canvas_original.bind("<MouseWheel>", self._on_zoom)

        # Bind spacebar for panning
        self.bind("<KeyPress-space>", self._on_space_press)
        self.bind("<KeyRelease-space>", self._on_space_release)
        self.canvas_overlay.bind("<ButtonPress-3>", self._on_pan_start)  # Right-click also pans
        self.canvas_overlay.bind("<B3-Motion>", self._on_pan_move)
        self.canvas_overlay.bind("<ButtonRelease-3>", self._on_pan_end)

        # Status label
        self.lbl_preview_status = ctk.CTkLabel(
            self,
            text="Detecting watermark...",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        )
        self.lbl_preview_status.pack(pady=(0, 5))

        # Bottom buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            btn_bar,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            height=36,
            width=120,
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_bar,
            text="Clear Mask",
            font=ctk.CTkFont(size=13),
            fg_color=BG_ELEVATED,
            hover_color=WARNING,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            height=36,
            width=130,
            command=self._clear_mask,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_bar,
            text="Accept Mask",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#000000",
            corner_radius=8,
            height=38,
            width=160,
            command=self._accept_mask,
        ).pack(side="right")

    def _set_draw_mode(self, mode: str):
        """Switch between add and erase drawing modes."""
        self.draw_mode = mode
        if mode == "add":
            self.btn_draw_add.configure(fg_color=ACCENT_DARK)
            self.btn_draw_erase.configure(fg_color=BG_ELEVATED)
            self.canvas_overlay.configure(cursor="crosshair")
        else:
            self.btn_draw_add.configure(fg_color=BG_ELEVATED)
            self.btn_draw_erase.configure(fg_color=DANGER)
            self.canvas_overlay.configure(cursor="circle")

    def _read_video_info(self):
        """Read video metadata (total frames, fps) for frame navigation."""
        try:
            cap = cv2.VideoCapture(self.video["path"])
            self.total_frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.current_frame_idx = self.total_frames // 2  # start at middle
            cap.release()
        except Exception:
            self.total_frames = 1
            self.current_frame_idx = 0

    def _goto_frame(self, frame_idx: int):
        """Jump to a specific frame and update the preview (keeps current mask)."""
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        self.current_frame_idx = frame_idx
        self.var_frame.set(frame_idx)
        self.lbl_frame_val.configure(text=f"{frame_idx} / {self.total_frames - 1}")

        # Read the frame in a background thread to keep UI responsive
        def read_frame():
            try:
                cap = cv2.VideoCapture(self.video["path"])
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    self.original_frame = frame
                    self.after(0, self._update_display)
            except Exception:
                pass

        threading.Thread(target=read_frame, daemon=True).start()

    def _prev_frame(self):
        """Go to the previous frame."""
        self._goto_frame(self.current_frame_idx - 1)

    def _next_frame(self):
        """Go to the next frame."""
        self._goto_frame(self.current_frame_idx + 1)

    def _run_detection(self):
        """Run watermark detection in a background thread."""
        if self._detection_running:
            return
        self._detection_running = True
        self.lbl_preview_status.configure(text="Detecting watermark...")
        self.btn_redetect.configure(state="disabled")

        def detect():
            try:
                sensitivity = self.var_preview_sensitivity.get()

                # Get the frame at the currently selected position
                cap = cv2.VideoCapture(self.video["path"])
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, self.current_frame_idx))
                ret, frame = cap.read()
                cap.release()

                if not ret:
                    self.after(
                        0,
                        lambda: self.lbl_preview_status.configure(
                            text="ERROR: Could not read video frame"
                        ),
                    )
                    self._detection_running = False
                    return

                self.original_frame = frame

                # Detect watermark
                mask = self.detector.detect(self.video["path"], sensitivity=sensitivity)
                self.current_mask = mask

                # Update display on the main thread
                self.after(0, self._update_display)
                pixel_count = int(np.sum(mask > 0))
                fidx = self.current_frame_idx
                self.after(
                    0,
                    lambda pc=pixel_count, f=fidx: self.lbl_preview_status.configure(
                        text=f"Detected {pc:,} watermark pixels (frame {f})  |  Draw on right image to add/remove"
                    ),
                )

            except Exception as e:
                self.after(
                    0,
                    lambda err=str(e): self.lbl_preview_status.configure(
                        text=f"Detection error: {err}"
                    ),
                )
            finally:
                self._detection_running = False
                self.after(0, lambda: self.btn_redetect.configure(state="normal"))

        thread = threading.Thread(target=detect, daemon=True)
        thread.start()

    def _update_display(self):
        """Update both canvases with current frame and mask, respecting zoom & pan."""
        if self.original_frame is None:
            return

        frame_rgb = cv2.cvtColor(self.original_frame, cv2.COLOR_BGR2RGB)
        h, w = frame_rgb.shape[:2]

        # Force geometry update so winfo gives real sizes
        self.update_idletasks()

        # Get actual canvas sizes
        canvas_w = self.canvas_original.winfo_width()
        canvas_h = self.canvas_original.winfo_height()
        if canvas_w < 50:
            canvas_w = 480
        if canvas_h < 50:
            canvas_h = 360

        # Calculate base scale to fit, then apply zoom
        scale_w = canvas_w / w
        scale_h = canvas_h / h
        base_scale = min(scale_w, scale_h)
        self.display_scale = base_scale * self._zoom_level

        disp_w = int(w * self.display_scale)
        disp_h = int(h * self.display_scale)

        if disp_w < 1 or disp_h < 1:
            return

        # Build overlay with mask
        overlay = frame_rgb.copy()
        if self.current_mask is not None and self.current_mask.shape[:2] == (h, w):
            mask_bool = self.current_mask > 127
            if np.any(mask_bool):
                overlay_r = overlay.copy()
                overlay_r[mask_bool, 0] = np.clip(
                    overlay_r[mask_bool, 0].astype(int) * 0.4 + 255 * 0.6, 0, 255
                ).astype(np.uint8)
                overlay_r[mask_bool, 1] = (overlay_r[mask_bool, 1] * 0.4).astype(np.uint8)
                overlay_r[mask_bool, 2] = (overlay_r[mask_bool, 2] * 0.4).astype(np.uint8)
                overlay = overlay_r
                contours, _ = cv2.findContours(
                    self.current_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)

        # Resize both images
        interp = cv2.INTER_AREA if self._zoom_level <= 1.0 else cv2.INTER_LINEAR
        frame_resized = cv2.resize(frame_rgb, (disp_w, disp_h), interpolation=interp)
        overlay_resized = cv2.resize(overlay, (disp_w, disp_h), interpolation=interp)

        # Pan offset in display pixels
        pan_dx = int(self._pan_x * self.display_scale)
        pan_dy = int(self._pan_y * self.display_scale)

        # --- Original frame ---
        self._img_original = ImageTk.PhotoImage(Image.fromarray(frame_resized))
        self.canvas_original.delete("all")
        ox = canvas_w // 2 + pan_dx
        oy = canvas_h // 2 + pan_dy
        self.canvas_original.create_image(ox, oy, image=self._img_original, anchor="center")

        # --- Overlay frame ---
        self._img_overlay = ImageTk.PhotoImage(Image.fromarray(overlay_resized))
        canvas_w2 = self.canvas_overlay.winfo_width()
        canvas_h2 = self.canvas_overlay.winfo_height()
        if canvas_w2 < 50:
            canvas_w2 = 480
        if canvas_h2 < 50:
            canvas_h2 = 360

        self.canvas_overlay.delete("all")
        ox2 = canvas_w2 // 2 + pan_dx
        oy2 = canvas_h2 // 2 + pan_dy
        self.canvas_overlay.create_image(ox2, oy2, image=self._img_overlay, anchor="center")

        # Store offsets for drawing coordinate translation
        self._img_offset_x = ox2 - disp_w // 2
        self._img_offset_y = oy2 - disp_h // 2
        self._disp_w = disp_w
        self._disp_h = disp_h

        # Show zoom level
        zoom_pct = int(self._zoom_level * 100)
        self.canvas_overlay.create_text(
            10, canvas_h2 - 10, text=f"{zoom_pct}%", fill="#00d2ff",
            font=("Consolas", 10, "bold"), anchor="sw",
        )

    def _canvas_to_mask_coords(self, cx, cy):
        """Convert canvas coordinates to mask image coordinates."""
        if self.display_scale <= 0 or self.current_mask is None:
            return None, None

        # Subtract image offset to get position relative to the displayed image
        ix = cx - self._img_offset_x
        iy = cy - self._img_offset_y

        # Check bounds on the displayed image
        if ix < 0 or iy < 0 or ix >= self._disp_w or iy >= self._disp_h:
            return None, None

        # Scale back to original mask resolution
        mx = int(ix / self.display_scale)
        my = int(iy / self.display_scale)

        # Bounds check on mask
        h, w = self.current_mask.shape
        mx = min(mx, w - 1)
        my = min(my, h - 1)

        return mx, my

    # ─── Zoom & Pan ────────────────────────────────────────────────

    def _on_zoom(self, event):
        """Mouse scroll to zoom in/out."""
        if event.delta > 0:
            self._zoom_level = min(10.0, self._zoom_level * 1.15)
        else:
            self._zoom_level = max(0.2, self._zoom_level / 1.15)
        self._update_display()

    def _on_space_press(self, event):
        """Spacebar held = pan mode."""
        if not self._space_held:
            self._space_held = True
            self.canvas_overlay.configure(cursor="fleur")

    def _on_space_release(self, event):
        """Spacebar released = back to draw mode."""
        self._space_held = False
        self._is_panning = False
        cursor = "crosshair" if self.draw_mode == "add" else "circle"
        self.canvas_overlay.configure(cursor=cursor)

    def _on_pan_start(self, event):
        """Start panning (right-click drag)."""
        self._is_panning = True
        self._pan_start_x = event.x
        self._pan_start_y = event.y

    def _on_pan_move(self, event):
        """Continue panning."""
        if self._is_panning:
            dx = event.x - self._pan_start_x
            dy = event.y - self._pan_start_y
            self._pan_start_x = event.x
            self._pan_start_y = event.y
            # Convert display pixel delta to original image pixel delta
            if self.display_scale > 0:
                self._pan_x += dx / self.display_scale
                self._pan_y += dy / self.display_scale
            self._update_display()

    def _on_pan_end(self, event):
        """Stop panning."""
        self._is_panning = False

    def _on_draw_start(self, event):
        """Start drawing on the mask."""
        # If space is held, start panning instead
        if self._space_held:
            self._is_panning = True
            self._pan_start_x = event.x
            self._pan_start_y = event.y
            return
        if self.current_mask is None:
            return
        self.is_drawing = True
        self._draw_at(event.x, event.y)

    def _on_draw_move(self, event):
        """Continue drawing on the mask."""
        # If panning with space+left-click
        if self._is_panning and self._space_held:
            dx = event.x - self._pan_start_x
            dy = event.y - self._pan_start_y
            self._pan_start_x = event.x
            self._pan_start_y = event.y
            if self.display_scale > 0:
                self._pan_x += dx / self.display_scale
                self._pan_y += dy / self.display_scale
            self._update_display()
            return
        if self.is_drawing and self.current_mask is not None:
            self._draw_at(event.x, event.y)

    def _on_draw_end(self, event):
        """Stop drawing on the mask."""
        self._is_panning = False
        self.is_drawing = False
        # Full refresh on mouse release
        self._update_display()

    def _draw_at(self, cx, cy):
        """Draw on the mask at canvas coordinates with real-time visual feedback."""
        if self.current_mask is None:
            return

        mx, my = self._canvas_to_mask_coords(cx, cy)
        if mx is None:
            return

        brush = self.var_brush.get()
        # Scale brush size to mask resolution
        mask_brush = max(1, int(brush / max(self.display_scale, 0.01)))

        color = 255 if self.draw_mode == "add" else 0
        cv2.circle(self.current_mask, (mx, my), mask_brush, color, -1)

        # Draw visual feedback circle directly on canvas (fast)
        disp_brush = max(2, brush)
        if self.draw_mode == "add":
            fill_color = "#FF000080"
            outline_color = "#00FF00"
        else:
            fill_color = ""
            outline_color = "#FF4444"

        self.canvas_overlay.create_oval(
            cx - disp_brush,
            cy - disp_brush,
            cx + disp_brush,
            cy + disp_brush,
            outline=outline_color,
            fill=fill_color if self.draw_mode == "add" else "",
            width=2,
            stipple="gray50" if self.draw_mode == "add" else "",
        )

        # Schedule a throttled display refresh (avoids redrawing every pixel)
        if not self._draw_update_pending:
            self._draw_update_pending = True
            self.after(150, self._throttled_display_update)

    def _throttled_display_update(self):
        """Throttled display update during drawing."""
        self._draw_update_pending = False
        if self.is_drawing:
            # Light update: just refresh the overlay image without full recompute
            self._update_display()

    def _clear_mask(self):
        """Clear the entire mask."""
        if self.current_mask is not None:
            self.current_mask = np.zeros_like(self.current_mask)
            self._update_display()
            self.lbl_preview_status.configure(text="Mask cleared. Draw to add mask regions.")

    def _accept_mask(self):
        """Accept the current mask and close the dialog."""
        if self.current_mask is not None:
            self.video["mask_data"] = self.current_mask.copy()
            pixel_count = int(np.sum(self.current_mask > 0))
            self.parent_app._log(
                f"Mask set for {os.path.basename(self.video['path'])} "
                f"({pixel_count:,} pixels)"
            )
            # Refresh the video list to show the ✓ Mask indicator
            self.parent_app._refresh_video_list()
        self.destroy()

# ─── Paste List Dialog ───────────────────────────────────────────────────
class PasteListDialog(ctk.CTkToplevel):
    """Dialog for pasting a list of filenames to add from a folder."""

    def __init__(self, parent: WatermarkRemoverApp):
        super().__init__(parent)

        self.parent_app = parent

        self.title("Paste Video List")
        self.geometry("700x550")
        self.configure(fg_color=BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Build the paste list dialog UI."""
        # Header
        ctk.CTkLabel(
            self,
            text="Paste Video Filenames",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Paste one filename per line. They will be resolved from the input folder below.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 10))

        # Input folder selector
        folder_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8)
        folder_frame.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            folder_frame,
            text="Input Folder:",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(12, 5), pady=10)

        self.var_input_folder = ctk.StringVar(value="")
        self.lbl_folder = ctk.CTkLabel(
            folder_frame,
            textvariable=self.var_input_folder,
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color=ACCENT,
            anchor="w",
        )
        self.lbl_folder.pack(side="left", fill="x", expand=True, padx=5, pady=10)

        ctk.CTkButton(
            folder_frame,
            text="Browse...",
            font=ctk.CTkFont(size=12),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            height=30,
            width=90,
            command=self._browse_folder,
        ).pack(side="right", padx=10, pady=10)

        # Text area for pasting filenames
        text_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8)
        text_frame.pack(fill="both", expand=True, padx=20, pady=4)

        ctk.CTkLabel(
            text_frame,
            text="FILENAMES (one per line)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.txt_filenames = ctk.CTkTextbox(
            text_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=BG_ELEVATED,
            text_color=TEXT_PRIMARY,
            corner_radius=8,
            wrap="none",
        )
        self.txt_filenames.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Status
        self.lbl_status = ctk.CTkLabel(
            self,
            text="Paste filenames and select a folder, then click Add",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
        )
        self.lbl_status.pack(pady=(4, 4))

        # Buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_bar,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color=BG_ELEVATED,
            hover_color=BORDER,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            height=36,
            width=120,
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_bar,
            text="Add Videos from List",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#000000",
            corner_radius=8,
            height=38,
            width=200,
            command=self._add_from_list,
        ).pack(side="right")

    def _browse_folder(self):
        """Browse for the input folder."""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.var_input_folder.set(folder)

    def _add_from_list(self):
        """Resolve filenames from the input folder and add to queue."""
        folder = self.var_input_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Warning", "Please select a valid input folder first.")
            return

        raw_text = self.txt_filenames.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showinfo("Info", "No filenames pasted. Paste one filename per line.")
            return

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        added = 0
        not_found = []
        duplicates = 0

        for filename in lines:
            full_path = os.path.join(folder, filename)

            if not os.path.isfile(full_path):
                not_found.append(filename)
                continue

            # Check for duplicates
            if any(v["path"] == full_path for v in self.parent_app.video_queue):
                duplicates += 1
                continue

            self.parent_app.video_queue.append(
                {
                    "path": full_path,
                    "status": "queued",
                    "mask_path": None,
                    "mask_data": None,
                    "progress": 0.0,
                }
            )
            added += 1

        # Update parent UI
        self.parent_app._refresh_video_list()

        # Log results
        status_parts = [f"Added {added} video(s)"]
        if duplicates:
            status_parts.append(f"{duplicates} duplicates skipped")
        if not_found:
            status_parts.append(f"{len(not_found)} not found")

        status = " | ".join(status_parts)
        self.lbl_status.configure(text=status, text_color=SUCCESS if added > 0 else WARNING)
        self.parent_app._log(f"Paste List: {status}")

        if not_found:
            # Show first few missing files in log
            for nf in not_found[:10]:
                self.parent_app._log(f"  NOT FOUND: {nf}")
            if len(not_found) > 10:
                self.parent_app._log(f"  ... and {len(not_found) - 10} more")

        if added > 0:
            self.after(500, self.destroy)


# ─── Entry Point ─────────────────────────────────────────────────────────
def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    app = WatermarkRemoverApp()
    app.mainloop()


if __name__ == "__main__":
    main()
