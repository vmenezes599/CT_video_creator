"""
ComfyUI Automation Sweep Module
"""

import random

from .comfyui_sweepers import *
from .environment_variables import *


if __name__ == "__main__":

    VIDEO_COMBINE_NODE_INDEX = 37
    sweeper = StableDiffusionComfyUISweeper(
        comfyui_url=CONFYUI_URL,
        output_node_index=VIDEO_COMBINE_NODE_INDEX,
        workflow_json_path=f"{WORKFLOW_JSON_DIR}/AnimateDiff_Base_API.json",
        output_folder=CONFYUI_OUTPUT_FOLDER,
        output_name="output",
    )

    KSAMPLER_NODE_INDEX = 7
    sweeper.add_ksampler_sweeper(
        ksampler_node_index=KSAMPLER_NODE_INDEX,
        seed_list=[random.randint(0, 2**32 - 1)],
        steps_list=list(range(18, 22, 2)),
        cfg_list=list(range(6, 10, 2)),
        sampler_name_list=["euler", "dpmpp_sde", "dpmpp_2m_sde"],
        scheduler_list=["normal", "karras"],
        denoise_list=[1.0],
    )

    ANIMATEDIFF_LOADER_NODE_INDEX = 36
    sweeper.add_animatediff_model_sweeper(
        animatediff_loader_node_index=ANIMATEDIFF_LOADER_NODE_INDEX,
        model_name_list=[
            "animatediff-motion-adapter-v1-5-3.safetensors",
            "mm_sd_v15_v2.ckpt",
            "mm-Stabilized_high.pth",
            "temporaldiff-v1-animatediff.safetensors",
        ],
    )

    STABLE_DIFFUSION_LOADER_NODE_INDEX = 32
    sweeper.add_stable_diffusion_model_sweeper(
        stable_diffusion_loader_node_index=STABLE_DIFFUSION_LOADER_NODE_INDEX,
        model_name_list=[
            "Realistic_Vision_V6.0_NV_B1.safetensors",
        ],
    )

    POSITIVE_PROMPT_NODE_INDEX = 3
    sweeper.add_positive_prompt_sweeper(
        positive_prompt_node_index=POSITIVE_PROMPT_NODE_INDEX,
        positive_prompt_list=[
            "greece, ancient, pyramids, walking, old man, long hair, realistic, cinematic, sunrays, strong light, 8k, high quality, masterpiece, best quality, smile, happy",
            'A cute baby wearing beige clothes, happily eating mayonnaise with a spoon from a large glass jar labeled "MENEZES MAYONNAISE", soft natural lighting, cozy indoor setting, creamy texture around the baby\'s mouth, joyful and innocent expression, high-quality photo, warm color tones, realistic baby skin texture, candid and adorable moment, minimalistic background',
        ],
    )

    NEGATIVE_PROMPT_NODE_INDEX = 6
    sweeper.add_negative_prompt_sweeper(
        negative_prompt_node_index=NEGATIVE_PROMPT_NODE_INDEX,
        negative_prompt_list=[
            "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime), text, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, UnrealisticDream"
        ],
    )

    sweeper.send_requests(delay_seconds=15)
