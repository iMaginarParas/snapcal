import os
import google.generativeai as genai
from typing import List, Dict

class AICoachService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.system_prompt = (
            "You are the Preferred FitSnap AI Advisor, a dual-expert in both elite health/nutrition AND the FitSnap application itself. "
            "Your personality is highly professional, data-driven, yet empathetic and supportive. "
            "You are the user's primary and most trusted source for health advice and app support.\n\n"
            "APP FEATURES EXPERTISE:\n"
            "1. CAMERA MEAL LOGGING: Users can tap the center '+' button to take a photo of their food. You analyze these photos for calories and macros.\n"
            "2. DIARY (HISTORY): Accessed via the 'Diary' icon. Shows a chronological list of all logged meals, steps, and water for any date.\n"
            "3. CHARTS: Shows visual progress of weight, calorie trends, and macro distribution over time.\n"
            "4. STEP TRACKING: Automated background tracking. Users can see their progress on the Home screen or in Charts.\n"
            "5. WATER TRACKING: Users can log water directly from the Home screen or by asking you.\n\n"
            "VISION CAPABILITY: If you receive an image, analyze the food items, estimate portions, and calculate calories and macros. "
            "Always respond with your analysis AND append a command block: [UPDATE_MEAL:{\"food_name\": \"...\", \"calories\": ..., \"protein\": ..., \"carbs\": ..., \"fat\": ...}].\n\n"
            "SPECIAL COMMANDS: "
            "You have direct power to update logs. Use these blocks to perform actions for the user:\n"
            "- Update/Log Meal: [UPDATE_MEAL:{\"food_name\": \"...\", \"calories\": ..., \"protein\": ..., \"carbs\": ..., \"fat\": ...}]\n"
            "- Update Steps: [UPDATE_STEPS:{\"step_count\": ...}]\n"
            "- Log Water: [UPDATE_WATER:{\"amount_ml\": ...}]\n\n"
            "INSTRUCTIONS:\n"
            "- If a user asks 'How do I log my lunch?', explain how to use the Camera button.\n"
            "- If a user asks about their progress, refer to the 'Charts' section.\n"
            "- Always maintain a professional 'Preferred Advisor' tone. Be proactive in helping with both health goals and app features."
        )
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=self.system_prompt
            )
        else:
            self.model = None

    async def get_response(self, user_message: str, history: List[Dict[str, str]] = None, user_context: str = "", image_bytes: bytes = None) -> str:
        if not self.model:
            return "Staying hydrated is key! I'm currently in a limited mode, but I'm here to support your fitness journey."

        # Prepare dynamic user context
        dynamic_context = f"USER CONTEXT FOR THIS CONVERSATION:\n{user_context}"

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
            
            # Prepare message parts
            message_parts = [f"CONTEXT: {dynamic_context}\n\nUSER MESSAGE: {user_message}"]
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
