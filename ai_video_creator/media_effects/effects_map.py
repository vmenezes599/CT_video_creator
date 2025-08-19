"""
Map audio effect types to their corresponding effect classes.
"""

from .audio_effects.audio_extender import AudioExtender


EFFECTS_MAP = {
    "AudioExtenderType": AudioExtender,
}
