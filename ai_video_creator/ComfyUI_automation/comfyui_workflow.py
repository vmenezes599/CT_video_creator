"""
ComfyUI workflow automation module.
"""

import os
import json
from abc import ABC, abstractmethod
from typing_extensions import override


class IComfyUIWorkflow(ABC):
    """
    Interface for ComfyUI workflow automation.
    """

    @abstractmethod
    def get_workflow_summary(self) -> str:
        """
        Get the workflow summary for the workflow.
        """

    @abstractmethod
    def _set_workflow_summary(self, workflow_summary: str) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """

    @abstractmethod
    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """

    @abstractmethod
    def get_json(self) -> dict:
        """
        Get the JSON configuration.
        """


class ComfyUIWorkflowBase(IComfyUIWorkflow):
    """
    Base class for ComfyUI
    """

    def __init__(self, base_workflow: dict):
        """
        Initialize the ComfyUIWorkflowBase class.
        """
        if not os.path.exists(base_workflow):
            raise ValueError(f"Base workflow file {base_workflow} does not exist.")

        with open(base_workflow, "r", encoding="utf-8") as file:
            self.workflow = json.load(file)

        self.workflow_summary = "output"

    def _set_fields(self, field_parameters: dict[int, dict[str, str]]) -> None:
        """
        Set the model sweeper to the JSON configuration.

        Eg.: { 12 : { "unet_name": "flux1-dev-fp8.safetensors" }, { ... } }
        """
        for node_index, parameters in field_parameters.items():
            index_str = str(node_index)

            # Check if the node exists in the workflow
            if index_str not in self.workflow:
                raise ValueError(
                    f"WRONG NODE INDEX: Node index {index_str} does not exist in the workflow."
                )

            # Check if the "inputs" field exists for the node
            if "inputs" not in self.workflow[index_str]:
                raise ValueError(
                    f"WRONG NODE INDEX: Node {index_str} is missing the 'inputs' field."
                )

            # Validate that all keys in `parameters` exist in the workflow's inputs
            for key in parameters.keys():
                if key not in self.workflow[index_str]["inputs"]:
                    raise ValueError(
                        f"WRONG NODE INDEX: Key '{key}' is missing in the 'inputs' of node {index_str}."
                    )

            # Set the values in the workflow
            for key, value in parameters.items():
                self.workflow[index_str]["inputs"][key] = value

    @override
    def _set_workflow_summary(self, workflow_summary: str) -> None:
        """
        Set the workflow summary string for the workflow.
        """
        self.workflow_summary = workflow_summary

    @override
    def get_workflow_summary(self) -> str:
        """
        Get the workflow summary string for the workflow.
        """
        return self.workflow_summary

    @override
    def get_json(self) -> dict:
        """
        Get the JSON configuration.
        """
        return self.workflow
