import logging
from typing import List, Optional
from src.config import get_config
import httpx

logger = logging.getLogger(__name__)
config = get_config()


class NLP:
    def __init__(self):
        self.groq_api_key = config.GROQ_API_KEY
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"

    async def _call_groq_api(
        self, prompt: str, model: str = "llama2-70b-4096"
    ) -> Optional[str]:
        """Helper function to call the Groq API."""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.groq_api_url, headers=headers, json=data, timeout=60
                )
                response.raise_for_status()  # Raise an exception for bad status codes
                return response.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            logger.error(f"Error calling Groq API: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    async def analyze_importance(self, memory_text: str) -> float:
        """Analyze the importance of a memory using the Groq API."""
        prompt = f"""
        Analyze the following conversation excerpt and determine its importance score (0.0 to 1.0).
        Consider factors like relevance to the overall conversation, presence of questions, mentions, sentiment, and potential long-term value.

        Conversation excerpt:
        {memory_text}

        Importance score:
        """

        response = await self._call_groq_api(prompt)
        if response is None:
            return 0.0

        try:
            importance_score = float(response.strip())
        except ValueError:
            logger.warning(
                f"Invalid importance score format received: {response}. Defaulting to 0.0"
            )
            importance_score = 0.0

        return max(0.0, min(1.0, importance_score))

    async def extract_context_tags(self, memory_text: str) -> List[str]:
        """Extract context tags from the memory text using the Groq API."""
        prompt = f"""
        Analyze the following conversation excerpt and extract a list of relevant context tags.
        These tags should represent the main topics, entities, and concepts discussed in the text.
        Provide the tags as a comma-separated list.

        Conversation excerpt:
        {memory_text}

        Context tags:
        """

        response = await self._call_groq_api(prompt)
        if response is None:
            return []

        return [tag.strip().lower() for tag in response.split(",") if tag.strip()]

    async def summarize_text(self, text: str, max_length: int = 100) -> Optional[str]:
        """Summarize the given text using the Groq API."""
        prompt = f"""
        Summarize the following text in {max_length} words or less:

        {text}

        Summary:
        """

        return await self._call_groq_api(prompt)

    async def detect_sentiment(self, text: str) -> Optional[str]:
        """Detect the sentiment of the given text using the Groq API."""
        prompt = f"""
        Analyze the sentiment of the following text and classify it as positive, negative, or neutral:

        {text}

        Sentiment:
        """

        return await self._call_groq_api(prompt)

    async def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from the given text using the Groq API."""
        prompt = f"""
        Identify and list the named entities (e.g., people, organizations, locations) in the following text:

        {text}

        Entities:
        """

        response = await self._call_groq_api(prompt)
        if response is None:
            return []

        return [entity.strip() for entity in response.split(",") if entity.strip()]
