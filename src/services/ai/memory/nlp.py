import logging
from typing import List, Optional, Union
from src.config import get_config
from pathlib import Path
import discord

logger = logging.getLogger(__name__)
config = get_config()


class NLP:
    def __init__(self):
        self.groq_api_key = config.GROQ_API_KEY
        self.groq_provider = None
        self.initialized = False

    async def initialize(self):
        """Initialize the Groq provider."""
        if self.groq_api_key and not self.initialized:
            from src.services.ai.providers import GroqAIProvider

            self.groq_provider = GroqAIProvider(api_key=self.groq_api_key)
            logger.info("Groq provider initialized.")
            self.initialized = True
        elif not self.groq_api_key:
            logger.warning("Groq API key not found. Groq provider will not be used.")
        else:
            logger.info("Groq provider already initialized.")

    async def _call_groq_api(
        self,
        prompt: str,
        files: Optional[List[Union[str, Path, discord.Attachment]]] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """Helper function to call the Groq API."""
        await self.initialize()
        if not self.groq_provider:
            logger.error("Groq provider not initialized.")
            return None

        try:
            response = await self.groq_provider.generate(
                prompt=prompt, files=files, system_prompt=system_prompt
            )
            return response
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return None

    async def analyze_importance(
        self,
        memory_text: str,
        files: Optional[List[Union[str, Path, discord.Attachment]]] = None,
    ) -> float:
        """Analyze the importance of a memory using the Groq API."""
        prompt = f"""
        Analyze the following conversation excerpt and determine its importance score (0.0 to 1.0).
        Consider factors like relevance to the overall conversation, presence of questions, mentions, sentiment, and potential long-term value.

        Conversation excerpt:
        {memory_text}

        Importance score:
        """

        response = await self._call_groq_api(prompt, files=files)
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

    async def extract_context_tags(
        self,
        memory_text: str,
        files: Optional[List[Union[str, Path, discord.Attachment]]] = None,
    ) -> List[str]:
        """Extract context tags from the memory text using the Groq API."""
        prompt = f"""
        Analyze the following conversation excerpt and extract a list of relevant context tags.
        These tags should represent the main topics, entities, and concepts discussed in the text.
        Provide the tags as a comma-separated list.

        Conversation excerpt:
        {memory_text}

        Context tags:
        """

        response = await self._call_groq_api(prompt, files=files)
        if response is None:
            return []

        return [tag.strip().lower() for tag in response.split(",") if tag.strip()]

    async def summarize_text(
        self,
        text: str,
        max_length: int = 100,
        files: Optional[List[Union[str, Path, discord.Attachment]]] = None,
    ) -> Optional[str]:
        """Summarize the given text using the Groq API."""
        prompt = f"""
        Summarize the following text in {max_length} words or less:

        {text}

        Summary:
        """

        return await self._call_groq_api(prompt, files=files)

    async def detect_sentiment(
        self,
        text: str,
        files: Optional[List[Union[str, Path, discord.Attachment]]] = None,
    ) -> Optional[str]:
        """Detect the sentiment of the given text using the Groq API."""
        prompt = f"""
        Analyze the sentiment of the following text and classify it as positive, negative, or neutral:

        {text}

        Sentiment:
        """

        return await self._call_groq_api(prompt, files=files)

    async def extract_entities(
        self,
        text: str,
        files: Optional[List[Union[str, Path, discord.Attachment]]] = None,
    ) -> List[str]:
        """Extract named entities from the given text using the Groq API."""
        prompt = f"""
        Identify and list the named entities (e.g., people, organizations, locations) in the following text:

        {text}

        Entities:
        """

        response = await self._call_groq_api(prompt, files=files)
        if response is None:
            return []

        return [entity.strip() for entity in response.split(",") if entity.strip()]

    async def classify_text(
        self,
        text: str,
        categories: List[str],
        files: Optional[List[Union[str, Path, discord.Attachment]]] = None,
    ) -> Optional[str]:
        """Classify the given text into one of the provided categories using the Groq API."""
        prompt = f"""
        Classify the following text into one of the following categories: {', '.join(categories)}.

        Text:
        {text}

        Category:
        """

        return await self._call_groq_api(prompt, files=files)

    async def analyze_multiple_messages(
        self,
        messages: List[str],
        task: str,
        files: Optional[List[List[Union[str, Path, discord.Attachment]]]] = None,
    ) -> List[Optional[str]]:
        """
        Analyze multiple messages using the Groq API.

        Args:
            messages: A list of message strings to analyze.
            task: The specific task to perform (e.g., "sentiment", "entities", "tags", "importance", "summary").
            files: Optional list of lists of files corresponding to each message.

        Returns:
            A list of analysis results, corresponding to each message.
        """
        results = []
        if files is None:
            files = [None] * len(messages)

        for message, file_list in zip(messages, files):
            if task == "sentiment":
                result = await self.detect_sentiment(message, files=file_list)
            elif task == "entities":
                result = await self.extract_entities(message, files=file_list)
            elif task == "tags":
                result = await self.extract_context_tags(message, files=file_list)
            elif task == "importance":
                result = await self.analyze_importance(message, files=file_list)
            elif task == "summary":
                result = await self.summarize_text(message, files=file_list)
            else:
                logger.warning(f"Unsupported task: {task}")
                result = None
            results.append(result)
        return results
