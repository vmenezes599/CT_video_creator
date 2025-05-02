"""
Realistic Vision Sweep Automation for ComfyUI
"""

import sys
import random

from .features.comfyui_sweep import ComfyUISweep
from .features.environment_variables import (
    CONFYUI_URL,
    WORKFLOW_JSON_DIR,
    CONFYUI_OUTPUT_FOLDER,
)

POSITIVE_PROMPT_NODE_INDEX = 3
NEGATIVE_PROMPT_NODE_INDEX = 6
KSAMPLER_NODE_INDEX = 7
BATCH_SIZE_NODE_INDEX = 9
STABLE_DIFFUSION_LOADER_NODE_INDEX = 32
ANIMATEDIFF_LOADER_NODE_INDEX = 36
VIDEO_COMBINE_NODE_INDEX = 37

SAMPLER_NAME_LIST = [
    "euler",
    "dpmpp_sde",
    "dpmpp_2m_sde",
]

SCHEDULER_LIST = [
    "normal",
    "karras",
]

MODEL_NAME_LIST = [
    "animatediff-motion-adapter-v1-5-3.safetensors",
    "mm_sd_v15_v2.ckpt",
    "mm-Stabilized_high.pth",
    "temporaldiff-v1-animatediff.safetensors",
]

STABLE_DIFFUSION_MODEL_NAME_LIST = [
    "Realistic_Vision_V6.0_NV_B1.safetensors",
]

"""
* Face Portrait: 896x896
* Portrait: 896x896, 768x1024
* Half Body: 768x1024, 640x1152
* Full Body: 896x896, 768x1024, 640x1152, 1024x768, 1152x640
"""

def realistic_vision_sweep_automation(workflow_name: str) -> None:
    """
    Automate the sweep process for Realistic Vision in ComfyUI.
    """

    sweeper = ComfyUISweep(
        comfyui_url=CONFYUI_URL,
        output_node_index=VIDEO_COMBINE_NODE_INDEX,
        workflow_json_path=f"{WORKFLOW_JSON_DIR}/{workflow_name}",
        output_folder=CONFYUI_OUTPUT_FOLDER,
        output_name="output",
    )

    sweeper.add_ksampler_sweeper(
        ksampler_node_index=KSAMPLER_NODE_INDEX,
        seed_list=[random.randint(0, 2**32 - 1)],
        steps_list=list(range(15, 51, 5)),
        cfg_list=list(range(6, 11, 2)),
        sampler_name_list=["dpmpp_sde"],
        scheduler_list=["karras"],
        denoise_list=[0.45, 1.0],
    )

    sweeper.add_animatediff_model_sweeper(
        animatediff_loader_node_index=ANIMATEDIFF_LOADER_NODE_INDEX,
        model_name_list=[
            "animatediff-motion-adapter-v1-5-3.safetensors",
        ],
    )

    sweeper.add_stable_diffusion_model_sweeper(
        stable_diffusion_loader_node_index=STABLE_DIFFUSION_LOADER_NODE_INDEX,
        model_name_list=[
            "Realistic_Vision_V6.0_NV_B1.safetensors",
        ],
    )

    sweeper.add_positive_prompt_sweeper(
        positive_prompt_node_index=POSITIVE_PROMPT_NODE_INDEX,
        positive_prompt_list=[
            "greece, ancient, pyramids, walking, old man, long hair, realistic, cinematic, sunrays, strong light, 8k, high quality, masterpiece, best quality, smile, happy",
            'A cute baby wearing beige clothes, happily eating mayonnaise with a spoon from a large glass jar labeled "MENEZES MAYONNAISE", soft natural lighting, cozy indoor setting, creamy texture around the baby\'s mouth, joyful and innocent expression, high-quality photo, warm color tones, realistic baby skin texture, candid and adorable moment, minimalistic background',
        ],
    )

    sweeper.add_negative_prompt_sweeper(
        negative_prompt_node_index=NEGATIVE_PROMPT_NODE_INDEX,
        negative_prompt_list=[
            "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime), text, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, UnrealisticDream"
        ],
    )

    sweeper.add_latent_image_sweeper(
        latent_image_node_index=BATCH_SIZE_NODE_INDEX,
        resolution_list=[
            (896, 896),
            (768, 1024),
            # (640, 1152),
            (1024, 768),
            # (1152, 640),
        ],
        batch_size_list=[32],
    )

    sweeper.send_requests(delay_seconds=15)


if __name__ == "__main__":
    try:
        realistic_vision_sweep_automation("AnimateDiff_Uniform_API.json")
        realistic_vision_sweep_automation("AnimateDiff_Loop_API.json")
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    
