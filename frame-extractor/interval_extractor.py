"""
Frame Extractor GUI — Extract every Nth frame from a video as PNG/JPG
"""
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog
import threading, time, sys, os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class FrameExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Frame Extractor")
        self.root.configure(bg="#1a1a2e")
        self.root.geometry("700x580")
        self.root.resizable(True, True)

        self.running = False
        self.paused = False
        self.stop_flag = False
        self.thread = None

        self._build_ui()

    def _build_ui(self):
        bg = "#1a1a2e"
        fg = "#e0e0e0"
        accent = "#0f3460"
        entry_bg = "#16213e"

        # Title
        tk.Label(self.root, text="Frame Extractor", font=("Segoe UI", 18, "bold"),
                 bg=bg, fg="#00d2ff").pack(pady=(10, 0))
        tk.Label(self.root, text="Extract every Nth frame from video as PNG or JPG",
                 font=("Segoe UI", 10), bg=bg, fg="#888").pack()

        # ─── Settings Frame ──────────────────────────────────────
        sf = tk.LabelFrame(self.root, text=" Settings ", font=("Segoe UI", 9, "bold"),
                           bg=accent, fg=fg, bd=1)
        sf.pack(fill="x", padx=12, pady=8)

        # Input video
        rf1 = tk.Frame(sf, bg=accent)
        rf1.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(rf1, text="Input Video:", font=("Segoe UI", 9, "bold"),
                 bg=accent, fg=fg, width=12, anchor="w").pack(side="left")
        self.input_var = tk.StringVar()
        tk.Entry(rf1, textvariable=self.input_var, font=("Consolas", 9),
                 bg=entry_bg, fg=fg, bd=0, insertbackground=fg).pack(side="left", fill="x", expand=True, padx=4)
        tk.Button(rf1, text="Browse", font=("Segoe UI", 8), bg="#16213e", fg=fg, bd=0,
                  command=self._browse_input, width=7).pack(side="right")

        # Output folder
        rf2 = tk.Frame(sf, bg=accent)
        rf2.pack(fill="x", padx=8, pady=2)
        tk.Label(rf2, text="Output Folder:", font=("Segoe UI", 9, "bold"),
                 bg=accent, fg=fg, width=12, anchor="w").pack(side="left")
        self.output_var = tk.StringVar()
        tk.Entry(rf2, textvariable=self.output_var, font=("Consolas", 9),
                 bg=entry_bg, fg=fg, bd=0, insertbackground=fg).pack(side="left", fill="x", expand=True, padx=4)
        tk.Button(rf2, text="Browse", font=("Segoe UI", 8), bg="#16213e", fg=fg, bd=0,
                  command=self._browse_output, width=7).pack(side="right")

        # Options row
        rf3 = tk.Frame(sf, bg=accent)
        rf3.pack(fill="x", padx=8, pady=(6, 8))

        # Frame interval
        tk.Label(rf3, text="Extract every:", font=("Segoe UI", 9, "bold"),
                 bg=accent, fg=fg).pack(side="left")
        self.interval_var = tk.IntVar(value=2)
        interval_menu = ttk.Combobox(rf3, textvariable=self.interval_var, width=4,
                                      values=[1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 24, 30],
                                      state="readonly", font=("Segoe UI", 9))
        interval_menu.pack(side="left", padx=4)
        tk.Label(rf3, text="frame(s)", font=("Segoe UI", 9),
                 bg=accent, fg="#aaa").pack(side="left")

        # Spacer
        tk.Label(rf3, text="    ", bg=accent).pack(side="left")

        # Format
        tk.Label(rf3, text="Format:", font=("Segoe UI", 9, "bold"),
                 bg=accent, fg=fg).pack(side="left")
        self.format_var = tk.StringVar(value="PNG")
        fmt_menu = ttk.Combobox(rf3, textvariable=self.format_var, width=5,
                                 values=["PNG", "JPG"], state="readonly",
                                 font=("Segoe UI", 9))
        fmt_menu.pack(side="left", padx=4)

        # Spacer
        tk.Label(rf3, text="    ", bg=accent).pack(side="left")

        # JPG quality
        tk.Label(rf3, text="JPG Quality:", font=("Segoe UI", 9, "bold"),
                 bg=accent, fg=fg).pack(side="left")
        self.quality_var = tk.IntVar(value=100)
        tk.Spinbox(rf3, from_=50, to=100, textvariable=self.quality_var, width=4,
                   font=("Segoe UI", 9), bg=entry_bg, fg=fg, bd=0,
                   buttonbackground=accent).pack(side="left", padx=4)

        # ─── Stats Bar ───────────────────────────────────────────
        stf = tk.Frame(self.root, bg="#16213e", bd=1, relief="groove")
        stf.pack(fill="x", padx=12)
        self.lbl_stats = tk.Label(stf, text="Select a video and output folder",
                                   font=("Segoe UI", 10), bg="#16213e", fg=fg, pady=5)
        self.lbl_stats.pack(fill="x")

        # Progress
        style = ttk.Style()
        style.theme_use('default')
        style.configure("fe.Horizontal.TProgressbar", troughcolor="#16213e",
                        background="#00b894", thickness=20)
        self.progress = ttk.Progressbar(self.root, style="fe.Horizontal.TProgressbar",
                                         mode='determinate')
        self.progress.pack(fill="x", padx=12, pady=(4, 2))

        # ─── Buttons ─────────────────────────────────────────────
        bf = tk.Frame(self.root, bg=bg)
        bf.pack(pady=6)
        self.btn_start = tk.Button(bf, text="Start", width=12, font=("Segoe UI", 11, "bold"),
                                    bg="#00b894", fg="white", bd=0, command=self.start)
        self.btn_start.pack(side="left", padx=4)
        self.btn_pause = tk.Button(bf, text="Pause", width=12, font=("Segoe UI", 11, "bold"),
                                    bg="#f39c12", fg="white", bd=0, command=self.pause, state="disabled")
        self.btn_pause.pack(side="left", padx=4)
        self.btn_stop = tk.Button(bf, text="Stop", width=12, font=("Segoe UI", 11, "bold"),
                                   bg="#e74c3c", fg="white", bd=0, command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=4)

        # ─── Log ─────────────────────────────────────────────────
        lf = tk.Frame(self.root, bg=bg)
        lf.pack(fill="both", expand=True, padx=12, pady=(2, 10))
        self.log_text = tk.Text(lf, height=10, bg="#0d1117", fg="#c9d1d9",
                                 font=("Consolas", 9), bd=0, wrap="word")
        sb = tk.Scrollbar(lf, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.tag_configure("ok", foreground="#00b894")
        self.log_text.tag_configure("err", foreground="#e74c3c")
        self.log_text.tag_configure("info", foreground="#74b9ff")

    # ─── Browse Dialogs ──────────────────────────────────────────
    def _browse_input(self):
        f = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv *.webm"), ("All", "*.*")])
        if f:
            self.input_var.set(f)
            # Auto-set output folder
            if not self.output_var.get():
                stem = Path(f).stem
                out = str(Path(f).parent / f"{stem}_frames")
                self.output_var.set(out)

    def _browse_output(self):
        f = filedialog.askdirectory(title="Select Output Folder")
        if f:
            self.output_var.set(f)

    # ─── Logging ─────────────────────────────────────────────────
    def log(self, msg, tag=""):
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")

    def ui(self, func):
        self.root.after(0, func)

    # ─── Controls ────────────────────────────────────────────────
    def start(self):
        if self.running and self.paused:
            self.paused = False
            self.btn_pause.config(text="Pause", state="normal")
            self.btn_start.config(state="disabled")
            self.ui(lambda: self.log("[RESUMED]", "info"))
            return

        # Validate
        inp = self.input_var.get().strip()
        out = self.output_var.get().strip()
        if not inp or not os.path.isfile(inp):
            self.ui(lambda: self.log("ERROR: Select a valid video file", "err"))
            return
        if not out:
            self.ui(lambda: self.log("ERROR: Select an output folder", "err"))
            return

        self.running = True
        self.paused = False
        self.stop_flag = False
        self.btn_start.config(text="Resume", state="disabled")
        self.btn_pause.config(state="normal")
        self.btn_stop.config(state="normal")
        self.thread = threading.Thread(target=self.extract_frames, daemon=True)
        self.thread.start()

    def pause(self):
        if self.running and not self.paused:
            self.paused = True
            self.btn_pause.config(text="Paused", state="disabled")
            self.btn_start.config(text="Resume", state="normal")
            self.ui(lambda: self.log("[PAUSED]", "info"))

    def stop(self):
        self.stop_flag = True
        self.running = False
        self.paused = False
        self.btn_start.config(text="Start", state="normal")
        self.btn_pause.config(text="Pause", state="disabled")
        self.btn_stop.config(state="disabled")
        self.ui(lambda: self.log("[STOPPED]", "info"))

    def _done(self):
        self.running = False
        self.btn_start.config(text="Start", state="normal")
        self.btn_pause.config(text="Pause", state="disabled")
        self.btn_stop.config(state="disabled")

    # ─── Frame Extraction ────────────────────────────────────────
    def extract_frames(self):
        video_path = self.input_var.get().strip()
        output_dir = Path(self.output_var.get().strip())
        interval = self.interval_var.get()
        fmt = self.format_var.get()
        quality = self.quality_var.get()

        output_dir.mkdir(parents=True, exist_ok=True)

        # Open video with unicode-safe method
        cap = None
        try:
            data = np.fromfile(video_path, dtype=np.uint8)
            # Write to temp file if unicode path
            if not video_path.isascii():
                import tempfile, shutil
                tmp = Path(output_dir) / "_temp_video" + Path(video_path).suffix
                shutil.copy2(video_path, str(tmp))
                cap = cv2.VideoCapture(str(tmp))
            else:
                cap = cv2.VideoCapture(video_path)
        except:
            cap = cv2.VideoCapture(video_path)

        if not cap or not cap.isOpened():
            self.ui(lambda: self.log("ERROR: Cannot open video", "err"))
            self.ui(self._done)
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frames_to_extract = total_frames // interval
        stem = Path(video_path).stem

        ext = ".png" if fmt == "PNG" else ".jpg"

        self.ui(lambda: self.log(f"Video: {Path(video_path).name}", "info"))
        self.ui(lambda: self.log(f"Resolution: {width}x{height} | FPS: {fps:.1f} | Frames: {total_frames}", "info"))
        self.ui(lambda: self.log(f"Extracting every {interval} frame(s) -> ~{frames_to_extract} images ({fmt})", "info"))
        self.ui(lambda: self.log(f"Output: {output_dir}\n", "info"))
        self.ui(lambda: self.progress.config(maximum=frames_to_extract, value=0))

        frame_num = 0
        saved = 0
        skipped = 0

        while True:
            if self.stop_flag:
                break
            while self.paused and not self.stop_flag:
                time.sleep(0.2)
            if self.stop_flag:
                break

            ret, frame = cap.read()
            if not ret:
                break

            if frame_num % interval == 0:
                out_name = f"{stem}_frame{frame_num:06d}{ext}"
                out_path = output_dir / out_name

                if out_path.exists():
                    skipped += 1
                else:
                    # Encode and save (unicode-safe)
                    if fmt == "PNG":
                        params = [cv2.IMWRITE_PNG_COMPRESSION, 1]  # 1 = fast, minimal compression
                    else:
                        params = [cv2.IMWRITE_JPEG_QUALITY, quality]

                    success, encoded = cv2.imencode(ext, frame, params)
                    if success:
                        encoded.tofile(str(out_path))
                        saved += 1
                    else:
                        self.ui(lambda n=out_name: self.log(f"  FAIL: {n}", "err"))

                count = saved + skipped
                if count % 50 == 0 or count == frames_to_extract:
                    self.ui(lambda c=count, s=saved, sk=skipped:
                        [self.progress.config(value=c),
                         self.lbl_stats.config(text=f"Saved: {s} | Skipped: {sk} | Frame: {c}/{frames_to_extract}")])

                if saved % 200 == 0 and saved > 0:
                    self.ui(lambda s=saved: self.log(f"  {s} frames saved...", "ok"))

            frame_num += 1

        cap.release()

        # Clean up temp file if created
        tmp_file = output_dir / ("_temp_video" + Path(video_path).suffix)
        if tmp_file.exists():
            try: tmp_file.unlink()
            except: pass

        self.ui(lambda: self.log(f"\nDone! Saved: {saved} | Skipped: {skipped}", "ok"))
        self.ui(lambda: self.lbl_stats.config(text=f"Complete! {saved} frames saved to {output_dir.name}"))
        self.ui(self._done)


if __name__ == "__main__":
    root = tk.Tk()
    app = FrameExtractorApp(root)
    root.mainloop()
