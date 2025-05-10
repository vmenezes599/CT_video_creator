"""
flux_sweep_automation.py
"""

import sys

from lib.ComfyUI_automation.environment_variables import CONFYUI_URL
from lib.ComfyUI_automation.comfyui_workflow import FluxWorkflow
from lib.ComfyUI_automation.comfyui_requests import ComfyUIRequests


MODEL_NAME_LIST = ["flux1-dev.safetensors", "flux1-dev-fp8.safetensors"]


def flux_sweep_automation():
    """
    Automate the sweep process for Realistic Vision in ComfyUI.
    """
    workflow = FluxWorkflow()

    workflow.set_positive_prompt(
        # positive_prompt="greece, ancient, pyramids, walking, old man, long hair, realistic, cinematic, sunrays, strong light, 8k, high quality, masterpiece, best quality, smile, happy"
        positive_prompt="luffy from one piece, football, dribbling, ball control, skillful, action shot, dynamic pose, vibrant colors, high energy, stadium background, crowd cheering, sports photography, 8k resolution"
    )

    workflow.set_unet_model(model_name="flux1-dev-fp8.safetensors")

    requests = ComfyUIRequests(CONFYUI_URL)

    requests.comfyui_send_prompt(workflow.get_json())


if __name__ == "__main__":
    try:
        flux_sweep_automation()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"flux_sweep_automation.py: An error occurred: {e}")
        sys.exit(1)
