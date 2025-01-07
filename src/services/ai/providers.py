from typing import Optional, List, Union, Any, Dict
from pathlib import Path
import time
from venv import logger
import discord
from google import genai
from google.genai import types
import base64
import cohere
from discord import Attachment
import asyncio
import aiohttp


class GoogleAIProvider:
    def __init__(self, api_key: str, model_id: str = "gemini-pro"):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

        # Configure default generation parameters
        self.default_config = types.GenerateContentConfig(
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=2048,
        )

    def create_chat(
        self, system_instruction: Optional[str] = None, temperature: float = 0.5
    ):
        """Create a new chat session"""
        return self.client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
            ),
        )

    async def generate(
        self,
        prompt: Optional[str] = None,
        files: Optional[List[Union[Path, discord.Attachment]]] = None,
        return_raw: bool = False,
    ) -> Union[str, types.GenerateContentResponse]:
        """
        Unified method to generate content with optional file inputs from paths or Discord attachments.
        Returns either the raw response object or just the text.
        """
        contents = []

        if files:
            for file in files:
                if isinstance(file, discord.Attachment):
                    # Handle Discord attachment
                    file_data = await file.read()
                    # Create temporary file with correct extension
                    temp_path = Path(f"temp_{file.filename}")
                    temp_path.write_bytes(file_data)

                    try:
                        file_upload = self.client.files.upload(path=temp_path)
                    finally:
                        # Cleanup temporary file
                        temp_path.unlink()
                else:
                    # Handle regular Path object
                    file_upload = self.client.files.upload(path=file)

                # Wait for video processing if necessary
                if file_upload.mime_type.startswith("video/"):
                    max_retries = 20  # Maximum number of retries
                    retry_delay = 5  # Delay between retries in seconds
                    for attempt in range(max_retries):
                        if file_upload.state == "PROCESSING":
                            time.sleep(retry_delay)
                            file_upload = self.client.files.get(name=file_upload.name)
                        elif file_upload.state == "ACTIVE":
                            break
                        else:
                            raise ValueError(
                                f"Video processing failed: {file}, state: {file_upload.state}"
                            )
                    else:
                        raise ValueError(f"Video processing timed out: {file}")

                # Wait for audio processing if necessary
                if file_upload.mime_type.startswith("audio/"):
                    max_retries = 20  # Maximum number of retries
                    retry_delay = 5  # Delay between retries in seconds
                    for attempt in range(max_retries):
                        if file_upload.state == "PROCESSING":
                            time.sleep(retry_delay)
                            file_upload = self.client.files.get(name=file_upload.name)
                        elif file_upload.state == "ACTIVE":
                            break
                        else:
                            raise ValueError(
                                f"Audio processing failed: {file}, state: {file_upload.state}"
                            )
                    else:
                        raise ValueError(f"Audio processing timed out: {file}")

                # Check for PDF files
                if file_upload.mime_type == "application/pdf":
                    pass  # No special processing needed for PDFs

                # Check for image files
                if file_upload.mime_type.startswith("image/"):
                    pass  # No special processing needed for images

                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(
                                file_uri=file_upload.uri,
                                mime_type=file_upload.mime_type,
                            )
                        ],
                    )
                )

        # Add the text prompt
        if prompt:
            contents.append(prompt)

        # Generate response
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id, contents=contents
            )
        except Exception as e:
            raise ValueError(f"Error generating content: {e}")

        return response if return_raw else response.text

    def count_tokens(self, content: str) -> int:
        """Count tokens for given content"""
        try:
            response = self.client.models.count_tokens(
                model=self.model_id, contents=content
            )
            return response.total_tokens
        except Exception as e:
            raise ValueError(f"Error counting tokens: {e}")


class CohereAIProvider:
    def __init__(self, api_key: str, model_id: str = "embed-english-v3.0"):
        self.client = cohere.AsyncClient(api_key=api_key)
        self.model_id = model_id

    async def get_embedding(
        self, content: Union[str, Union[Path, Attachment]], content_type: str = "text"
    ) -> List[float]:
        """Get embedding for either text or image input."""
        try:
            if content_type == "text":
                response = await self.client.embed(
                    texts=[content],
                    model=self.model_id,
                    input_type="search_document",
                    embedding_types=["float"],
                )
                return response.embeddings.float[0]

            elif content_type == "image":
                if isinstance(content, str):  # URL
                    async with aiohttp.ClientSession() as session:
                        async with session.get(content) as resp:
                            image_data = await resp.read()
                            content_type = resp.headers["Content-Type"]
                elif isinstance(content, Attachment):
                    image_data = await content.read()
                    content_type = content.content_type
                elif isinstance(content, Path):
                    image_data = content.read_bytes()
                    content_type = "image/jpeg"
                else:
                    raise ValueError(f"Unsupported image source type: {type(content)}")

                stringified_buffer = base64.b64encode(image_data).decode("utf-8")
                image_base64 = f"data:{content_type};base64,{stringified_buffer}"

                response = await self.client.embed(
                    model=self.model_id,
                    input_type="image",
                    embedding_types=["float"],
                    images=[image_base64],
                )
                return response.embeddings.float[0]

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise ValueError(f"Error generating embedding: {str(e)}")

    async def generate(
        self,
        inputs: Union[List[str], List[Union[Path, Attachment]]],
        input_type: str = "search_document",
        embedding_types: Optional[List[str]] = None,
        truncate: str = "END",
        return_raw: bool = False,
    ) -> Union[Dict[str, Any], List[List[float]]]:
        """Generate embeddings for multiple inputs."""
        if embedding_types is None:
            embedding_types = ["float"]

        try:
            if input_type == "search_document":
                response = await self.client.embed(
                    texts=inputs,
                    model=self.model_id,
                    input_type=input_type,
                    embedding_types=embedding_types,
                    truncate=truncate,
                )
                return response if return_raw else response.embeddings.float

            elif input_type == "image":
                image_base64_list = []
                for image in inputs:
                    if isinstance(image, Attachment):
                        image_data = await image.read()
                        content_type = image.content_type
                    elif isinstance(image, Path):
                        image_data = image.read_bytes()
                        content_type = "image/jpeg"
                    else:
                        raise ValueError(f"Unsupported image type: {type(image)}")

                    stringified_buffer = base64.b64encode(image_data).decode("utf-8")
                    image_base64 = f"data:{content_type};base64,{stringified_buffer}"
                    image_base64_list.append(image_base64)

                response = await self.client.embed(
                    model=self.model_id,
                    input_type="image",
                    embedding_types=embedding_types,
                    images=image_base64_list,
                )
                return response if return_raw else response.embeddings.float

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise ValueError(f"Error generating embeddings: {str(e)}")
