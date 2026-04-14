import os
import google.generativeai as genai
from typing import List, Dict

class AICoachService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def get_response(self, user_message: str, history: List[Dict[str, str]] = None, user_context: str = "", image_bytes: bytes = None) -> str:
        if not self.model:
            return "Staying hydrated is key! I'm currently in a limited mode, but I'm here to support your fitness journey."

        # Prepare context with Vision and Coaching capabilities
        system_prompt = (
            "You are FitSnap AI Coach, an elite health and nutrition expert with VISION capabilities. "
            "Your personality is highly professional, data-driven, yet empathetic and supportive.\n\n"
            "VISION CAPABILITY: If you receive an image, analyze the food items, estimate portions, and calculate calories and macros. "
            "Always respond with your analysis AND append a command block: [UPDATE_MEAL:{\"food_name\": \"...\", \"calories\": ..., \"protein\": ..., \"carbs\": ..., \"fat\": ...}].\n\n"
            "HISTORICAL ANALYSIS: Use the user's historical context provided below to notice trends (weight loss, calorie intake habits) and comment on them positively or with corrective advice.\n\n"
            "SPECIAL COMMANDS: "
            "Update any log: [UPDATE_MEAL:{...}], [UPDATE_STEPS:{\"step_count\": ...}], [UPDATE_WATER:{\"amount_ml\": ...}].\n\n"
            "Be encouraging but firm about health goals.\n\n"
            f"USER CONTEXT FOR THIS CONVERSATION:\n{user_context}"
        )
        )

        try:
            # Construct chat
            chat = self.model.start_chat(history=[])
            
            # Add history if provided (convert roles to gemini format: 'user' and 'model')
            gemini_history = []
            if history:
                for msg in history:
                    gemini_history.append({
                        "role": "user" if msg["role"] == "user" else "model",
                        "parts": [msg["content"]]
                    })
            
            # Re-initialize chat with history
            chat = self.model.start_chat(history=gemini_history)
            
            message_parts = [f"{system_prompt}\n\nUser: {user_message}"]
            if image_bytes:
                message_parts.append({
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                })
            
            response = chat.send_message(message_parts)
            return response.text
        except Exception as e:
            print(f"AI Service Error: {e}")
            return "I'm having a bit of trouble processing that right now. Could you please try again?"

ai_coach_service = AICoachService()
