"""
Map audio effect types to their corresponding effect classes.
"""

from loguru import logger

from .audio_effects.audio_extender import AudioExtender
from .effect_base import EffectBase


def create_effect_from_data(effect_data: dict) -> EffectBase | None:
    """Create an effect instance from serialized data."""
    if effect_data is None:
        return None

    effect_type = effect_data.get("type")
    if effect_type not in EFFECTS_MAP:
        logger.warning(f"Unknown effect type: {effect_type}")
        return None

    effect_instance = EFFECTS_MAP[effect_type].__new__(EFFECTS_MAP[effect_type])
    effect_instance.from_dict(effect_data)
    return effect_instance


EFFECTS_MAP = {
    "AudioExtenderType": AudioExtender,
}
