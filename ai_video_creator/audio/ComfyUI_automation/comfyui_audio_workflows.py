"""
Audio workflows for ComfyUI.
"""

from ai_video_creator.ComfyUI_automation.comfyui_workflow import ComfyUIWorkflowBase
from .environment_variables import WORKFLOW_JSON_DIR


class SparkTTSWorkflow(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    FLUX_WORKFLOW_PATH = f"{WORKFLOW_JSON_DIR}/SparkTTS_Voice_Creator_API.json"
    VOICE_CREATOR_NODE_INDEX = 1
    SAVE_AUDIO_NODE_INDEX = 8

    def __init__(self):
        """
        Initialize the FluxWorkflow class.
        """
        super().__init__(self.FLUX_WORKFLOW_PATH)

    def set_prompt(self, prompt: str) -> None:
        """
        Set the positive prompt in the workflow.
        """
        parameters = {
            self.VOICE_CREATOR_NODE_INDEX: {
                "text": prompt,
            }
        }
        super()._set_fields(parameters)
        workflow_summary = (
            f"Prompt({prompt[0]} {prompt[1]}...)/{self.get_workflow_summary()}"
        )
        self.set_workflow_summary(workflow_summary)

    def set_gender(self, gender: str) -> None:
        """
        Set the gender in the workflow.
        """
        possible_genders = ["male", "female"]

        if not gender in possible_genders:
            raise ValueError(f"Invalid gender value: {gender}")

        parameters = {self.VOICE_CREATOR_NODE_INDEX: {"gender": gender}}
        super()._set_fields(parameters)
        workflow_summary = f"Gender({gender})/{self.get_workflow_summary()}"
        self.set_workflow_summary(workflow_summary)

    def set_pitch(self, pitch: str) -> None:
        """
        Set the pitch in the workflow.
        """
        possible_pitches = ["low", "medium", "high"]

        if not pitch in possible_pitches:
            raise ValueError(f"Invalid pitch value: {pitch}")

        parameters = {self.VOICE_CREATOR_NODE_INDEX: {"pitch": pitch}}
        super()._set_fields(parameters)
        workflow_summary = f"Pitch({pitch})/{self.get_workflow_summary()}"
        self.set_workflow_summary(workflow_summary)

    def set_speed(self, speed: str) -> None:
        """
        Set the speed in the workflow.
        """
        possible_speeds = ["slow", "medium", "fast"]

        if not speed in possible_speeds:
            raise ValueError(f"Invalid speed value: {speed}")

        parameters = {self.VOICE_CREATOR_NODE_INDEX: {"speed": speed}}
        super()._set_fields(parameters)
        workflow_summary = f"Speed({speed})/{self.get_workflow_summary()}"
        self.set_workflow_summary(workflow_summary)

    def set_output_filename(self, filename):
        """
        Set the output filename in the workflow.
        """
        parameters = {self.SAVE_AUDIO_NODE_INDEX: {"filename_prefix": filename}}
        super()._set_fields(parameters)
