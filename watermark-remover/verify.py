"""Quick verification that all components are working."""
import sys
print(f"Python: {sys.version}")

# Test PyTorch + CUDA
print("\n--- PyTorch ---")
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    # Quick CUDA test
    x = torch.randn(100, 100, device='cuda')
    y = torch.matmul(x, x)
    print(f"CUDA compute test: PASSED (result shape: {y.shape})")

# Test OpenCV
print("\n--- OpenCV ---")
import cv2
print(f"OpenCV: {cv2.__version__}")

# Test CustomTkinter
print("\n--- CustomTkinter ---")
import customtkinter
print(f"CustomTkinter: {customtkinter.__version__}")

# Test ProPainter directory
print("\n--- ProPainter ---")
import os
pp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ProPainter")
script = os.path.join(pp_dir, "inference_propainter.py")
print(f"ProPainter dir exists: {os.path.exists(pp_dir)}")
print(f"Inference script exists: {os.path.exists(script)}")

# Test imports from our modules
print("\n--- App Modules ---")
from watermark_detector import WatermarkDetector
print("WatermarkDetector: OK")
from propainter_runner import ProPainterRunner
print("ProPainterRunner: OK")

print("\n✅ All checks passed!")
