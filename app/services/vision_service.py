import os
import google.generativeai as genai
import json
from PIL import Image
import io
import asyncio

class VisionService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def analyze_meal(self, image_bytes: bytes):
        if not self.model:
            return None

        prompt = (
            "Analyze this meal image and provide the nutrition facts. "
            "Return ONLY a JSON object with these fields: "
            "food_name (string), calories (number), protein (number), carbs (number), fat (number), portion_size (string). "
            "Be as accurate as possible. If multiple items are present, sum them up."
        )

        try:
            # Prepare the image for Gemini
            image = Image.open(io.BytesIO(image_bytes))
            
            # Call Gemini
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image]
            )
            
            # Parse JSON from response
            text = response.text
            # Clean text in case Gemini adds markdown backticks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
        except Exception as e:
            print(f"Vision Service Error: {e}")
            return None

vision_service = VisionService()
