"""
Realistic Vision Sweep Automation for ComfyUI
"""

import sys

from .features.environment_variables import CONFYUI_URL
from .features.comfyui_workflow import StableDiffusionWorkflow
from .features.comfyui_requests import ComfyUIRequests


def stable_diffusion_history_maker() -> None:
    """
    Automate the sweep process for Realistic Vision in ComfyUI.
    """
    workflow = StableDiffusionWorkflow()

    requests = ComfyUIRequests(CONFYUI_URL)
    
    story = [
        (
            "Once upon a time, in a quiet village surrounded by hills, lived a curious little girl named Mia. She loved to explore and ask questions about everything she saw.",
            "cinematic animation of a young girl walking through a tranquil village nestled in rolling green hills, warm golden sunlight, stone cottages with mossy roofs, trees gently swaying, girl with curious expression wearing simple dress, early morning glow, soft painterly style",
            "blurry, distorted face, extra limbs, low resolution, bad anatomy, harsh shadows, modern buildings, crowded city, realism",
        ),
        (
            "One sunny morning, Mia found a glowing pebble near the river. It shimmered in shades of blue and green, unlike any rock she had ever seen.",
            "close-up of a young girl kneeling by a sparkling river, holding a glowing blue-green pebble, water flowing gently, reflections dancing on her face, enchanted forest backdrop, magical lighting, soft fantasy ambiance",
            "oversaturated colors, harsh lighting, futuristic elements, low detail, floating artifacts, broken fingers, unnatural poses",
        ),
        (
            "Excited, she ran home to show her grandmother. Her grandmother’s eyes widened, and she whispered, 'That looks like a stone from the Whispering Forest.'",
            "cozy cottage interior with soft light filtering through windows, wooden walls, shelves with herbs and jars, young girl showing glowing pebble to an old woman with gray hair and kind eyes, both smiling, candlelight ambiance, warm magical mood",
            "blurry background, dark and scary tones, glitch effects, modern furniture, horror elements, deformed faces, missing limbs",
        ),
        (
            "Mia had heard stories about the forest, where trees whispered secrets and animals could talk. Most villagers were too afraid to go near it.",
            "wide shot of a mystical forest with towering ancient trees, glowing mist floating through the air, whispers as glowing lines or particles, soft wind moving leaves, magical creatures hiding in shadows, dreamy and mysterious vibe",
            "dull lighting, chaotic composition, robotic elements, empty forest, low contrast, sci-fi objects, violent themes",
        ),
        (
            "But Mia was brave. The next day, she packed a small bag with snacks, water, and the pebble, and set off toward the Whispering Forest.",
            "animated scene of a determined young girl walking toward an enchanted forest at dawn, soft light from sunrise, small satchel on her shoulder, glowing pebble in her hand, forest glowing faintly in the distance, hopeful and adventurous tone",
            "dark environment, rainy weather, sad expression, empty background, futuristic style, horror themes, poor lighting",
        ),
        (
            "As she stepped inside, the trees rustled gently. A squirrel hopped down and said, 'Welcome, Mia. We’ve been waiting for you.'",
            "lush forest entrance with magical trees moving slowly, a squirrel with expressive eyes talking to the girl from a tree branch, glowing particles floating in the air, forest bathed in soft green and gold light, girl looking surprised but happy, fairytale atmosphere",
            "monochrome, broken lighting, horror style animals, static poses, dark forest, evil tones, sci-fi armor",
        ),
        (
            "The forest was full of magic. Birds sang tunes that shaped the wind, and flowers opened to greet her. She felt like she belonged.",
            "fantasy forest alive with magic, animated birds flying in colorful flocks, gentle wind swirling with glowing lines, flowers blooming as the girl walks by, vibrant colors, enchanted harmony, soft motion and dreamlike quality",
            "glitchy animation, robotic birds, dry forest, dull colors, dark tone, aggressive expressions, unnatural motion blur",
        ),
        (
            "By sunset, Mia had made many new friends. She promised to return and share their stories with the village. From that day on, the forest and the village became connected through Mia's courage.",
            "sunset scene with golden sky over village and forest edge, girl walking back with a smile, magical creatures waving goodbye, soft sunlight bathing the path, forest and village blending in harmony, emotional and warm conclusion",
            "night scene, sad tone, broken animation, cold colors, lonely atmosphere, blurry characters, post-apocalyptic setting",
        ),
    ]
    
    for s in story:
        workflow.set_positive_prompt(s[1])
        requests.comfyui_send_prompt(workflow.get_json())


if __name__ == "__main__":
    try:
        stable_diffusion_history_maker()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"stable_diffusion_sweep_automation.py: An error occurred: {e}")
        sys.exit(1)
