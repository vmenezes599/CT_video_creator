"""Module for building background music generation prompts."""


class BackgroundMusicDefaultPrompts:
    """Class providing default prompts for background music generation."""

    DEFAULT_PROMPTS = {
        "relax": "Documentary underscore, airy ney breaths and gentle qanun over warm string drone, Hijaz color with bar roots D-C-D-A, 76 BPM feel with very soft frame-drum heartbeat, subtle room reverb, loop-friendly 4 bars, texture only, no vocals, no lead melody, no fills, no bright cymbals, no big hits.",
        "action": "Tense pursuit underscore, muted frame-drum heartbeat and sparse darbuka ghost notes under low string drone, Hijaz/Phrygian color with bar roots D-G-A-D, 108 BPM feel in staccato pulses, loop-friendly 4 bars, restrained dynamics, texture bed only, no vocals, no melodic lead, no cymbals, no risers.",
        "sci-fi": "Sci-fi underscore, soft oud harmonics layered with analog pad and granular shimmer, modal color with bar roots D-Bb-D-C, 84 BPM feel with a steady sub-pulse, wide but gentle ambience, loop-friendly 4 bars, texture only, no vocals, no hook, no risers, no bright cymbals.",
    }

    @classmethod
    def get_relax_prompt(cls) -> str:
        """Get the default relax music prompt."""
        return cls.DEFAULT_PROMPTS["relax"]

    @classmethod
    def get_action_prompt(cls) -> str:
        """Get the default action music prompt."""
        return cls.DEFAULT_PROMPTS["action"]

    @classmethod
    def get_sci_fi_prompt(cls) -> str:
        """Get the default sci-fi music prompt."""
        return cls.DEFAULT_PROMPTS["sci-fi"]
