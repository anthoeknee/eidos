from typing import Optional, List, Union
from pathlib import Path
import time
import discord
from google import genai
from google.genai import types


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

    async def generate_content(
        self, prompt: str, files: Optional[List[Union[Path, discord.Attachment]]] = None
    ) -> str:
        """Generate content with optional file inputs from paths or Discord attachments"""
        contents = []

        # Handle file uploads if provided
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
                    while file_upload.state == "PROCESSING":
                        time.sleep(5)
                        file_upload = self.client.files.get(name=file_upload.name)
                    if file_upload.state == "FAILED":
                        raise ValueError(f"Video processing failed: {file}")

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
        contents.append(prompt)

        # Generate response
        response = await self.client.aio.models.generate_content(
            model=self.model_id, contents=contents
        )

        return response.text

    def count_tokens(self, content: str) -> int:
        """Count tokens for given content"""
        response = self.client.models.count_tokens(
            model=self.model_id, contents=content
        )
        return response.total_tokens
