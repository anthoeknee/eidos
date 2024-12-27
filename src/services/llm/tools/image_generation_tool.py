from typing import Dict, Any
from src.services.llm.tools.base import BaseTool
from src.core.config import settings
from src.utils import logger
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel
import base64


log = logger.setup_logger(__name__)


class ImageGenerationTool(BaseTool):
    """Tool that generates images using the Gemini API."""

    def __init__(self):
        """Initialize the image generation tool."""
        super().__init__(
            name="generate_image",
            description="Generates an image based on a text prompt.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "prompt": {
                        "type": "STRING",
                        "description": "The text prompt to generate the image from.",
                    },
                    "number_of_images": {
                        "type": "INTEGER",
                        "description": "The number of images to generate.",
                    },
                    "aspect_ratio": {
                        "type": "STRING",
                        "description": "The aspect ratio of the image.",
                        "enum": ["1:1", "3:4", "4:3", "9:16", "16:9"],
                    },
                },
                "required": ["prompt"],
            },
        )
        try:
            # Initialize Vertex AI
            aiplatform.init(
                project=settings.gcp_project_id, location=settings.gcp_region
            )
            self.model = GenerativeModel(model_name="gemini-2.0-flash-exp")
            # Use the ImageGenerationModel from vertexai.preview.vision_models
            from vertexai.preview.vision_models import ImageGenerationModel

            self.image_model = ImageGenerationModel.from_pretrained(
                "imagen-3.0-fast-generate-001"
            )
        except Exception as e:
            log.error(f"Error initializing Vertex AI: {e}")
            self.image_model = None

    async def execute(self, args: Dict[str, Any]) -> Any:
        """Generate an image based on the given prompt.

        Args:
            args: A dictionary containing the prompt and optional parameters.

        Returns:
            A list of base64 encoded images.
        """
        if not self.image_model:
            return "Sorry, the image generation tool is not available due to initialization errors."

        prompt = args.get("prompt")
        number_of_images = args.get("number_of_images", 1)
        aspect_ratio = args.get("aspect_ratio", "1:1")

        if not prompt:
            return "A text prompt is required to generate an image."

        try:
            images = self.image_model.generate_images(
                prompt=prompt,
                number_of_images=number_of_images,
                aspect_ratio=aspect_ratio,
                safety_filter_level="block_low_and_above",
            )

            base64_images = []
            for image in images:
                image_bytes = image._image_bytes
                base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
                base64_images.append(base64_encoded)

            return base64_images

        except Exception as e:
            log.error(f"Error generating image: {e}")
            return f"Sorry, I encountered an error generating the image: {e}"
