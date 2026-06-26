import difflib
from app.repositories.food_repository import food_repository

# Standard pre-defined mappings for common spelling variations and synonyms
COMMON_INDIAN_MAPPINGS = {
    "chicken biriyani": "Chicken Biryani",
    "hyderabadi chicken biryani": "Chicken Biryani",
    "hyderabadi biryani": "Chicken Biryani",
    "mutton biriyani": "Mutton Biryani",
    "butter paneer": "Paneer Butter Masala",
    "paneer butter": "Paneer Butter Masala",
    "paneer tikka masala": "Paneer Tikka Masala",
    "masala dosai": "Masala Dosa",
    "plain dosai": "Plain Dosa",
    "ghee roast dosa": "Plain Dosa",
    "chappathi": "Chapati",
    "roti": "Chapati",
    "phulka": "Chapati",
    "tandoori roti": "Chapati",
    "poori bhaji": "Poori",
    "puri": "Poori",
    "parotta": "Paratha",
    "aloot paratha": "Paratha",
    "ragi ball": "Ragi Mudde",
    "ragi mudda": "Ragi Mudde",
    "upma uppittu": "Upma",
    "uppittu": "Upma",
    "ven pongal": "Pongal",
    "khara pongal": "Pongal",
    "puliyodarai": "Puliyogare",
    "tamarind rice": "Puliyogare",
    "neer dosai": "Neer Dosa",
    "bisi bele bath": "Bisi Bele Bath",
    "bisibelebath": "Bisi Bele Bath",
    "chole bhature": "Chole",
    "rajma chawal": "Rajma",
    "dal tadka": "Dal Tadka",
    "dal fry": "Dal Tadka",
    "yellow dal": "Dal Tadka",
    "sambar bowl": "Sambar",
    "rasam soup": "Rasam",
    "vada pav": "Vada",
    "medu vada": "Vada",
    "idly": "Idli"
}

class FoodNormalizer:
    def normalize(self, raw_name: str) -> str:
        """
        Normalizes a raw food name into its canonical standardized name.
        Looks up cache, aliases in database, custom rules, and fuzzy matches.
        """
        if not raw_name:
            return "Generic Food"
            
        name_clean = raw_name.strip()
        name_lower = name_clean.lower()

        # 1. Check direct dictionary mappings
        if name_lower in COMMON_INDIAN_MAPPINGS:
            return COMMON_INDIAN_MAPPINGS[name_lower]

        # 2. Check Database Aliases table
        alias_match = food_repository.get_alias(name_lower)
        if alias_match:
            return alias_match["standard_name"]

        # 3. Check exact match in Foods table
        food_match = food_repository.get_food_by_name(name_lower)
        if food_match:
            return food_match["name"]

        # 4. Check keyword substring matches (Indian foods fallback)
        if "biryani" in name_lower or "biriyani" in name_lower:
            if "mutton" in name_lower:
                return "Mutton Biryani"
            if "veg" in name_lower:
                return "Veg Biryani"
            return "Chicken Biryani"

        if "dosa" in name_lower or "dosai" in name_lower:
            if "masala" in name_lower:
                return "Masala Dosa"
            if "neer" in name_lower:
                return "Neer Dosa"
            return "Plain Dosa"

        if "roti" in name_lower or "rotti" in name_lower or "chapati" in name_lower or "chappathi" in name_lower:
            if "akki" in name_lower:
                return "Akki Roti"
            return "Chapati"

        if "paneer" in name_lower:
            if "tikka" in name_lower:
                return "Paneer Tikka Masala"
            return "Paneer Butter Masala"

        if "idli" in name_lower or "idly" in name_lower:
            return "Idli"

        if "vada" in name_lower:
            return "Vada"

        if "sambar" in name_lower:
            return "Sambar"

        if "rasam" in name_lower:
            return "Rasam"

        if "pongal" in name_lower:
            return "Pongal"

        if "upma" in name_lower:
            return "Upma"

        # 5. Fuzzy Match against all foods registered in database
        # Fetch standard list of foods for matching
        standard_foods = []
        if is_supabase_live():
            try:
                res = food_repository.search_foods("", limit=100)
                standard_foods = [f["name"] for f in res]
            except Exception:
                pass

        if not standard_foods:
            # Fallback list of standard names
            standard_foods = [
                "Chicken Biryani", "Mutton Biryani", "Veg Biryani",
                "Idli", "Vada", "Plain Dosa", "Masala Dosa", "Neer Dosa", "Akki Roti",
                "Ragi Mudde", "Sambar", "Rasam", "Chapati", "Paratha", "Poori",
                "Upma", "Pongal", "Rajma", "Chole", "Paneer Butter Masala", "Paneer Tikka Masala",
                "Dal Tadka", "Bisi Bele Bath", "Puliyogare", "Mixed Green Salad", "White Rice", "Boiled Egg"
            ]

        # Use difflib close matches
        matches = difflib.get_close_matches(name_clean, standard_foods, n=1, cutoff=0.6)
        if matches:
            return matches[0]

        # Capitalize raw name as fallback standard name
        return name_clean.title()

food_normalizer = FoodNormalizer()
