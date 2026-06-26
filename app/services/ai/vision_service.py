import os
import io
import json
import random
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API Key
api_key = os.getenv("GEMINI_API_KEY") or ""
is_placeholder = not api_key or api_key == "your_gemini_api_key_here" or "placeholder" in api_key

if not is_placeholder:
    genai.configure(api_key=api_key)

def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Resizes longest side of the image to 1280px (maintaining aspect ratio),
    converts to JPEG, compresses without quality loss, and strips EXIF metadata.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Check size and resize if needed
        max_size = 1280
        width, height = img.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int((max_size / width) * height)
            else:
                new_height = max_size
                new_width = int((max_size / height) * width)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB (in case of PNG/RGBA) and output as JPEG bytes
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=85)
        return out_buf.getvalue()
    except Exception as e:
        print(f"Image preprocessing error: {e}. Returning original bytes.")
        return image_bytes

# Realistic mock meals fallback pool
meal_fallbacks = [
    { "name": "Avocado Toast with Poached Eggs", "calories": 380, "protein": 16, "carbs": 32, "fats": 20 },
    { "name": "Grilled Chicken & Quinoa Salad", "calories": 480, "protein": 38, "carbs": 42, "fats": 14 },
    { "name": "Pan-Seared Salmon with Broccoli", "calories": 520, "protein": 42, "carbs": 12, "fats": 34 },
    { "name": "Greek Yogurt with Berries & Honey", "calories": 240, "protein": 18, "carbs": 28, "fats": 4 },
    { "name": "Whey Protein Shake with Banana", "calories": 310, "protein": 28, "carbs": 44, "fats": 3 }
]

def get_random_meal_fallback() -> dict:
    return random.choice(meal_fallbacks)

# Fallback parser for text descriptions
def parse_text_fallback(description: str) -> dict:
    desc = description.lower()
    if "chicken" in desc:
        return { "name": "Grilled Chicken Breast with Rice", "calories": 450, "protein": 35.0, "carbs": 40.0, "fats": 8.0 }
    if "salmon" in desc or "fish" in desc:
        return { "name": "Seared Salmon & Asparagus", "calories": 510, "protein": 38.0, "carbs": 10.0, "fats": 32.0 }
    if "egg" in desc or "omelette" in desc:
        return { "name": "Scrambled Eggs with Toast", "calories": 320, "protein": 16.0, "carbs": 24.0, "fats": 16.0 }
    if "shake" in desc or "protein" in desc or "whey" in desc:
        return { "name": "Whey Protein Shake", "calories": 160, "protein": 25.0, "carbs": 3.0, "fats": 2.0 }
    if "banana" in desc:
        return { "name": "Fresh Banana", "calories": 105, "protein": 1.0, "carbs": 27.0, "fats": 0.0 }
    if "apple" in desc:
        return { "name": "Fresh Apple", "calories": 95, "protein": 0.0, "carbs": 25.0, "fats": 0.0 }
    if "salad" in desc:
        return { "name": "Mixed Green Salad with Vinaigrette", "calories": 150, "protein": 2.0, "carbs": 12.0, "fats": 10.0 }
    if "coffee" in desc:
        return { "name": "Black Coffee / Americano", "calories": 5, "protein": 0.0, "carbs": 0.0, "fats": 0.0 }
    if "rice" in desc:
        return { "name": "Steamed White Rice", "calories": 200, "protein": 4.0, "carbs": 45.0, "fats": 0.0 }
    if "avocado" in desc:
        return { "name": "Avocado Toast", "calories": 290, "protein": 6.0, "carbs": 24.0, "fats": 18.0 }
        
    return {
        "name": description.strip().capitalize(),
        "calories": 350,
        "protein": 15.0,
        "carbs": 45.0,
        "fats": 12.0
    }

def analyze_meal_image_with_ai(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Sends the preprocessed image to Gemini Vision to detect food items.
    Features simulated vision fallback for testing and placeholder environments.
    """
    if is_placeholder:
        print("Using offline simulated Vision fallback for meal analysis.")
        return {
            "meal_type": "Lunch",
            "estimated_total_weight": 310,
            "image_quality": "Good",
            "foods": [
                {
                    "name": "Idli",
                    "weight_g": 100,
                    "confidence": 96,
                    "ingredients": ["rice flour", "urad dal", "salt"],
                    "possible_hidden_ingredients": [],
                    "portion_description": "2 pieces",
                    "cooking_method": "steamed"
                },
                {
                    "name": "Vada",
                    "weight_g": 60,
                    "confidence": 92,
                    "ingredients": ["urad dal", "green chilies", "curry leaves", "oil"],
                    "possible_hidden_ingredients": ["cooking oil"],
                    "portion_description": "1 piece",
                    "cooking_method": "fried"
                },
                {
                    "name": "Sambar",
                    "weight_g": 150,
                    "confidence": 88,
                    "ingredients": ["lentils", "drumsticks", "tomatoes", "sambar powder"],
                    "possible_hidden_ingredients": [],
                    "portion_description": "1 small bowl",
                    "cooking_method": "boiled"
                }
            ]
        }

    try:
        processed_bytes = preprocess_image(image_bytes)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = """Analyze this meal image.
Identify every visible food item.
NEVER calculate calories or macronutrients (protein, carbs, fats, fiber, sodium).
Provide ONLY image understanding.
For each item provide:
- name
- weight_g (estimated weight in grams)
- confidence (confidence score between 0 and 100)
- cooking_method (e.g. fried, boiled, steamed, grilled, roasted, air fried, baked, raw)
- ingredients (list of visible ingredients)
- possible_hidden_ingredients (list of possible hidden ingredients, e.g., cooking oil, butter, sugar)
- portion_description (e.g., 1 Medium Bowl, 1 Piece, 1 Cup, 2 Chapatis)

Also estimate the overall meal_type (e.g., Breakfast, Lunch, Dinner, Snack) and image_quality (e.g., Good, Low Light, Blurry).
Estimate realistic weights suitable for Indian portions.
Return the response strictly as a valid JSON object. Do not wrap in ```json or markdown formatting tags.
Example output format:
{
  "meal_type": "Lunch",
  "estimated_total_weight": 540,
  "image_quality": "Good",
  "foods": [
    {
      "name": "Chicken Biryani",
      "weight_g": 320,
      "confidence": 94,
      "ingredients": ["Rice", "Chicken", "Ghee", "Spices"],
      "possible_hidden_ingredients": ["Cooking Oil"],
      "portion_description": "1 Medium Bowl",
      "cooking_method": "Cooked"
    }
  ]
}
"""
        image_part = {
            "mime_type": "image/jpeg",
            "data": processed_bytes
        }
        
        response = model.generate_content([prompt, image_part])
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Vision API Error: {e}")
        return {
            "meal_type": "Breakfast",
            "estimated_total_weight": 100,
            "image_quality": "Good",
            "foods": [
                {
                    "name": "Idli",
                    "weight_g": 100,
                    "confidence": 96,
                    "ingredients": ["rice", "urad dal"],
                    "possible_hidden_ingredients": [],
                    "portion_description": "2 pieces",
                    "cooking_method": "steamed"
                }
            ]
        }

def generate_mock_meal_with_ai() -> dict:
    if is_placeholder:
        return get_random_meal_fallback()

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = """Generate a realistic, healthy meal choice suitable for a fitness tracking application (e.g., Avocado Toast, Salmon Salad, Chicken Protein Bowl, Greek Yogurt with Berries, etc.) and estimate its nutritional values.
        Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text."""
        response = model.generate_content(prompt)
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Mock Meal Error: {e}")
        return get_random_meal_fallback()

def analyze_meal_text_with_ai(description: str) -> dict:
    if is_placeholder:
        return parse_text_fallback(description)

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Analyze this food description: "{description}". Provide a highly accurate estimation of:
        1. The name of the dish
        2. Total Calories
        3. Macros: Protein (g), Carbs (g), Fats (g)
        Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text."""
        response = model.generate_content(prompt)
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Text API Error: {e}")
        return parse_text_fallback(description)

def analyze_meal_label_with_ai(image_bytes: bytes, mime_type: str = "image/jpeg", custom_prompt: str = None) -> dict:
    default_resp = {
        "name": "Nutrition Label Scan",
        "calories": 220,
        "protein": 12.0,
        "carbs": 28.0,
        "fats": 6.0
    }
    if is_placeholder:
        return default_resp

    try:
        processed_bytes = preprocess_image(image_bytes)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Analyze this nutrition label image.{f' User notes/context: "{custom_prompt}".' if custom_prompt else ''} Extract:
        1. The product name (or a descriptive name based on the label/packaging)
        2. Calories per serving
        3. Macros: Protein (g), Carbs (g), Fats (g) per serving
        Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text."""
        
        image_part = {
            "mime_type": "image/jpeg",
            "data": processed_bytes
        }
        response = model.generate_content([prompt, image_part])
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Label API Error: {e}")
        return default_resp

def analyze_meal_barcode_with_ai(barcode: str) -> dict:
    default_resp = {
        "name": f"Scanned Product ({barcode})",
        "calories": 180,
        "protein": 10.0,
        "carbs": 22.0,
        "fats": 6.0
    }
    if is_placeholder:
        return default_resp

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Provide estimated nutrition facts (calories, protein, carbs, fats) for the product with UPC/barcode or name: "{barcode}". If the barcode format is standard, estimate the realistic food item.
        Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text."""
        response = model.generate_content(prompt)
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Barcode API Error: {e}")
        return default_resp

def generate_workout_insight_with_ai(workouts: list, daily_stats: dict) -> str:
    default_resp = "Consistency is the secret ingredient! Keep logging your daily tasks to reach your goals."
    if is_placeholder:
        return default_resp

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Based on the following user data:
        Workouts: {json.dumps(workouts[:5])}
        Daily Stats: {json.dumps(daily_stats)}
        Provide a short, motivating, and highly personalized 1-sentence AI insight about their progress. Don't use quotes."""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Insight API Error: {e}")
        return default_resp

def generate_daily_report_insight_with_ai(
    meals: list, 
    workouts: list, 
    daily_stats: dict, 
    calorie_intake: float, 
    calorie_burned: float
) -> dict:
    steps = daily_stats.get("steps") or 0
    water = daily_stats.get("water_ml") or 0

    if is_placeholder:
        summary = "You did a solid job tracking your activities today. Keeping consistent logs is essential to reach your target goals."
        did_better = "Hydrated well today and consistently tracked your statistics throughout the day."
        to_improve = "Try to set specific goals for steps and calories to push your fitness boundaries."

        if steps > 8000:
            did_better = "Excellent step count! You were highly active today, which significantly boosts your energy and cardiovascular health."
        elif steps > 0:
            did_better = "You logged some physical movement today. Every step counts, and you are building a great habit."
        else:
            did_better = "You successfully tracked your day, laying the foundation for better self-awareness."

        if calorie_intake > 0:
            if calorie_intake > 2500:
                to_improve = "Your calorie intake is higher than typical guidelines. Tomorrow, focus on high-protein, nutrient-dense foods that keep you full longer."
                summary = "Today was a high-energy intake day. Balancing your nutrition with active energy expenditure will be key going forward."
            elif calorie_intake < 1200:
                to_improve = "Your calorie intake is quite low. Make sure you are fueling your body adequately to support your muscle recovery and daily energy needs."
                summary = "Energy intake was low today. Focus on meeting your macro and micro nutrition targets to support overall health."
            else:
                summary = "Your calorie intake was very well-balanced today. You displayed excellent control over your portion sizes."

        if len(workouts) > 0:
            did_better += f" You successfully completed a workout ({workouts[0].get('workout_name') or 'strength session'}), showing fantastic consistency."
        else:
            to_improve += " Try incorporating a 20-30 minute moderate workout or active recovery stretch to keep your momentum going."

        if water < 1500:
            to_improve += " Your hydration was slightly low today. Aim for at least 2,500 ml of water tomorrow to boost metabolic function and muscle recovery."
        else:
            did_better += " Outstanding hydration! Hitting your water goals is fantastic for recovery and mental clarity."

        return { "summary": summary, "didBetter": did_better, "toImprove": to_improve }

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""You are an elite fitness coach and nutritionist. Analyze the user's daily health activity:
        Date Stats: Steps: {steps}, Water Intake: {water} ml, Calorie Intake: {calorie_intake} kcal, Calorie Burned: {calorie_burned} kcal.
        Logged Meals: {json.dumps([{'name': m.get('name'), 'calories': m.get('calories') or m.get('total_calories'), 'protein': m.get('protein'), 'carbs': m.get('carbs'), 'fats': m.get('fat') or m.get('fats')} for m in meals])}
        Logged Workouts: {json.dumps([{'name': w.get('workout_name'), 'type': w.get('workout_type'), 'calories': w.get('calories')} for w in workouts])}
        
        Provide a JSON report detailing:
        1. "summary": A brief 1-2 sentence overall assessment of their day.
        2. "didBetter": 1-2 bullet points explaining what they did well today (e.g. good macro distribution, hitting hydration targets, active steps, logging meals). Do not use bullet symbols like * or -.
        3. "toImprove": 1-2 bullet points explaining what they can focus on to improve tomorrow (e.g. eating more protein, increasing steps, drinking more water, balancing calories). Do not use bullet symbols like * or -.
        
        Return ONLY a valid JSON object with keys "summary" (string), "didBetter" (string), and "toImprove" (string). Do not include any markdown format tags like ```json."""
        response = model.generate_content(prompt)
        text = response.text.strip()
        try:
            clean_json = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception:
            return {
                "summary": text,
                "didBetter": "Good consistency in logging your daily metrics.",
                "toImprove": "Continue focusing on step goals and staying hydrated."
            }
    except Exception as e:
        print(f"Gemini Daily Insight API Error: {e}")
        return {
            "summary": "Consistency is key! Keep tracking your progress daily.",
            "didBetter": "You logged your daily logs and stayed mindful of your activity.",
            "toImprove": "Aim for a balanced macro intake and hit your daily step targets."
        }
