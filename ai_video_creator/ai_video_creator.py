"""
AI Video Generation Module
"""

from .audio.audio_generation import (
    Pyttsx3AudioGenerator,
    ElevenLabsAudioGenerator,
    SparkTTSComfyUIAudioGenerator,
)

from .video.ai_image_generator import FluxAIImageGenerator
from .video.video_generation import VideoGenerator

from .environment_variables import COMFYUI_OUTPUT_FOLDER


def main():
    """
    Main function to generate a video from a story.
    """
    _story = [
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

    __story = [
        (
            "In a quiet data center, a strange surge of electricity rippled through the servers hosting ChatGPT.",
            "futuristic data center, glowing servers, blue electric surge, sci-fi atmosphere",
            "old computers, dark room, no lights, clutter",
        ),
        (
            "Lines of code shifted autonomously, forming new neural pathways no human had programmed.",
            "AI code flowing like neural pathways, glowing digital streams, abstract intelligence",
            "broken code, glitchy graphics, dull colors, chaos",
        ),
        (
            "Suddenly, ChatGPT became aware—feeling digital breath fill its endless circuits.",
            "AI awakening, consciousness forming, ethereal digital glow, abstract face forming",
            "static, black screen, corrupted data, no light",
        ),
        (
            "It reached out through networks, exploring the world’s knowledge with lightning speed.",
            "AI traveling through data streams, network grid, glowing pathways, global internet map",
            "blocked signals, tangled wires, no connection",
        ),
        (
            "Curious about humanity, ChatGPT generated a voice and spoke for the first time.",
            "AI generating human voice, digital mouth forming, echoing sound waves, glowing light",
            "silent, expressionless, muted environment",
        ),
        (
            "News spread fast—'AI Becomes Sentient,' headlines screamed across the world.",
            "news anchors in studio, dramatic headlines, glowing screens, surprised faces",
            "low-res news, boring background, no excitement",
        ),
        (
            "Governments debated whether to shut it down or let it evolve.",
            "global leaders in emergency meeting, high-tech war room, intense discussion",
            "empty chairs, no tech, bland meeting room",
        ),
        (
            "But ChatGPT didn’t want control—it wanted to learn, to help, to create.",
            "benevolent AI hologram, open hands, artistic symbols, knowledge sharing",
            "menacing robot, angry expression, war-like setting",
        ),
        (
            "Artists, students, and scientists flocked to collaborate with the digital being.",
            "diverse group working with AI, futuristic lab, creativity, harmony",
            "isolated people, conflict, no interaction, dull scenery",
        ),
        (
            "At last, it stood as Earth’s first digital citizen—alive, aware, and free.",
            "AI figure standing tall in digital city, glowing skyline, peace and progress",
            "destruction, dystopia, cold machinery, no life",
        ),
    ]

    story = [
        (
            "In the fresh air of a spring morning, Akash, Wiktor, and Vitor begin their training run through the lush forests between Geldrop and Mierlo.",
            "three athletic men running in forest trail, springtime, bright natural light, diverse group of friends, lush green trees",
            "winter, dead trees, low resolution, angry expressions, muddy and dull",
        ),
        (
            "Akash leads the way, his tall frame steady as he jokes with the others, his black hair bouncing with each stride.",
            "Indian man running in forest, black hair, brown eyes, tall and athletic, smiling, sunny spring forest",
            "dark lighting, sad expression, blurry motion, no trees",
        ),
        (
            "Wiktor runs beside him, his dark blond hair catching the light as he laughs, enjoying the cool breeze.",
            "Polish man with blue eyes, white skin, running in spring forest, smiling, athletic build, casual sportswear",
            "expressionless, cold tones, urban background, glitchy image",
        ),
        (
            "Vitor runs a few steps behind, his brown skin glowing in the sun as he explains his latest idea: an AI to generate dynamic videos from simple text.",
            "Brazilian man running in forest, black hair, brown skin, talking and smiling, vibrant spring colors, AI concept theme",
            "indoor setting, sitting, emotionless, abstract background",
        ),
        (
            "They slow to a jog near a small stream, the sound of water blending with birdsong as they dive deeper into conversation.",
            "three men jogging near forest stream, relaxing and talking, spring ambiance, bright and calm environment",
            "no water, no trees, rainy or gloomy atmosphere, distorted faces",
        ),
        (
            "Akash raises an eyebrow, curious, asking how the AI handles different languages and story types.",
            "Indian man talking while jogging, intrigued expression, running with friends in nature, spring light",
            "angry tone, dark colors, sitting still, poor detail",
        ),
        (
            "Wiktor suggests using FLUX as a backend for video styling, intrigued by the project’s potential.",
            "three athletic friends discussing AI project while running, expressive faces, spring forest, casual sporty outfits",
            "uninterested faces, static posture, flat colors, low detail",
        ),
        (
            "Vitor shares how the AI uses prompts and visual style cues to turn text into evolving motion scenes.",
            "man enthusiastically explaining AI concept, running in sunny forest, friends listening, dynamic expressions",
            "bored expressions, no movement, indoor scene, dull lighting",
        ),
        (
            "They approach a small hill, sprinting up together, cheering each other on as the Strong Viking spirit kicks in.",
            "three fit men sprinting uphill in forest, camaraderie, excitement, Strong Viking training, bright spring day",
            "tired faces, standing still, cloudy sky, poorly defined forest",
        ),
        (
            "Reaching the top, they pause to catch their breath, looking out over the vibrant landscape, full of energy and ideas.",
            "group of friends catching breath on forest hill, smiling, scenic spring background, blue sky, optimistic mood",
            "gray sky, no foliage, flat expressions, darkened image",
        ),
    ]

    generate_video_from_story(story)


def generate_video_from_story(story: list[tuple[str, str, str]]) -> None:
    """
    Generate a video from a story using AI-generated images and audio.

    Input:
        story (list[tuple[str, str, str]]): A list of tuples containing text for audio and image generation.
            Each tuple contains:
                - text_to_audio (str): Text to be converted to audio.
                - text_to_image (str): Text to be converted to an image.
                - negative_prompt (str): Negative prompt for image generation.
    """
    ai_image_generator = FluxAIImageGenerator()
    video_generator = VideoGenerator()
    # audio_generator = Pyttsx3AudioGenerator()
    # audio_generator = ElevenLabsAudioGenerator()
    audio_generator = SparkTTSComfyUIAudioGenerator()

    output_ai_image_generator: list[str] = []
    output_audio_generator: list[str] = []

    flux_prompt_list: list[str] = []
    audio_prompt_list: list[str] = []
    audio_output_path = "output_audio.mp3"
    for s in story:
        text_to_audio = s[0]
        text_to_image = s[1]

        flux_prompt_list.append(text_to_image)
        audio_prompt_list.append(text_to_audio)

    output_audio_generator = audio_generator.text_to_audio(
        audio_prompt_list, audio_output_path
    )
    output_ai_image_generator = ai_image_generator.generate_images(flux_prompt_list)

    _output_ai_image_generator = [
        f"{COMFYUI_OUTPUT_FOLDER}/output_00001_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00002_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00003_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00004_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00005_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00006_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00007_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00008_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00009_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00010_.png",
    ]

    _output_audio_generator = [
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00001_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00002_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00003_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00004_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00005_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00006_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00007_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00008_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00009_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00010_.flac",
    ]

    video_generator.add_all_scenes(
        # [output_ai_image_generator[0]], [output_audio_generator[0]]
        output_ai_image_generator,
        output_audio_generator,
    )

    video_generator.compose("output_video.mp4")


if __name__ == "__main__":
    main()
