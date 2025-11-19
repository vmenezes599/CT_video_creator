"""Module for defining the Prompt class used in AI video creation."""

import json


class Prompt:
    """A class representing a prompt for an AI video creation system."""

    def __init__(
        self,
        narrator: str,
        visual_description: str,
        visual_prompt: str,
        scene_time_period: str,
        mood: str,
    ):
        self.narrator = narrator
        self.visual_description = visual_description
        self.visual_prompt = visual_prompt
        self.scene_time_period = scene_time_period
        self.mood = mood

    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        """Create a Prompt instance from a dictionary."""
        return cls(
            narrator=data.get("narrator", ""),
            visual_description=data.get("visual_description", ""),
            visual_prompt=data.get("visual_prompt", ""),
            scene_time_period=data.get("scene_time_period", ""),
            mood=data.get("mood", ""),
        )

    @classmethod
    def load_from_json(cls, file_path: str) -> list["Prompt"]:
        """Load multiple prompts from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            # Handle corrupted JSON, missing files, or other I/O errors gracefully
            # Return empty list so the system can continue with default behavior
            return []

        prompts = []
        if "prompts" in data and isinstance(data["prompts"], list):
            for prompt_data in data["prompts"]:
                prompts.append(cls.from_dict(prompt_data))

        return prompts

    def __str__(self):
        """String representation showing the narrator text."""
        return f"Narrator: {self.narrator[:100]}..." if len(self.narrator) > 100 else f"Narrator: {self.narrator}"
