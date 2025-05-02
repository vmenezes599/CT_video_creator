"""
SSIM Validation for Video Frames
"""

import os
from typing import List

import cv2
import numpy as np
import PIL.Image
from skimage.metrics import structural_similarity as ssim


def ssim_validation(frames: List[PIL.Image.Image]) -> float:
    """
    Compute the average SSIM score for a sequence of frames.

    Args:
        frames (List[PIL.Image.Image]): List of PIL Image objects.

    Returns:
        float: Average SSIM score for the sequence of frames.
    """
    scores = []

    for i in range(len(frames) - 1):
        # Convert PIL Images to numpy arrays
        frame1 = cv2.cvtColor(np.array(frames[i]), cv2.COLOR_RGB2GRAY)
        frame2 = cv2.cvtColor(np.array(frames[i + 1]), cv2.COLOR_RGB2GRAY)

        # Compute SSIM between consecutive frames
        score, _ = ssim(frame1, frame2, full=True)
        scores.append(score)

    # Compute the average SSIM score
    avg_score = sum(scores) / len(scores) if scores else 0.0
    return avg_score


def ssim_validation_dir(frames_dir) -> float:
    """
    Compute the average SSIM score for a sequence of frames saved in PNG or JPG inside a folder.

    Args:
        frames_dir (str): Path to the directory containing frames.

    Returns:
        float: Average SSIM score for the sequence of frames. Returns 0.0 if no frames are found.
    """

    frames = sorted(
        [f for f in os.listdir(frames_dir) if f.endswith(".jpg") or f.endswith(".png")]
    )

    if len(frames) == 0:
        print("No frames found in the directory.")
        return 0.0

    scores = []

    for i in range(len(frames) - 1):
        frame1 = cv2.imread(os.path.join(frames_dir, frames[i]))
        frame2 = cv2.imread(os.path.join(frames_dir, frames[i + 1]))

        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        score, _ = ssim(gray1, gray2, full=True)
        scores.append(score)

    avg_score = sum(scores) / len(scores) if scores else 0.0
    return avg_score


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_frames_path = os.path.join(script_dir, "test", "test_frames", "good")

    # Iterate through all subdirectories in the base_frames_path
    for folder_name in os.listdir(base_frames_path):
        folder_path = os.path.join(base_frames_path, folder_name)

        # Check if it's a directory
        if os.path.isdir(folder_path):
            print(f"\n📂 Processing folder: {folder_name}")

            # Compute SSIM score for the folder
            ssim_score = ssim_validation_dir(folder_path)
            print(f"🧪 SSIM Score for {folder_name}: {ssim_score:.3f}")

            # Print results based on the SSIM score
            if ssim_score >= 0.90:
                print("✅ Pass: Good temporal consistency")
            elif ssim_score >= 0.85:
                print("⚠️  Warning: Minor flicker or motion artifacts")
            else:
                print("❌ Fail: Likely unstable or low-quality animation")
