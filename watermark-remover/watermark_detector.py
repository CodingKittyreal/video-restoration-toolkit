"""
Automatic Watermark Detection Module
=====================================
Detects static watermarks in videos using temporal variance analysis
combined with edge detection. Watermarks are static overlays that remain
in the same position across frames while video content changes.

Algorithm:
1. Sample diverse frames across the video timeline
2. Compute per-pixel temporal variance (static regions = low variance)
3. Detect edges on the median frame (watermarks have text/logo edges)
4. Combine: static regions WITH edges = watermark candidates
5. Morphological cleanup + contour filtering
6. Corner/edge bias (watermarks are usually in corners)
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List


class WatermarkDetector:
    """Detects and generates masks for static watermarks in videos."""

    def __init__(
        self,
        num_samples: int = 80,
        variance_threshold: float = 12.0,
        edge_low: int = 40,
        edge_high: int = 120,
        min_contour_area: int = 150,
        max_contour_area_ratio: float = 0.15,
        dilation_iterations: int = 6,
        dilation_kernel_size: int = 7,
        corner_bias_weight: float = 1.5,
        corner_region_ratio: float = 0.25,
    ):
        """
        Initialize the watermark detector.

        Args:
            num_samples: Number of frames to sample from the video.
            variance_threshold: Threshold for static region detection (lower = more sensitive).
            edge_low: Canny edge detection low threshold.
            edge_high: Canny edge detection high threshold.
            min_contour_area: Minimum contour area to consider as watermark.
            max_contour_area_ratio: Maximum ratio of frame area a watermark can occupy.
            dilation_iterations: Number of dilation iterations for mask expansion.
            dilation_kernel_size: Kernel size for dilation.
            corner_bias_weight: Weight multiplier for corner/edge regions.
            corner_region_ratio: Fraction of frame width/height considered as corner region.
        """
        self.num_samples = num_samples
        self.variance_threshold = variance_threshold
        self.edge_low = edge_low
        self.edge_high = edge_high
        self.min_contour_area = min_contour_area
        self.max_contour_area_ratio = max_contour_area_ratio
        self.dilation_iterations = dilation_iterations
        self.dilation_kernel_size = dilation_kernel_size
        self.corner_bias_weight = corner_bias_weight
        self.corner_region_ratio = corner_region_ratio

    def detect(self, video_path: str, sensitivity: float = 1.0) -> np.ndarray:
        """
        Detect watermark in a video and return a binary mask.

        Args:
            video_path: Path to the input video file.
            sensitivity: Sensitivity multiplier (higher = more aggressive detection).
                         1.0 = default, 2.0 = very aggressive, 0.5 = conservative.

        Returns:
            Binary mask (numpy array) where 255 = watermark region, 0 = keep.
        """
        # Adjust threshold based on sensitivity
        adjusted_threshold = self.variance_threshold / sensitivity

        # Sample frames
        frames_gray, frames_color = self._sample_frames(video_path)

        if len(frames_gray) < 5:
            raise ValueError(
                f"Could not sample enough frames from '{video_path}'. "
                f"Got {len(frames_gray)}, need at least 5."
            )

        frame_stack = np.array(frames_gray, dtype=np.float32)
        h, w = frame_stack.shape[1], frame_stack.shape[2]

        # Step 1: Temporal variance — find static regions
        variance_map = self._compute_variance(frame_stack)

        # Step 2: Threshold variance to get static mask
        static_mask = self._threshold_variance(variance_map, adjusted_threshold)

        # Step 3: Edge detection on median frame
        median_frame = np.median(frame_stack, axis=0).astype(np.uint8)
        edges = cv2.Canny(median_frame, self.edge_low, self.edge_high)

        # Step 4: Dilate edges to connect nearby edges
        edge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges_dilated = cv2.dilate(edges, edge_kernel, iterations=2)

        # Step 5: Combine static regions with edges
        watermark_mask = cv2.bitwise_and(static_mask, edges_dilated)

        # Step 6: Apply corner/edge bias
        watermark_mask = self._apply_corner_bias(watermark_mask, h, w)

        # Step 7: Morphological cleanup
        watermark_mask = self._morphological_cleanup(watermark_mask)

        # Step 8: Filter contours by area
        watermark_mask = self._filter_contours(watermark_mask, h, w)

        # Step 9: Final dilation to ensure full watermark coverage
        final_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.dilation_kernel_size, self.dilation_kernel_size),
        )
        watermark_mask = cv2.dilate(
            watermark_mask, final_kernel, iterations=self.dilation_iterations
        )

        return watermark_mask

    def preview(
        self, video_path: str, sensitivity: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate a preview of the watermark detection.

        Args:
            video_path: Path to the input video file.
            sensitivity: Detection sensitivity multiplier.

        Returns:
            Tuple of (original_frame, binary_mask, overlay_frame).
            overlay_frame shows the detected watermark highlighted in red on the original frame.
        """
        # Get a representative frame (from the middle of the video)
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
        ret, original_frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError(f"Could not read frame from '{video_path}'")

        # Detect watermark
        mask = self.detect(video_path, sensitivity=sensitivity)

        # Create overlay
        overlay = original_frame.copy()
        # Red highlight on watermark regions
        red_overlay = np.zeros_like(overlay)
        red_overlay[:, :, 2] = 255  # Red channel
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) // 255
        overlay = cv2.addWeighted(
            overlay, 1.0, (red_overlay * mask_3ch).astype(np.uint8), 0.5, 0
        )

        # Draw contour outlines in bright green
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)

        return original_frame, mask, overlay

    def _sample_frames(
        self, video_path: str
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Sample frames spread across the video timeline."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise ValueError(f"Video has no frames: {video_path}")

        # Calculate sample indices spread across the video
        # Skip first and last 2% to avoid intro/outro
        start_idx = max(0, int(total_frames * 0.02))
        end_idx = min(total_frames - 1, int(total_frames * 0.98))
        num_to_sample = min(self.num_samples, end_idx - start_idx)

        if num_to_sample <= 0:
            # Very short video, sample what we can
            sample_indices = list(range(min(total_frames, self.num_samples)))
        else:
            sample_indices = np.linspace(
                start_idx, end_idx, num_to_sample, dtype=int
            ).tolist()

        frames_gray = []
        frames_color = []

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames_color.append(frame)
                frames_gray.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

        cap.release()
        return frames_gray, frames_color

    def _compute_variance(self, frame_stack: np.ndarray) -> np.ndarray:
        """Compute per-pixel temporal variance across sampled frames."""
        variance = np.var(frame_stack, axis=0)
        return variance

    def _threshold_variance(
        self, variance_map: np.ndarray, threshold: float
    ) -> np.ndarray:
        """
        Create a binary mask of static regions (low variance).

        Uses percentile-based normalization to handle different video types.
        """
        # Normalize variance using the 95th percentile for robustness
        p95 = np.percentile(variance_map, 95)
        if p95 < 1.0:
            # Entire frame is nearly static (e.g., still image)
            # Use absolute threshold
            normalized = variance_map
        else:
            normalized = (variance_map / p95) * 100.0

        # Threshold: regions below threshold are considered static
        static_mask = np.where(normalized < threshold, 255, 0).astype(np.uint8)

        return static_mask

    def _apply_corner_bias(
        self, mask: np.ndarray, h: int, w: int
    ) -> np.ndarray:
        """
        Apply higher weight to corner/edge regions of the frame.
        Watermarks are typically placed in corners or along edges.
        """
        # Create a weight map that's higher at corners/edges
        weight_map = np.ones((h, w), dtype=np.float32)
        ch = int(h * self.corner_region_ratio)
        cw = int(w * self.corner_region_ratio)

        # Boost corners
        weight_map[:ch, :cw] = self.corner_bias_weight       # Top-left
        weight_map[:ch, w - cw :] = self.corner_bias_weight   # Top-right
        weight_map[h - ch :, :cw] = self.corner_bias_weight   # Bottom-left
        weight_map[h - ch :, w - cw :] = self.corner_bias_weight  # Bottom-right

        # Boost edges (but less than corners)
        edge_weight = (self.corner_bias_weight + 1.0) / 2.0
        weight_map[:ch, :] = np.maximum(weight_map[:ch, :], edge_weight)   # Top edge
        weight_map[h - ch :, :] = np.maximum(weight_map[h - ch :, :], edge_weight)  # Bottom edge
        weight_map[:, :cw] = np.maximum(weight_map[:, :cw], edge_weight)   # Left edge
        weight_map[:, w - cw :] = np.maximum(weight_map[:, w - cw :], edge_weight)  # Right edge

        # Apply weight — for the mask, this effectively makes corner detections
        # survive while center detections need stronger evidence
        weighted = mask.astype(np.float32) * weight_map
        _, biased_mask = cv2.threshold(
            weighted.astype(np.uint8), 127, 255, cv2.THRESH_BINARY
        )

        return biased_mask

    def _morphological_cleanup(self, mask: np.ndarray) -> np.ndarray:
        """Clean up the mask using morphological operations."""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

        # Close small gaps within the watermark region
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)

        # Remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        return mask

    def _filter_contours(
        self, mask: np.ndarray, h: int, w: int
    ) -> np.ndarray:
        """Filter contours by area to remove noise and overly large detections."""
        frame_area = h * w
        max_area = frame_area * self.max_contour_area_ratio

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        filtered_mask = np.zeros_like(mask)
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_contour_area <= area <= max_area:
                cv2.drawContours(filtered_mask, [contour], -1, 255, -1)

        return filtered_mask

    def get_video_info(self, video_path: str) -> dict:
        """Get basic video information."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            / max(cap.get(cv2.CAP_PROP_FPS), 1),
        }
        cap.release()
        return info
