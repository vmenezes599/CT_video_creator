"""
Test script for generating video frames using Stable Diffusion and AnimateDiff
"""

def main():
    """
    Prototype for video generation using Stable Diffusion and AnimateDiff
    """
    default_positive_prompt = "cinematic animation in ultra-high detail, soft lighting, dynamic range, shallow depth of field, expressive character motion, realistic textures, golden hour glow, slow camera pan, natural background, 4k film style, "
    default_negative_prompt = "deformed, blurry, mutated, extra limbs, extra fingers, bad hands, low quality, distorted face, missing limbs, broken anatomy, fuzzy, dark, messy background, ugly, glitch, horror style, static pose, photorealistic, grayscale, "

    story = [
        (
            "Once upon a time, in a quiet village surrounded by hills, lived a curious little girl named Mia. She loved to explore and ask questions about everything she saw.",
            "cinematic animation of a young girl walking through a tranquil village nestled in rolling green hills, warm golden sunlight, stone cottages with mossy roofs, trees gently swaying, girl with curious expression wearing simple dress, early morning glow, soft painterly style",
            "blurry, distorted face, extra limbs, low resolution, bad anatomy, harsh shadows, modern buildings, crowded city, realism",
        )
    ]
    # negative_prompt=["bad quality, worse quality" for i in range(0, len(story))]


if __name__ == "__main__":
    main()