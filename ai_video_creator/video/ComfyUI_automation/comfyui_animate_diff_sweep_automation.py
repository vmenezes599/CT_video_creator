"""
Realistic Vision Sweep Automation for ComfyUI
"""

import sys
import random

from .comfyui_video_sweepers import StableDiffusionComfyUISweeper

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


def animate_diff_sweep_automation() -> None:
    """
    Automate the sweep process for Realistic Vision in ComfyUI.
    """

    sweeper = StableDiffusionComfyUISweeper()

    sweeper.add_ksampler_sweeper(
        seed_list=[random.randint(0, 2**32 - 1)],
        steps_list=list(range(15, 51, 5)),
        cfg_list=list(range(6, 11, 2)),
        sampler_name_list=["dpmpp_sde"],
        scheduler_list=["karras"],
        denoise_list=[0.45, 1.0],
    )

    sweeper.add_animatediff_model_sweeper(
        model_name_list=[
            "animatediff-motion-adapter-v1-5-3.safetensors",
        ],
    )

    sweeper.add_stable_diffusion_model_sweeper(
        model_name_list=[
            "Realistic_Vision_V6.0_NV_B1.safetensors",
        ],
    )

    sweeper.add_positive_prompt_sweeper(
        positive_prompt_list=[
            "greece, ancient, pyramids, walking, old man, long hair, realistic, cinematic, sunrays, strong light, 8k, high quality, masterpiece, best quality, smile, happy",
            'A cute baby wearing beige clothes, happily eating mayonnaise with a spoon from a large glass jar labeled "MENEZES MAYONNAISE", soft natural lighting, cozy indoor setting, creamy texture around the baby\'s mouth, joyful and innocent expression, high-quality photo, warm color tones, realistic baby skin texture, candid and adorable moment, minimalistic background',
        ],
    )

    sweeper.add_negative_prompt_sweeper(
        negative_prompt_list=[
            "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime), text, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, UnrealisticDream"
        ],
    )

    sweeper.add_latent_image_sweeper(
        resolution_list=[
            (896, 896),
            (768, 1024),
            # (640, 1152),
            (1024, 768),
            # (1152, 640),
        ],
        batch_size_list=[32],
    )

    sweeper.send_requests()


if __name__ == "__main__":
    try:
        animate_diff_sweep_automation()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"animate_diff_sweep_automation.py: An error occurred: {e}")
        sys.exit(1)
