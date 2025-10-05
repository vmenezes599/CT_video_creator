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
            self.workflow: dict = json.load(file)

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

    def _replace_model_node_reference(
        self,
        from_node_index: int,
        to_node_index: int,
        reference_keys: list[str],
    ) -> None:
        """
        Change all references from one node to another node in the workflow.
        This replaces node references in array values but keeps dictionary keys unchanged.
        """
        from_index_str = str(from_node_index)
        to_index_str = str(to_node_index)

        def __replace_references(obj):
            if isinstance(obj, dict):
                # For dictionaries, recurse into values but keep keys unchanged
                result = {}

                for key, value in obj.items():
                    if key in reference_keys:
                        new_values = [
                            to_index_str if v == from_index_str else v for v in value
                        ]
                        result[key] = new_values
                    else:
                        result[key] = __replace_references(value)

                return result
            else:
                return obj

        self.workflow = __replace_references(self.workflow)

    def _rewire_node(
        self, node_index_to_rewire: int, from_index: int, to_index: int
    ) -> None:
        """Rewire the output of one node to the input of another node."""
        node_index_to_rewire_str = str(node_index_to_rewire)
        from_index_str = str(from_index)
        to_index_str = str(to_index)

        if node_index_to_rewire_str not in self.workflow:
            raise ValueError(
                f"Node '{node_index_to_rewire_str}' does not exist in the workflow."
            )

        if "inputs" not in self.workflow[node_index_to_rewire_str]:
            raise ValueError(
                f"Node '{node_index_to_rewire_str}' has no inputs to rewire."
            )

        if "model" not in self.workflow[node_index_to_rewire_str]["inputs"]:
            raise ValueError(
                f"Node '{node_index_to_rewire_str}' has no model to rewire."
            )

        # Fix: Properly modify the model reference in the workflow
        model_input = self.workflow[node_index_to_rewire_str]["inputs"]["model"]
        for i, value in enumerate(model_input):
            if value == from_index_str:
                model_input[i] = to_index_str

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

    def _set_output_filename(
        self, output_filename_node_index: int, filename: str
    ) -> None:
        """
        Set the output filename for the generated file.
        """
        parameters = {
            output_filename_node_index: {
                "filename_prefix": filename,
            }
        }
        self._set_fields(parameters)
