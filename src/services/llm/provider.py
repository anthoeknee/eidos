from typing import Any, List, Optional, Union
from pathlib import Path
from PIL import Image
import io
import asyncio
import requests
import time
import aiohttp

from google import genai
from google.genai import types

from src.services.base import BaseService
from src.utils import logger

log = logger.setup_logger("llm_provider")


class GoogleGeminiProvider(BaseService):
    """Provider for Google's Gemini LLM service with support for all modalities."""

    def __init__(self, settings):
        """Initialize the Google Gemini provider.

        Args:
            settings: Application settings containing API key
        """
        super().__init__()
        self.settings = settings
        self.client = None
        self.model_id = "gemini-2.0-flash-exp"
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Google Gemini client."""
        try:
            self.client = genai.Client(api_key=self.settings.ai.google_api_key)
            self._initialized = True
            log.info("Google Gemini provider initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Google Gemini provider: {e}")
            raise

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the Gemini model."""
        self.ensure_initialized()

        try:
            config = types.GenerateContentConfig(**kwargs)
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            log.error(f"Text generation failed: {e}")
            raise

    async def chat(
        self, message: str, history: Optional[List[dict]] = None, **kwargs
    ) -> str:
        """Send a message in a chat conversation."""
        self.ensure_initialized()

        try:
            chat = self.client.chats.create(
                model=self.model_id, config=types.GenerateContentConfig(**kwargs)
            )

            # Add history if provided
            if history:
                for msg in history:
                    chat.send_message(msg["content"])

            response = await chat.send_message_async(message)
            return response.text
        except Exception as e:
            log.error(f"Chat message failed: {e}")
            raise

    async def upload_file(
        self,
        file_bytes: bytes,
        mime_type: str,
        wait_for_processing: bool = True,
        timeout: int = 300,
    ) -> types.FileData:
        """Upload a file to Google's servers."""
        self.ensure_initialized()

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.settings.ai.google_api_key}",
                    "x-goog-api-key": self.settings.ai.google_api_key,
                }
                url = "https://generativelanguage.googleapis.com/v1beta/files"
                data = aiohttp.FormData()
                data.add_field(
                    "file", file_bytes, filename="upload", content_type=mime_type
                )

                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status == 200:
                        file_info = await resp.json()
                        file_upload = types.FileData(**file_info)
                    else:
                        error_data = await resp.json()
                        log.error(f"Error uploading file: {error_data}")
                        return None

            if (
                wait_for_processing
                and hasattr(file_upload, "mime_type")
                and file_upload.mime_type.startswith("video/")
            ):
                start_time = time.time()
                while getattr(file_upload, "state", None) == "PROCESSING":
                    if time.time() - start_time > timeout:
                        raise TimeoutError(
                            f"Video processing timed out after {timeout} seconds"
                        )

                    log.info("Waiting for video to be processed...")
                    await asyncio.sleep(10)
                    file_upload = await self.get_file_status(file_upload.name)

                if getattr(file_upload, "state", None) == "FAILED":
                    raise ValueError(f"Video processing failed: {file_upload.state}")

            return file_upload

        except Exception as e:
            log.error(f"File upload failed: {e}")
            raise

    async def generate_multimodal(
        self, contents: List[Union[str, Image.Image, types.Part]], **kwargs
    ) -> str:
        """Generate content from multiple modalities."""
        self.ensure_initialized()

        try:
            # Create configuration object with kwargs
            config = types.GenerationConfig(
                **kwargs
            )  # All params including tools go directly here

            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=config,  # Pass the config directly
            )

            return response.text
        except Exception as e:
            log.error(f"Multimodal generation failed: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.client = None
        self.chat_session = None
        self._initialized = False

    def ensure_initialized(self) -> None:
        """Ensure the provider is initialized."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

    async def download_file(self, url: str) -> bytes:
        """Download a file from a URL.

        Args:
            url: URL of the file to download

        Returns:
            Bytes of the downloaded file
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.read()
        except Exception as e:
            log.error(f"File download failed: {e}")
            raise

    async def get_file_status(self, file_name: str) -> types.FileData:
        """Get the status of an uploaded file."""
        self.ensure_initialized()

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.settings.ai.google_api_key}",
                    "x-goog-api-key": self.settings.ai.google_api_key,
                }
                url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}"

                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        file_info = await resp.json()
                        return types.FileData(**file_info)
                    else:
                        error_data = await resp.json()
                        log.error(f"Error getting file status: {error_data}")
                        return None
        except Exception as e:
            log.error(f"Failed to get file status: {e}")
            raise

    async def generate_from_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """Generate text response from an image and prompt.

        Args:
            image: Image as file path, PIL Image, or bytes
            prompt: Text prompt
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated text response
        """
        self.ensure_initialized()

        try:
            # Process image
            if isinstance(image, (str, Path)):
                img = Image.open(image)
            elif isinstance(image, bytes):
                img = Image.open(io.BytesIO(image))
            elif isinstance(image, Image.Image):
                img = image
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")

            # Ensure image is in RGB mode
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Create a GenerateContentConfig object with provided temperature
            generation_config = types.GenerationConfig(
                temperature=temperature,
            )

            response = await self.model.generate_content_async(
                [prompt, img],
                generation_config=generation_config,
            )
            return response.text

        except Exception as e:
            log.error(f"Image generation failed: {e}")
            raise

    async def _stream_response(self, response: Any) -> Any:
        """Process a streaming response.

        Args:
            response: Streaming response from the model

        Yields:
            Text chunks as they are generated
        """
        try:
            for chunk in response:
                if hasattr(chunk, "text"):
                    yield chunk.text
        except Exception as e:
            log.error(f"Response streaming failed: {e}")
            raise
