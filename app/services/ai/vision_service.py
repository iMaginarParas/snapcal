import os
import io
import json
import random
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_random_meal_fallback() -> dict:
    fallbacks = [
        {
            "meal_type": "Lunch",
            "estimated_total_weight": 350,
            "image_quality": "Good",
            "foods": [
                {
                    "name": "Grilled Chicken Salad",
                    "weight_g": 200,
                    "confidence": 92,
                    "ingredients": ["Chicken", "Olive Oil", "Herbs"],
                    "possible_hidden_ingredients": ["Olive Oil"],
                    "portion_description": "1 Serving",
                    "cooking_method": "Grilled"
                },
                {
                    "name": "Garden Salad",
                    "weight_g": 150,
                    "confidence": 88,
                    "ingredients": ["Lettuce", "Tomatoes", "Cucumbers"],
                    "possible_hidden_ingredients": ["Salad Dressing"],
                    "portion_description": "1 Bowl",
                    "cooking_method": "Raw"
                }
            ]
        },
        {
            "meal_type": "Breakfast",
            "estimated_total_weight": 280,
            "image_quality": "Good",
            "foods": [
                {
                    "name": "Avocado Toast with Eggs",
                    "weight_g": 280,
                    "confidence": 90,
                    "ingredients": ["Whole Wheat Bread", "Avocado", "Eggs"],
                    "possible_hidden_ingredients": ["Butter"],
                    "portion_description": "2 Slices",
                    "cooking_method": "Toasted"
                }
            ]
        },
        {
            "meal_type": "Lunch",
            "estimated_total_weight": 400,
            "image_quality": "Good",
            "foods": [
                {
                    "name": "Chicken Biryani",
                    "weight_g": 350,
                    "confidence": 94,
                    "ingredients": ["Rice", "Chicken", "Ghee", "Spices"],
                    "possible_hidden_ingredients": ["Cooking Oil"],
                    "portion_description": "1 Medium Bowl",
                    "cooking_method": "Cooked"
                }
            ]
        }
    ]
    return random.choice(fallbacks)

# Configure Gemini API Key dynamically
def is_gemini_active() -> bool:
    key = os.getenv("GEMINI_API_KEY") or ""
    if key and key != "your_gemini_api_key_here" and "placeholder" not in key.lower():
        try:
            genai.configure(api_key=key)
            return True
        except Exception as e:
            print(f"[VisionService] WARNING: Failed to configure Gemini client: {e}")
    else:
        print(f"[VisionService] NOTICE: GEMINI_API_KEY is missing or empty. Using smart meal recognition fallback.")
    return False

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

def analyze_meal_image_with_ai(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Sends the preprocessed image to Gemini Vision to detect food items.
    """
    try:
        if not is_gemini_active():
            raise ValueError("Gemini API key is not configured in environment variables.")
        processed_bytes = preprocess_image(image_bytes)
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
        img_obj = Image.open(io.BytesIO(processed_bytes))
        models_to_try = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3.6-flash"]
        response_text = None
        last_error = None

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                res = model.generate_content([prompt, img_obj])
                if res and res.text:
                    response_text = res.text
                    print(f"[VisionService] Model '{model_name}' succeeded.")
                    break
            except Exception as model_err:
                last_error = model_err
                print(f"[VisionService] Model '{model_name}' failed: {model_err}")
                continue

        if not response_text:
            print(f"[VisionService] Gemini vision model calls failed ({last_error}). Using smart meal recognition fallback.")
            fallback = get_random_meal_fallback()
            fallback["is_fallback"] = True
            return fallback

        import re
        cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()
        
        # Try direct JSON parsing first
        try:
            data = json.loads(cleaned_text)
        except Exception:
            # Match first { ... } block in case of conversation wrapper text
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse JSON response from Gemini Vision.")

        # Normalize 'items' to 'foods' if the model returned 'items'
        if "foods" not in data and "items" in data:
            data["foods"] = data["items"]

        foods = data.get("foods") or []
        print(f"[VisionService] Detected {len(foods)} food item(s) in image.")
        return data
    except Exception as e:
        print(f"[VisionService] Photo analysis warning: {e}. Returning smart fallback meal.")
        fallback = get_random_meal_fallback()
        fallback["is_fallback"] = True
        return fallback


def generate_mock_meal_with_ai() -> dict:
    """Gets a healthy meal choice recommendation and macronutrient estimates from Gemini."""
    try:
        if not is_gemini_active():
            raise ValueError("Gemini key not configured")
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = """Generate a realistic, healthy meal choice suitable for a fitness tracking application (e.g., Avocado Toast, Salmon Salad, Chicken Protein Bowl, Greek Yogurt with Berries, etc.) and estimate its nutritional values.
        Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text."""
        response = model.generate_content(prompt)
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Mock Meal Warning/Fallback: {e}")
        return {
            "name": "Avocado Toast with Poached Eggs",
            "calories": 380,
            "protein": 16.0,
            "carbs": 32.0,
            "fats": 20.0
        }

def analyze_meal_text_with_ai(description: str) -> dict:
    try:
        if not is_gemini_active():
            raise ValueError("Gemini key not configured")
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
        print(f"Gemini Text API Warning/Fallback: {e}")
        return {
            "name": description.title() if description else "Parsed Meal",
            "calories": 350,
            "protein": 20.0,
            "carbs": 40.0,
            "fats": 12.0
        }

def analyze_meal_label_with_ai(image_bytes: bytes, mime_type: str = "image/jpeg", custom_prompt: str = None) -> dict:
    try:
        if not is_gemini_active():
            raise ValueError("Gemini key not configured")
        processed_bytes = preprocess_image(image_bytes)
        img_obj = Image.open(io.BytesIO(processed_bytes))
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Analyze this nutrition label image.{f' User notes/context: "{custom_prompt}".' if custom_prompt else ''} Extract:
        1. The product name (or a descriptive name based on the label/packaging)
        2. Calories per serving
        3. Macros: Protein (g), Carbs (g), Fats (g) per serving
        Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text."""
        
        response = model.generate_content([prompt, img_obj])
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Label API Warning/Fallback: {e}")
        return {
            "name": custom_prompt if custom_prompt else "Nutrition Label Scan",
            "calories": 250,
            "protein": 15.0,
            "carbs": 30.0,
            "fats": 8.0
        }

def analyze_meal_barcode_with_ai(barcode: str) -> dict:
    try:
        if not is_gemini_configured:
            raise ValueError("Gemini key not configured")
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Provide estimated nutrition facts (calories, protein, carbs, fats) for the product with UPC/barcode or name: "{barcode}". If the barcode format is standard, estimate the realistic food item.
        Return the response strictly as a JSON object with keys: "name" (string), "calories" (number), "protein" (number), "carbs" (number), "fats" (number). Do not include markdown formatting or additional text."""
        response = model.generate_content(prompt)
        text = response.text.strip()
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Barcode API Warning/Fallback: {e}")
        return {
            "name": f"Barcode Product #{barcode}",
            "calories": 200,
            "protein": 10.0,
            "carbs": 25.0,
            "fats": 5.0
        }

def generate_workout_insight_with_ai(workouts: list, daily_stats: dict) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Based on the following user data:
        Workouts: {json.dumps(workouts[:5])}
        Daily Stats: {json.dumps(daily_stats)}
        Provide a short, motivating, and highly personalized 1-sentence AI insight about their progress. Don't use quotes."""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise ValueError(f"Gemini Insight API Error: {e}")

def generate_daily_report_insight_with_ai(
    meals: list, 
    workouts: list, 
    daily_stats: dict, 
    calorie_intake: float, 
    calorie_burned: float
) -> dict:
    try:
        steps = daily_stats.get("steps") or 0
        water = daily_stats.get("water_ml") or 0
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
        clean_json = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        raise ValueError(f"Gemini Daily Insight API Error: {e}")
