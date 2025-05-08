"""
AI Image Generation Module
"""

from .ai_image_generator import FluxAIImageGenerator


# Example usage
if __name__ == "__main__":
    # Define the output folder
    output_folder = "outputs/generated_images"

    # Create an instance of AIImageGenerator
    generator = FluxAIImageGenerator(output_folder)

    # List of prompts to generate images for
    prompts = [
        "A serene village surrounded by mountains during sunrise, soft light, painterly style.",
        "A futuristic cityscape with flying cars and neon lights, cyberpunk theme.",
        "A magical forest with glowing trees and mystical creatures, fantasy ambiance.",
        "A cozy cabin in the snow with smoke coming from the chimney, warm and inviting.",
    ]

    # Generate images and get their paths
    image_paths = generator.generate_images(prompts)

    # Print the paths to the generated images
    print("Generated image paths:")
    for path in image_paths:
        print(path)