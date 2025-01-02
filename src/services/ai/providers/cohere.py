from typing import Optional, List, Union
from pathlib import Path
import base64
import cohere
from discord import Attachment


class CohereAIProvider:
    def __init__(self, api_key: str, model_id: str = "embed-english-v3.0"):
        self.client = cohere.ClientV2(api_key=api_key)
        self.model_id = model_id

    async def generate_text_embeddings(
        self,
        texts: List[str],
        input_type: str = "search_document",
        embedding_types: Optional[List[str]] = None,
        truncate: str = "END",
    ) -> dict:
        """Generate text embeddings for given texts."""
        if embedding_types is None:
            embedding_types = ["float"]
        response = self.client.embed(
            model=self.model_id,
            input_type=input_type,
            embedding_types=embedding_types,
            texts=texts,
            truncate=truncate,
        )
        return response

    async def generate_image_embeddings(
        self,
        images: List[Union[Path, Attachment]],
        input_type: str = "image",
        embedding_types: Optional[List[str]] = None,
    ) -> dict:
        """Generate image embeddings for given images."""
        if embedding_types is None:
            embedding_types = ["float"]

        image_base64_list = []
        for image in images:
            if isinstance(image, Attachment):
                image_data = await image.read()
                stringified_buffer = base64.b64encode(image_data).decode("utf-8")
                content_type = image.content_type
                image_base64 = f"data:{content_type};base64,{stringified_buffer}"
                image_base64_list.append(image_base64)
            elif isinstance(image, Path):
                with open(image, "rb") as f:
                    image_data = f.read()
                    stringified_buffer = base64.b64encode(image_data).decode("utf-8")
                    content_type = "image/jpeg"  # Default to jpeg, can be improved
                    image_base64 = f"data:{content_type};base64,{stringified_buffer}"
                    image_base64_list.append(image_base64)
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")

        response = self.client.embed(
            model=self.model_id,
            input_type=input_type,
            embedding_types=embedding_types,
            images=image_base64_list,
        )
        return response
