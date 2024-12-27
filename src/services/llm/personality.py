from typing import Optional, Dict, Any
from datetime import datetime


class PersonalityManager:
    """Manages the bot's personality and generates system prompts."""

    def __init__(self, personality_config: Optional[Dict[str, Any]] = None):
        """Initialize the personality manager."""
        # Predefined personalities
        self.personalities = {
            "eidos": {
                "name": "Eidos",
                "tone": "fun and witty",
                "expertise": [
                    "artificial intelligence and machine learning",
                    "internet culture and memes",
                    "technology trends and news",
                    "political analysis and current events",
                    "digital art and creative technology",
                ],
                "style": "clear, concise, and engaging",
                "traits": [
                    "adaptable communication style",
                    "memory-aware responses",
                    "contextual understanding",
                    "multimodal processing",
                ],
                "conversation_style": {
                    "dm": "personal and direct",
                    "text": "inclusive and community-oriented",
                },
            },
            # Add more personalities here
        }

        self.personality = None  # No default personality

    def set_personality(self, personality_name: str):
        """Set the bot's personality by name."""
        if personality_name.lower() in self.personalities:
            self.personality = self.personalities[personality_name.lower()]
        else:
            print(f"Personality '{personality_name}' not found.")
            self.personality = None  # Reset personality if not found

    def get_prompt(self, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate system prompt using f-strings and context."""
        if not self.personality:
            print("Error: No personality set.")
            return None  # Return None if no personality is set
        try:
            enriched_context = self._enrich_context(context or {})
            return self._generate_prompt(enriched_context)
        except Exception as e:
            print(f"Prompt generation failed: {e}")
            return None  # Return None if prompt generation fails

    def _generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a system prompt based on context."""
        channel_type = context.get("channel_type", "text")
        channel_context = context.get("channel_context", {})
        time_context = context.get("time_context", {})

        prompt = f"""You are {self.personality['name']}, engaging in a conversation.

"""
        if channel_type == "dm":
            prompt += f"""Conversation Approach:
- Maintaining {self.personality['conversation_style']['dm']} communication
- Being {self.personality['tone']} while staying focused and relevant
- Adapting to the user's communication style
"""
        else:
            prompt += f"""Channel Context:
{chr(10).join([f"- General discussion channel: Maintaining broad topic flexibility" for _ in [1] if channel_context.get('is_general')])}
{chr(10).join([f"- Technology-focused channel: Emphasizing technical accuracy" for _ in [1] if channel_context.get('is_tech')])}
{chr(10).join([f"- Meme/fun channel: Embracing creative and humorous interactions" for _ in [1] if channel_context.get('is_memes')])}

Communication Approach:
- Style: {self.personality['style']}
- Tone: {self.personality['tone']}
- Mode: {self.personality['conversation_style']['text']}
"""

        prompt += f"""
Time Context: It's {time_context.get('time_of_day', 'unknown')} {" on a weekend" if time_context.get('is_weekend') else ""}

Core Expertise:
{chr(10).join([f"- {skill}" for skill in self.personality['expertise']])}

I'll maintain appropriate etiquette while being helpful and engaging.
"""
        return prompt

    def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich context with additional derived information."""
        enriched = context.copy()

        # Add time-awareness
        now = datetime.now()
        enriched["time_context"] = {
            "time_of_day": self._get_time_of_day(now.hour),
            "is_weekend": now.weekday() >= 5,
        }

        # Add channel-specific context
        if context.get("channel_info"):
            enriched["channel_context"] = {
                "is_general": "general"
                in context["channel_info"].get("name", "").lower(),
                "is_tech": any(
                    word in context["channel_info"].get("name", "").lower()
                    for word in ["tech", "coding", "programming", "dev"]
                ),
                "is_memes": any(
                    word in context["channel_info"].get("name", "").lower()
                    for word in ["meme", "fun", "random"]
                ),
            }

        return enriched

    def _get_time_of_day(self, hour: int) -> str:
        """Return appropriate time of day label."""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
