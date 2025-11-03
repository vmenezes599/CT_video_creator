"""Module for building background music generation prompts."""

import random
from logging_utils import logger
from ai_video_creator.prompt import Prompt
from ai_video_creator.environment_variables import BACKGROUND_MUSIC_PROMPT_LLM_MODEL
from ai_llm import LLMManager, LLMPromptBuilder

from ai_video_creator.utils import VideoCreatorPaths
from ai_video_creator.generators import MusicGenRecipe

from ai_video_creator.modules.narrator import NarratorAssets
from .background_music_recipe import BackgroundMusicRecipe


class BackgroundMusicRecipeBuilder:
    """Background music recipe builder for creating background music recipes from stories."""

    DEFAULT_LLM_MODEL = BACKGROUND_MUSIC_PROMPT_LLM_MODEL
    DEFAULT_MAXIMUM_SCENE_MUSIC_REPETITIONS = 8

    def __init__(self, video_creator_paths: VideoCreatorPaths):
        """Initialize BackgroundMusicRecipeBuilder with recipe data."""

        self._paths = video_creator_paths
        story_folder = self._paths.story_folder

        logger.info(
            "Initializing BackgroundMusicRecipeBuilder for story:"
            f" {story_folder.name}, chapter: {self._paths.chapter_index + 1}"
        )

        self._chapter_prompt_path = self._paths.chapter_prompt_path

        self._narrator_assets = NarratorAssets(video_creator_paths)

        if not self._narrator_assets.is_complete():
            raise ValueError("Narrator assets are incomplete. Cannot build background music recipe.")

        # Load video prompts
        self._video_prompts = Prompt.load_from_json(self._chapter_prompt_path)

        self._llm_manager = LLMManager()
        self.recipe = None

    def _generate_music_mood_extraction_prompt(self, moods: list[str], index: int) -> LLMPromptBuilder:
        """Generate prompt for extracting music mood from scene description."""

        mood_index = index - 1
        previous_3_moods = moods[max(0, mood_index - 3) : mood_index]

        system = "You are a music-mood classifier for narrator scenes. You always pick exactly one mood from a fixed list. You optimize for background underscore, not song writing. Prefer to REUSE moods already used in this chapter unless the current story clearly shifts tone."
        prompt_builder = LLMPromptBuilder(system=system)

        prompt_builder.add_content_rules_front(
            [
                "Allowed moods (pick exactly one): calm_warm, travel_neutral, mystery_low, tense_mid, emotional_soft.",
                "If the current scene fits any mood in PREVIOUS MOODS, prefer that mood.",
                "Neutral / exposition / traveling / scene-bridging / logistical narration → travel_neutral.",
                "Peaceful / hopeful / comforting / safe arrival / gentle descriptions → calm_warm.",
                "Suspicious / night / being watched / sneaking / quiet or unknown danger → mystery_low.",
                "Confrontation / urgency / active danger / argument / chase / high stakes → tense_mid.",
                "Intimate / sad / reassuring children / emotional vulnerability / grief → emotional_soft.",
                "If two moods seem possible, choose the calmer one OR the one appearing in PREVIOUS MOODS.",
                "Do NOT invent new moods. Do NOT output anything outside the allowed list.",
            ]
        )

        prompt_builder.add_format_rules_front(
            [
                "Output exactly one line.",
                "The line must start with: MOOD:",
                "After MOOD: output exactly one of: calm_warm, travel_neutral, mystery_low, tense_mid, emotional_soft.",
                "No extra text, no JSON, no code blocks, no explanations.",
            ]
        )

        user = "PREVIOUS MOODS:\n" + "\n".join(previous_3_moods)
        prompt_builder.set_user_prompt(user)

        extra = f"\nSTORY:\n{self._video_prompts[index].narrator}"
        prompt_builder.set_extra(extra)

        return prompt_builder

    def _music_mood_validator(self, response: str) -> bool:
        """Validate music mood extraction response."""
        result = True
        valid_moods = {"calm_warm", "travel_neutral", "mystery_low", "tense_mid", "emotional_soft"}
        response = response.strip()

        result = result and response in valid_moods

        if not result:
            logger.warning(f"Invalid music mood extraction response: {response}")

        return result

    def _music_mood_post_process(self, response: str) -> str:
        """Post-process music mood extraction response."""
        response = response.strip()
        mood = response[len("MOOD:") :].strip() if response.startswith("MOOD:") else response
        return mood

    def _extract_music_moods_from_prompts(self) -> list[str]:
        """Extract music moods from video prompts using LLM."""
        moods = []

        for i, scene in enumerate(self._video_prompts):
            if i == 0:
                continue
            prompt_builder = self._generate_music_mood_extraction_prompt(moods, i)
            response = self._llm_manager.send_prompt_advanced(
                model_class=self.DEFAULT_LLM_MODEL,
                prompt_builder=prompt_builder,
                validator=self._music_mood_validator,
                post_process=self._music_mood_post_process,
            )

            moods.append(response)

        return [moods[0], *moods]

    def _generate_music_prompt_from_mood_prompt_builder(self, mood_list, index: int) -> LLMPromptBuilder:
        """Generate prompt for music generation based on mood."""

        system = "You write short prompts for a text-to-music model that will generate background underscore under spoken narration. Keep it simple. Keep it consistent with the most recent scenes. Never add vocals."

        prompt_builder = LLMPromptBuilder(system=system)

        prompt_builder.add_content_rules_front(
            [
                "Inputs: up to 3 previous moods (ordered oldest → newest), the current mood, and the current narrator text.",
                "If the current mood appears in previous moods, keep the same style and instruments.",
                (
                    "Mood → tempo/instruments:\n"
                    "    - calm_warm → 72-90 bpm, soft piano, warm pads, light strings\n"
                    "    - travel_neutral → 70-88 bpm, light percussion, pads, muted guitar/synth\n"
                    "    - mystery_low → 76-88 bpm, soft pulses, low strings, light ticking percussion\n"
                    "    - tense_mid → 92-110 bpm, hybrid/light percussion, short strings, bass pulse\n"
                    "    - emotional_soft → 68-86 bpm, piano, soft strings, airy pad"
                ),
                "Always background/underscore, not a full song.",
                "Always say: “no vocals”.",
                "Always say: “loopable 30 seconds”.",
                "Add one short “inspired by …” phrase from the narrator text.",
            ]
        )

        prompt_builder.add_format_rules_front(
            [
                "Output exactly ONE line.",
                "Start with: PROMPT:",
                "Then write the full prompt for the text-to-music model.",
                "No JSON, no explanations.",
            ]
        )

        user = f"MOOD: {mood_list[index]}"
        prompt_builder.set_user_prompt(user)

        extra = f"\nSCENE DESCRIPTION:\n{self._video_prompts[index].narrator}"
        prompt_builder.set_extra(extra)

        return prompt_builder

    def _music_prompt_validator(self, response: str) -> bool:
        """Validate music generation prompt response."""
        result = True
        response = response.strip()

        if not result:
            logger.warning(f"Invalid music generation prompt response: {response}")

        return result

    def _music_prompt_post_process(self, response: str) -> str:
        """Post-process music generation prompt response."""
        response = response.strip()
        prompt = response[len("PROMPT:") :].strip() if response.startswith("PROMPT:") else response
        return prompt

    def _generate_music_prompts_from_moods(self, mood_list: list[str]) -> list[str]:
        """Generate prompt for music generation based on mood."""

        music_prompts = []

        last_prompt_for_mood: dict[str, str] = {}

        for i, mood in enumerate(mood_list):
            if mood not in last_prompt_for_mood:
                prompt_builder = self._generate_music_prompt_from_mood_prompt_builder(mood_list, i)
                response = self._llm_manager.send_prompt_advanced(
                    model_class=self.DEFAULT_LLM_MODEL,
                    prompt_builder=prompt_builder,
                    validator=self._music_prompt_validator,
                    post_process=self._music_prompt_post_process,
                )
                last_prompt_for_mood[mood] = response

            music_prompts.append(last_prompt_for_mood[mood])

        return music_prompts

    def _create_default_background_music_recipe(self) -> None:
        """Create background music recipe using default prompts."""
        logger.info(f"Creating background music recipes for {len(self._video_prompts)} prompts")

        moods = self._extract_music_moods_from_prompts()

        music_prompts = self._generate_music_prompts_from_moods(moods)

        previous_mood = None
        number_of_repeats = 0
        seed = -1
        for video_prompt, mood, music_prompt in zip(self._video_prompts, moods, music_prompts):

            if mood == previous_mood:
                number_of_repeats += 1
            else:
                number_of_repeats = 1

            if previous_mood is None or number_of_repeats >= self.DEFAULT_MAXIMUM_SCENE_MUSIC_REPETITIONS:
                seed = random.randint(0, 2**31 - 1)
                number_of_repeats = 1

            music_recipe = MusicGenRecipe(
                mood=mood,
                prompt=music_prompt,
                seed=seed,
            )
            self.recipe.add_music_recipe(music_recipe)

            previous_mood = mood

        logger.info(f"Successfully created {len(self._video_prompts)} background music recipes")

    def create_background_music_recipes(self) -> None:
        """Create background music recipe from story folder and chapter prompt index."""

        logger.info("Starting background music recipe creation process")

        self.recipe = BackgroundMusicRecipe(self._paths)

        if self.recipe.is_empty():
            self.recipe.clean()
            self._create_default_background_music_recipe()

        logger.info("Background music recipe creation completed successfully")
