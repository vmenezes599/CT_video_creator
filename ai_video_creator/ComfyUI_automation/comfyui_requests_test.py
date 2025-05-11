"""
ComfyUI Automation Helper Functions
"""
from .comfyui_requests import ComfyUIRequests

if __name__ == "__main__":

    request = ComfyUIRequests()
    response = request.comfyui_send_empty_prompt()
    print(f"Response:\n {response}")
