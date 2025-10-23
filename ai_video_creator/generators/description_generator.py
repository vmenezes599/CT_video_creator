"""
This module contains the Florence image generator class."""

import random
import tempfile
from pathlib import Path

from ai_llm import LLMManager, LLMPromptBuilder
from ai_video_creator.ComfyUI_automation import (
    ComfyUIRequests,
)
from ai_video_creator.environment_variables import (
    COMFYUI_OUTPUT_FOLDER,
    DESCRIPTION_GENERATION_LLM_MODEL,
)
from ai_video_creator.generators.ComfyUI_automation.comfyui_text_workflows import (
    FlorentI2TWorkflow,
    FlorentV2TWorkflow,
)

from ai_video_creator.prompt import Prompt
from logging_utils import logger


class FlorenceGenerator:
    """
    A class to generate videos based on a list of strings using ComfyUI workflows.
    """

    def __init__(self):
        """
        Initialize the WanGenerator class.
        :param generation_count: Number of passes of WAN. Each passes adds 5 second of video.
        """
        self.requests = ComfyUIRequests()  # Initialize ComfyUI requests

    def generate_description(self, asset: Path) -> str:
        """
        Generate a description based on the input image.
        """

        if not asset:
            logger.warning("No asset provided for description generation")
            return ""

        new_asset_path = self.requests.upload_file(asset)

        workflow = None
        if asset.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            workflow = FlorentI2TWorkflow()
            workflow.set_image(new_asset_path.name)
        elif asset.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
            workflow = FlorentV2TWorkflow()
            workflow.set_video(new_asset_path.name)
        else:
            logger.error(f"Unsupported asset type: {asset.suffix}")
            raise ValueError(f"Unsupported asset type: {asset.suffix}")

        temp_file_name = Path(f"florence_output_{random.randint(0, 2**32 - 1)}.txt")

        workflow.set_seed(random.randint(0, 2**64 - 1))
        workflow.set_output_filename(temp_file_name.stem)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            results = self.requests.ensure_send_all_prompts([workflow], temp_output_dir)

            output_text_path = results[0]

            with open(output_text_path, "r", encoding="utf-8") as file_handler:
                result = file_handler.read().strip()

        return result


class SceneScriptGenerator:
    """
    A class to generate scene scripts based on a list of strings using ComfyUI workflows.
    """

    DEFAULT_LLM_MODEL = DESCRIPTION_GENERATION_LLM_MODEL

    def __init__(
        self,
        scene_initial_image: Path,
        number_of_subdivisions: int,
        sub_video_prompt: Prompt,
        previous_sub_video_prompt: Prompt = None,
    ):
        """
        Initialize the SceneScriptGenerator class.
        """
        self._number_of_subdivisions = number_of_subdivisions
        self._sub_video_prompt = sub_video_prompt
        self._previous_sub_video_prompt = previous_sub_video_prompt

        self._llm_manager = LLMManager()

        self._scene_subdivisions: list[str] = []

        self.florence2_description = FlorenceGenerator().generate_description(
            scene_initial_image
        )

    def _generate_scene_script_prompt(self, index: int) -> LLMPromptBuilder:
        """
        Generate a prompt to enrich a single visual segment (from subdivision)
        into a full scene script description.
        This is the second phase after subdivision.
        """

        system = (
            "You are a helpful assistant that turns short, literal visual descriptions "
            "into rich scene scripts. Your job is to expand each one into a detailed, vivid "
            "scene description suitable for visual rendering."
        )

        prompt_builder = LLMPromptBuilder(system=system)

        # --- FORMAT RULES ---
        format_rules = [
            "Output exactly one paragraph.",
            "Do not number or bullet the output.",
            "Write in present tense, third person.",
            "Do not include camera terms unless explicitly mentioned.",
            "Avoid dialogue and internal thoughts.",
            "Keep it between 1 and 3 sentences, 50–80 words in total.",
        ]
        prompt_builder.add_format_rules_front(format_rules)

        # --- CONTENT RULES ---
        content_rules = [
            "Base the enrichment primarily on the Florence2 description and the given visual segment.",
            "Use the original visual prompt only for optional cues about symbolism, mood, or visual composition — never for literal details.",
            "Do not introduce characters, actions, or objects not supported by the Florence2 description or the current segment.",
            "Preserve the visual setting and sequence, ensuring the result aligns with what would be seen in the image.",
            "You may add environmental details, lighting, motion, or atmosphere for richness.",
            "Do not contradict or reinterpret the original visual intent.",
            "Write as if describing a cinematic shot ready for generation.",
            "If a previous visual segment is provided, you may use it to preserve flow or avoid repeating visual setup.",
        ]
        prompt_builder.add_content_rules_front(content_rules)

        # --- USER PROMPT ---
        scene_description = self._scene_subdivisions[index]
        previous_description = (
            self._scene_subdivisions[index - 1] if index > 0 else None
        )
        original_visual_prompt = self._sub_video_prompt.visual_description

        user_prompt = (
            "You are given a plain visual description of a scene segment. "
            "Your task is to enrich the current visual description into a vivid, cinematic scene. "
            "Use the Florence2 description as the main perceptual base, "
            "and the original visual prompt only as optional context for intent or tone.\n\n"
            f"Scene context (Florence2 – visual base):\n{self.florence2_description.strip()}\n\n"
            f"Original visual prompt (intent/tone):\n{original_visual_prompt.strip()}\n\n"
        )

        if previous_description:
            user_prompt += f"Previous visual segment (for continuity):\n{previous_description.strip()}\n\n"

        user_prompt += f"Current visual description:\n{scene_description.strip()}"
        prompt_builder.set_user_prompt(user_prompt)

        # --- EXAMPLE ---
        example = (
            "Scene context (Florence2 – visual base):\n"
            "A moody, sun-dappled forest filled with motion and tension.\n\n"
            "Original visual prompt (intent/tone):\n"
            "The boy stands alone beneath the towering canopy as the sunlight breaks through the mist.\n\n"
            "Previous visual segment (for continuity):\n"
            "The boy slows down, breathing heavily as the forest path narrows.\n\n"
            "Current visual description:\n"
            "The boy runs through a dense forest path, sunlight flashing between the leaves.\n\n"
            "Enriched scene:\n"
            "Sunlight pulses through the trees as the boy sprints along the narrow forest trail. "
            "Leaves scatter under his feet while the distant wind whistles through the dense canopy. "
            "The light dances across his face, emphasizing the urgency in his stride."
        )
        prompt_builder.set_example(example)

        return prompt_builder

    def _generate_scene_script_validator(self, script: str) -> bool:
        """
        Validate the generated script to ensure it meets the required criteria.
        """
        if len(script.split()) < 20:  # Example: Ensure script has at least 20 words
            return False

        return True

    def _generate_scene_script_post_process(self, script: str) -> str:
        """
        Post-process the generated script to ensure it is clean and formatted correctly.
        """
        return script.strip()

    def _generate_scene_script(self, index: int) -> str:
        """
        Generate a scene script based on the input image and scene text.
        """
        prompt_builder = self._generate_scene_script_prompt(index)
        response = self._llm_manager.send_prompt_advanced(
            self.DEFAULT_LLM_MODEL,
            prompt_builder,
            self._generate_scene_script_validator,
            self._generate_scene_script_post_process,
        )

        return response

    def _generate_subdivide_scene_prompt(self) -> LLMPromptBuilder:
        """
        Generate a prompt for subdividing the scene into smaller parts.
        """
        system = "You are a helpful assistant that divides a complete narrated text into timed visual segments. Each segment corresponds to a portion of the narration and should describe a visible moment based only on that part."
        prompt_builder = LLMPromptBuilder(system=system)

        # FORMAT RULES
        format_rules = [
            "Output one line per segment.",
            "Do not number or bullet the lines.",
            "Each line should be a single sentence (maximum ~25 words).",
            "Avoid dialogue, inner thoughts, stylistic language, or camera terms.",
            "Describe only simple, visible actions or settings that match the narration.",
        ]
        prompt_builder.add_format_rules_front(format_rules)

        # CONTENT RULES
        content_rules = [
            f"The full narration below must be divided into {self._number_of_subdivisions} equal-length segments based on time (~{self._number_of_subdivisions} seconds per part).",
            "For each timed segment, write one visual description that aligns only with that part of the narration.",
            "Treat each segment independently and in order — do not summarize the whole scene.",
            "Do not enrich, stylize, or interpret beyond what is stated or clearly implied.",
            "If a segment is abstract, convert it into a neutral, symbolic visual (e.g., swirling patterns, expanding light).",
            "Avoid introducing new elements not implied by the narration.",
            "The example is dynamically sized to match the required number of segments.",
        ]
        prompt_builder.add_content_rules_front(content_rules)

        # USER PROMPT
        if self._previous_sub_video_prompt:
            user_prompt = (
                f"The following is a continuation of a narrated scene. The previous part was provided for context:\n"
                f"{self._previous_sub_video_prompt.narrator}n\n"
                f"The current narration is complete and has not yet been divided.\n"
                f"For each part, write one simple visual description, one per line, based only on that portion of the narration.\n"
                f"Do not combine, summarize, or enrich across parts. Treat each segment independently.\n\n"
                f"Below is the full narration to be subdivided into {self._number_of_subdivisions} equal time-based parts:\n{self._sub_video_prompt.narrator}"
            )
        else:
            user_prompt = (
                f"The following narrated text is complete and has not yet been divided.\n"
                f"For each part, write one simple visual description, one per line, based only on that portion of the narration.\n"
                f"Do not combine, summarize, or enrich across parts. Treat each segment independently.\n\n"
                f"Below is the full narration to be subdivided into {self._number_of_subdivisions} equal time-based parts:\n{self._sub_video_prompt.narrator}"
            )

        prompt_builder.set_user_prompt(user_prompt)

        # EXAMPLE (dynamically sliced/padded to match number_of_subdivisions)
        example_lines = [
            "A boy walks along a dirt trail surrounded by tall pine trees.",
            "He looks up at the canopy as sunlight flickers through the leaves.",
            "A gust of wind rustles the branches, scattering dry needles around him.",
            "He pauses near a mossy boulder and glances behind him.",
            "A distant bird call makes him turn his head toward the sky.",
            "He crouches to examine a set of animal tracks in the mud.",
            "Leaves swirl gently across the path as the breeze picks up.",
            "He stands and brushes dirt from his knees.",
            "Clouds begin to gather above the forest canopy.",
            "The light dims slightly as the first drop of rain hits his arm.",
        ]

        if self._number_of_subdivisions <= len(example_lines):
            example = "\n".join(example_lines[: self._number_of_subdivisions])
        else:
            additional = [example_lines[-1]] * (
                self._number_of_subdivisions - len(example_lines)
            )
            example = "\n".join(example_lines + additional)

        prompt_builder.set_example(example)

        return prompt_builder

    def _subdivide_scene_validator(self, subdivisions: str) -> bool:
        """
        Validate the subdivisions to ensure they meet the required criteria.
        """
        scene_count = len([line for line in subdivisions.split("\n") if line.strip()])
        if scene_count != self._number_of_subdivisions:
            return False

        return True

    def _subdivide_scene_post_process(self, subdivisions: str) -> str:
        """
        Post-process the subdivisions to ensure they are clean and formatted correctly.
        """
        return subdivisions

    def _generate_scene_subdivisions(self) -> list[str]:
        """
        Generate subdivisions for the scene.
        """
        prompt_builder = self._generate_subdivide_scene_prompt()
        response = self._llm_manager.send_prompt_advanced(
            self.DEFAULT_LLM_MODEL,
            prompt_builder,
            self._subdivide_scene_validator,
            self._subdivide_scene_post_process,
        )
        self._scene_subdivisions = [
            line.strip() for line in response.split("\n") if line.strip()
        ]

    def generate_scenes_script(self) -> list[str]:
        """
        Generate scripts for all scenes.
        """

        self._generate_scene_subdivisions()

        result: list[str] = []
        for index, _ in enumerate(self._scene_subdivisions):
            script = self._generate_scene_script(index)
            result.append(script)

        logger.info(f"Generated {len(result)} scene scripts.")

        return result


def main():
    """Main function for testing purposes."""
    previous_prompt = Prompt(
        "In the beginning, there was only the deep, a vast emptiness, a canvas waiting. From this void, God’s thoughts took shape, swirling and coalescing in the infinite silence. He breathed, and a spark—a light—came into being, warm and radiant. Let there be light, He declared, and in an instant, the darkness shattered like glass, revealing a tapestry of brilliance that spread across the cosmos. The air crackled with energy as colors burst forth; vibrant hues painted the heavens.",
        "",
        "",
    )
    current_prompt = Prompt(
        "With each utterance, He crafted the sky above—a vast expanse of deep blues and soft whites—and the waters below, their surfaces shimmering like gemstones under the newborn sun. Establishing boundaries that formed a delicate balance, He watched as the stars flickered to life like celestial messengers sent to herald this new creation. Mountains rose majestically from the earth, their jagged peaks touching the heavens while valleys nestled in their embrace, filled with vibrant greens that danced in the gentle breeze.",
        "In a breathtaking widescreen panorama, the sky unfurls in deep blues and soft whites, while the waters below sparkle like scattered gemstones, reflecting the golden hue of the newborn sun. God stands at the edge of a rugged mountain peak, arms outstretched as he shapes the celestial canvas above, while humanity gathers in awe at the valley's edge, their silhouettes framed against the vibrant greens of swaying grass and blooming wildflowers. The atmosphere is imbued with a sense of sublime creation, as gentle breezes carry whispers of life through this newly formed world, where every element vibrates with harmony and potential.",
        "",
    )
    image_path = Path(
        "/home/vitor/projects/AI-Story-Video/AI-Video-Creator/stories/Bible/video/chapter_001/assets/images/chapter_001_image_003_00005_.png"
    )

    gen = SceneScriptGenerator(image_path, 5, current_prompt, previous_prompt)

    result = gen.generate_scenes_script()


if __name__ == "__main__":
    main()
