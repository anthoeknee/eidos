from typing import Optional, List, Union, Any, Dict
from pathlib import Path
import time
import discord
from google import genai
from google.genai import types
import base64
import cohere
from discord import Attachment


class GoogleAIProvider:
    def __init__(self, api_key: str, model_id: str = "gemini-2.0-flash-exp"):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

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
        self.client = cohere.ClientV2(api_key=api_key)
        self.model_id = model_id

    async def generate(
        self,
        inputs: Union[List[str], List[Union[Path, Attachment]]],
        input_type: str = "auto",
        embedding_types: Optional[List[str]] = None,
        truncate: str = "END",
        return_raw: bool = False,
    ) -> Union[Dict[str, Any], cohere.responses.EmbedResponse]:
        """
        Unified method to generate embeddings for text or images.
        Returns either the raw response object or just the embedding data.
        """
        if embedding_types is None:
            embedding_types = ["float"]

        if input_type == "auto":
            if isinstance(inputs[0], str):
                input_type = "search_document"
            elif isinstance(inputs[0], (Path, Attachment)):
                input_type = "image"
            else:
                raise ValueError(f"Unsupported input type: {type(inputs[0])}")

        if input_type == "search_document":
            try:
                response = await self.client.embed(
                    model=self.model_id,
                    input_type="search_document",
                    embedding_types=embedding_types,
                    texts=inputs,
                    truncate=truncate,
                )
            except Exception as e:
                raise ValueError(f"Error generating text embeddings: {e}")
            return response if return_raw else response.embeddings

        elif input_type == "image":
            image_base64_list = []
            for image in inputs:
                if isinstance(image, Attachment):
                    image_data = await image.read()
                    stringified_buffer = base64.b64encode(image_data).decode("utf-8")
                    content_type = image.content_type
                    image_base64 = f"data:{content_type};base64,{stringified_buffer}"
                    image_base64_list.append(image_base64)
                elif isinstance(image, Path):
                    with open(image, "rb") as f:
                        image_data = f.read()
                        stringified_buffer = base64.b64encode(image_data).decode(
                            "utf-8"
                        )
                        content_type = "image/jpeg"  # Default to jpeg, can be improved
                        image_base64 = (
                            f"data:{content_type};base64,{stringified_buffer}"
                        )
                        image_base64_list.append(image_base64)
                else:
                    raise ValueError(f"Unsupported image type: {type(image)}")
            try:
                response = await self.client.embed(
                    model=self.model_id,
                    input_type="image",
                    embedding_types=embedding_types,
                    images=image_base64_list,
                )
            except Exception as e:
                raise ValueError(f"Error generating image embeddings: {e}")
            return response if return_raw else response.embeddings
        else:
            raise ValueError(f"Unsupported input type: {input_type}")
