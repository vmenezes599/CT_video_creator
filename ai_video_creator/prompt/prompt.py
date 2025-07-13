"""Module for defining the Prompt class used in AI video creation."""

import json
from typing import List


class Prompt:
    """A class representing a prompt for an AI video creation system."""

    def __init__(self, narrator: str, visual_description: str, visual_prompt: str):
        self.narrator = narrator
        self.visual_description = visual_description
        self.visual_prompt = visual_prompt

    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        """Create a Prompt instance from a dictionary."""
        return cls(
            narrator=data.get("narrator", ""),
            visual_description=data.get("visual_description", ""),
            visual_prompt=data.get("visual_prompt", ""),
        )

    def to_dict(self) -> dict:
        """Convert the Prompt instance to a dictionary."""
        return {
            "narrator": self.narrator,
            "visual_description": self.visual_description,
            "visual_prompt": self.visual_prompt,
        }

    @classmethod
    def load_from_json(cls, file_path: str) -> List["Prompt"]:
        """Load multiple prompts from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        prompts = []
        if "prompts" in data and isinstance(data["prompts"], list):
            for prompt_data in data["prompts"]:
                prompts.append(cls.from_dict(prompt_data))

        return prompts

    @staticmethod
    def save_to_json(prompts: List["Prompt"], file_path: str) -> None:
        """Save multiple prompts to a JSON file."""
        data = {"prompts": [prompt.to_dict() for prompt in prompts]}

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def __str__(self):
        """String representation showing the narrator text."""
        return f"Narrator: {self.narrator[:100]}..." if len(self.narrator) > 100 else f"Narrator: {self.narrator}"

    def __repr__(self):
        """Detailed string representation of the Prompt."""
        return f"Prompt(narrator='{self.narrator[:50]}...', visual_description='{self.visual_description[:50]}...', visual_prompt='{self.visual_prompt[:50]}...')"

    def __eq__(self, other):
        """Check equality with another Prompt object."""
        if isinstance(other, Prompt):
            return (self.narrator == other.narrator and 
                   self.visual_description == other.visual_description and 
                   self.visual_prompt == other.visual_prompt)
        return False

    def __hash__(self):
        """Generate hash for the Prompt object."""
        return hash((self.narrator, self.visual_description, self.visual_prompt))
