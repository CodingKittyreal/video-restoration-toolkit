"""
Batch Last Frame Extractor GUI — Extracts the last frame of all videos in a folder as PNG/JPG
Uses -sseof for reliable last-frame seeking, no ffprobe dependency.
"""
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog
import threading, time, sys, os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FFMPEG = "ffmpeg"


class LastFrameExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Last Frame Extractor")
        self.root.configure(bg="#1a1a2e")
        self.root.geometry("750x620")
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
        tk.Label(self.root, text="Batch Last Frame Extractor", font=("Segoe UI", 18, "bold"),
                 bg=bg, fg="#00d2ff").pack(pady=(10, 0))
        tk.Label(self.root, text="Extract only the last frame of all videos in an input folder",
                 font=("Segoe UI", 10), bg=bg, fg="#888").pack()

        # ─── Settings Frame ──────────────────────────────────────
        sf = tk.LabelFrame(self.root, text=" Settings ", font=("Segoe UI", 9, "bold"),
                           bg=accent, fg=fg, bd=1)
        sf.pack(fill="x", padx=12, pady=8)

        # Input folder
        rf1 = tk.Frame(sf, bg=accent)
        rf1.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(rf1, text="Input Folder:", font=("Segoe UI", 9, "bold"),
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

        # Format
        tk.Label(rf3, text="Format:", font=("Segoe UI", 9, "bold"),
                 bg=accent, fg=fg).pack(side="left")
        self.format_var = tk.StringVar(value="PNG")
        fmt_menu = ttk.Combobox(rf3, textvariable=self.format_var, width=5,
                                 values=["PNG", "JPG"], state="readonly",
                                 font=("Segoe UI", 9))
        fmt_menu.pack(side="left", padx=4)

        # ─── Stats Bar ───────────────────────────────────────────
        stf = tk.Frame(self.root, bg="#16213e", bd=1, relief="groove")
        stf.pack(fill="x", padx=12)
        self.lbl_stats = tk.Label(stf, text="Select an input folder and output folder",
                                   font=("Segoe UI", 10), bg="#16213e", fg=fg, pady=5)
        self.lbl_stats.pack(fill="x")

        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("fe.Horizontal.TProgressbar", troughcolor="#16213e",
                        background="#00b894", thickness=20)
        self.progress = ttk.Progressbar(self.root, style="fe.Horizontal.TProgressbar",
                                         mode='determinate')
        self.progress.pack(fill="x", padx=12, pady=(10, 2))

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
        self.log_text = tk.Text(lf, height=12, bg="#0d1117", fg="#c9d1d9",
                                 font=("Consolas", 9), bd=0, wrap="word")
        sb = tk.Scrollbar(lf, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.tag_configure("ok", foreground="#00b894")
        self.log_text.tag_configure("err", foreground="#e74c3c")
        self.log_text.tag_configure("info", foreground="#74b9ff")
        self.log_text.tag_configure("warn", foreground="#fdcb6e")

    # ─── Browse Dialogs ──────────────────────────────────────────
    def _browse_input(self):
        f = filedialog.askdirectory(title="Select Input Video Folder")
        if f:
            self.input_var.set(f)
            if not self.output_var.get():
                self.output_var.set(f)

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
        if not inp or not os.path.isdir(inp):
            self.ui(lambda: self.log("ERROR: Select a valid input folder", "err"))
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
        self.thread = threading.Thread(target=self.batch_process, daemon=True)
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

    # ─── Batch Processing Loop ───────────────────────────────────
    def batch_process(self):
        input_dir = Path(self.input_var.get().strip())
        output_dir = Path(self.output_var.get().strip())
        fmt = self.format_var.get()

        output_dir.mkdir(parents=True, exist_ok=True)

        # Scan for video files
        video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        video_files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() in video_extensions])
        total_videos = len(video_files)

        if total_videos == 0:
            self.ui(lambda: self.log(f"ERROR: No matching video files found in {input_dir}", "err"))
            self.ui(self._done)
            return

        self.ui(lambda: self.log(f"Starting batch extraction of last frames. Found {total_videos} videos.", "info"))
        self.ui(lambda: self.progress.config(maximum=total_videos, value=0))

        ext = ".png" if fmt == "PNG" else ".jpg"
        skipped = 0
        created = 0
        failed = 0

        for idx, video_path in enumerate(video_files, 1):
            if self.stop_flag:
                break
            while self.paused and not self.stop_flag:
                time.sleep(0.2)
            if self.stop_flag:
                break

            out_name = f"{video_path.stem}{ext}"
            out_path = output_dir / out_name

            if out_path.exists():
                skipped += 1
                self.ui(lambda i=idx, n=out_name: self.log(f"  [{i}/{total_videos}] SKIP (exists): {n}"))
                self.ui(lambda v=idx, c=created, s=skipped, f=failed: [
                    self.progress.config(value=v),
                    self.lbl_stats.config(text=f"Processed: {v}/{total_videos} | Created: {c} | Skipped: {s} | Failed: {f}")])
                continue

            # Use -sseof to seek from the end (no ffprobe needed)
            # Convert paths to strings with proper Windows backslashes
            input_str = str(video_path.resolve())
            output_str = str(out_path.resolve())

            cmd = [
                FFMPEG, "-y",
                "-sseof", "-0.1",
                "-i", input_str,
                "-update", "1",
                "-frames:v", "1",
                "-q:v", "2",
                output_str,
            ]

            try:
                r = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                stderr_text = r.stderr.decode('utf-8', errors='replace') if r.stderr else ""
            except subprocess.TimeoutExpired:
                failed += 1
                self.ui(lambda i=idx, n=video_path.name: self.log(f"  [{i}/{total_videos}] FAIL (timeout): {n}", "err"))
                continue
            except Exception as e:
                failed += 1
                self.ui(lambda i=idx, n=video_path.name, err=str(e): self.log(f"  [{i}/{total_videos}] FAIL ({err}): {n}", "err"))
                continue

            if out_path.exists():
                created += 1
                self.ui(lambda i=idx, n=out_name: self.log(f"  [{i}/{total_videos}] OK: {n}", "ok"))
            else:
                failed += 1
                # Log the actual ffmpeg error so we can see what went wrong
                err_lines = [l for l in stderr_text.splitlines() if l.strip() and not l.strip().startswith(('configuration:', 'lib', 'built with', 'ffmpeg version', '--enable'))]
                err_summary = err_lines[-3:] if err_lines else ["Unknown error"]
                self.ui(lambda i=idx, n=video_path.name: self.log(f"  [{i}/{total_videos}] FAIL: {n}", "err"))
                for line in err_summary:
                    self.ui(lambda l=line: self.log(f"    >> {l.strip()}", "warn"))

            self.ui(lambda v=idx, c=created, s=skipped, f=failed: [
                self.progress.config(value=v),
                self.lbl_stats.config(text=f"Processed: {v}/{total_videos} | Created: {c} | Skipped: {s} | Failed: {f}")])

        if self.stop_flag:
            self.ui(lambda: self.log("\nBatch extraction STOPPED.", "err"))
            self.ui(lambda: self.lbl_stats.config(text="Stopped by user"))
        else:
            self.ui(lambda: self.log(f"\nDone! Created: {created} | Skipped: {skipped} | Failed: {failed}", "ok"))
            self.ui(lambda: self.lbl_stats.config(text=f"Complete! Created: {created} | Skipped: {skipped}"))
        self.ui(self._done)


if __name__ == "__main__":
    root = tk.Tk()
    app = LastFrameExtractorApp(root)
    root.mainloop()
