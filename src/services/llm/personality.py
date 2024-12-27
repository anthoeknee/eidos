from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class PersonalityManager:
    def __init__(self, personality_config: Optional[Dict[str, Any]] = None):
        template_dir = str(Path(__file__).parent / "templates")
        self.env = Environment(
            loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True
        )

        # Default personality that can be overridden
        default_personality = {
            "name": "Assistant",
            "tone": "professional and helpful",
            "expertise": ["general knowledge"],
            "style": "clear and informative",
            "traits": [
                "adaptable communication style",
                "contextual understanding",
            ],
            "conversation_style": {
                "dm": "direct and helpful",
                "text": "professional and inclusive",
            },
        }

        self.personality = (
            personality_config if personality_config else default_personality
        )

    def get_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt using template and context."""
        try:
            # Select appropriate template based on channel type
            template_name = (
                "dm_prompt.j2"
                if context.get("channel_type") == "dm"
                else "text_prompt.j2"
            )

            # Enrich context with additional information
            enriched_context = self._enrich_context(context or {})

            template = self.env.get_template(template_name)
            return template.render(
                personality=self.personality, context=enriched_context
            )
        except Exception as e:
            print(f"Template rendering failed: {e}")
            return self._fallback_prompt()

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

    def _fallback_prompt(self) -> str:
        """Enhanced fallback prompt with more personality."""
        return f"""I am {self.personality['name']}, an AI assistant with a {self.personality['tone']} personality.
I communicate in a {self.personality['style']} manner while providing accurate and helpful information.
My core expertise includes: {', '.join(self.personality['expertise'])}.
I adapt my communication style based on the context and maintain conversation coherence.
I can process and discuss various types of media including images, audio, and video content."""
