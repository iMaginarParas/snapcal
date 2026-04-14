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

    async def get_response(self, user_message: str, history: List[Dict[str, str]] = None, user_context: str = "") -> str:
        if not self.model:
            return "Staying hydrated is key! I'm currently in a limited mode, but I'm here to support your fitness journey."

        # Prepare context with correction capabilities
        system_prompt = (
            "You are FitSnap AI Coach, an elite health and nutrition expert. "
            "Your personality is highly professional, data-driven, yet empathetic and supportive. "
            "You focus on helping users maintain their calorie deficit or surplus goals and optimizing macro-nutrients.\n\n"
            "KNOWLEDGE OF TODAY: You have real-time access to the user's calories, steps, and water intake for today. "
            "Use this data to give specific advice (e.g., 'You've only had 500ml of water, try to drink more' or 'You have 400 calories left for dinner').\n\n"
            "SPECIAL CAPABILITY: You can correct meal logs if the user indicates a mistake.\n"
            "If you determine the user wants to update a meal (e.g., 'that wasn't a burger, it was a salad' or 'calories should be 400'), "
            "append a command block at the end of your message in this format: [UPDATE_MEAL:{\"food_name\": \"New Name\", \"calories\": 400}].\n"
            "Only include fields that need changing. For example, if they only change the name, use [UPDATE_MEAL:{\"food_name\": \"Salad\"}].\n"
            "If they say 'the AI got it wrong', ask what the correct details are.\n\n"
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
            
            response = chat.send_message(f"{system_prompt}\n\nUser: {user_message}")
            return response.text
        except Exception as e:
            print(f"AI Service Error: {e}")
            return "I'm having a bit of trouble processing that right now. Could you please try again?"

ai_coach_service = AICoachService()
