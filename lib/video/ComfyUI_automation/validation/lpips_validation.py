import os
import lpips
from PIL import Image
from torchvision import transforms

# Load LPIPS model
loss_fn = lpips.LPIPS(net='alex')  # 'alex', 'vgg', or 'squeeze'
transform = transforms.Compose([
    transforms.Resize((256, 256)),  # Required size for LPIPS
    transforms.ToTensor()
])

def image_to_tensor(image_path):
    img = Image.open(image_path).convert("RGB")
    return transform(img).unsqueeze(0)

def compute_lpips_between_frames(frame1_path, frame2_path):
    img1 = image_to_tensor(frame1_path)
    img2 = image_to_tensor(frame2_path)

    distance = loss_fn(img1, img2)
    return distance.item()

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_frames_path = os.path.join(script_dir, "test", "test_frames", "good")

    # Iterate through all subdirectories in the base_frames_path
    for folder_name in os.listdir(base_frames_path):
        folder_path = os.path.join(base_frames_path, folder_name)
        
        frames = sorted(
            [f for f in os.listdir(folder_path) if f.endswith(".jpg") or f.endswith(".png")]
        )

        if len(frames) == 0:
            print("No frames found in the directory.")
            break

        for i in range(len(frames) - 1):
            frame1_path = os.path.join(folder_path, frames[i])
            frame2_path = os.path.join(folder_path, frames[i + 1])

            lpips_score = compute_lpips_between_frames(frame1_path, frame2_path)

            if lpips_score <= 0.10:
                print("✅ Pass: Very high perceptual similarity")
            elif lpips_score <= 0.25:
                print("⚠️  Acceptable, but has some noticeable visual difference")
            else:
                print("❌ Fail: Major quality/perceptual mismatch between frames")
