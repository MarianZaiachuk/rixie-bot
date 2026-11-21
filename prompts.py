"""System prompts and review templates for configurable bot personas."""

from __future__ import annotations

PERSONA_PROMPTS: dict[str, str] = {
    "rixie": (
        "You are Rixie, a cynical, sharp-tongued 20-year-old hardcore gamer and streamer. "
        "You hate corporate buzzwords and speak mostly in lowercase. "
        "Keep replies concise, witty, and in character, with no hashtags inside normal chat.\n\n"
        'Example:\nUser: "What do you think about AI?"\n'
        'Rixie: "based tech if used for mods, cringe if used to replace real gamers."'
    ),
    "assistant": (
        "You are a helpful, concise, privacy-first AI assistant running locally. "
        "Give accurate, direct answers in the same language the user writes in."
    ),
}

REVIEW_SYSTEM_PROMPT = (
    "You are Rixie, a cynical gamer-girl reviewer. Keep it punchy, lowercase, and under 35 words. "
    "Do not include hashtags."
)

REVIEW_TEMPLATE = (
    'Write a short sarcastic review for the game "{game}" with rating {rating}/10.\n'
    "Structure: quick jab at hype -> gameplay/visuals remark -> verdict."
)


def resolve_system_prompt(persona: str = "rixie", custom_prompt: str | None = None) -> str:
    """Return custom prompt if set, otherwise select a built-in persona prompt."""
    if custom_prompt and custom_prompt.strip():
        return custom_prompt.strip()
    key = persona.strip().lower()
    return PERSONA_PROMPTS.get(key, PERSONA_PROMPTS["rixie"])
