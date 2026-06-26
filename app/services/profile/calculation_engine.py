from typing import Dict, Any, Tuple

class CalculationEngine:
    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> Tuple[float, str]:
        """Calculates BMI and returns (bmi_value, bmi_category)."""
        if height_cm <= 0 or weight_kg <= 0:
            return 0.0, "Unknown"
        
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m * height_m)
        bmi = round(bmi, 1)
        
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25.0:
            category = "Healthy"
        elif bmi < 30.0:
            category = "Overweight"
        else:
            category = "Obese"
            
        return bmi, category

    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
        """Calculates BMR using the Mifflin-St Jeor Equation."""
        if weight_kg <= 0 or height_cm <= 0 or age <= 0:
            return 0.0
            
        if gender.lower() == "female":
            bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) - 161.0
        else:
            bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + 5.0
            
        return round(bmr, 1)

    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> float:
        """Calculates TDEE based on activity multiplier."""
        multiplier_map = {
            "sedentary": 1.20,
            "lightly active": 1.375,
            "light activity": 1.375,
            "moderately active": 1.55,
            "moderate activity": 1.55,
            "very active": 1.725,
            "athlete": 1.90
        }
        
        level = (activity_level or "").strip().lower()
        multiplier = multiplier_map.get(level, 1.20)
        tdee = bmr * multiplier
        return round(tdee, 1)

    @staticmethod
    def calculate_target_calories(tdee: float, goal: str) -> int:
        """Calculates calorie target with a safe healthy floor of 1200 kcal."""
        goal_lower = (goal or "").strip().lower()
        
        if "lose" in goal_lower:
            calories = tdee - 500.0
        elif "gain" in goal_lower or "build" in goal_lower:
            calories = tdee + 400.0  # +300 to +500 kcal/day range baseline
        else:
            calories = tdee
            
        # Enforce healthy minimum floor
        if calories < 1200:
            calories = 1200.0
            
        return int(round(calories))

    @staticmethod
    def calculate_macros(target_calories: int, weight_kg: float, goal: str) -> Dict[str, int]:
        """Calculates personalized macros in grams."""
        goal_lower = (goal or "").strip().lower()
        
        # 1. Protein Target
        if "lose" in goal_lower:
            protein_per_kg = 2.1  # 2.0 - 2.2 g/kg
        elif "gain" in goal_lower or "build" in goal_lower:
            protein_per_kg = 2.0  # 1.8 - 2.2 g/kg
        else:
            protein_per_kg = 1.7  # 1.6 - 1.8 g/kg
            
        protein_g = protein_per_kg * weight_kg
        if protein_g < 40:
            protein_g = 40.0 # Standard absolute minimum floor
            
        # 2. Fat Target (25% - 30% of total calories, using 25% base)
        fat_calories = target_calories * 0.25
        fat_g = fat_calories / 9.0
        
        # 3. Carbohydrates Target (Remaining calories)
        protein_calories = protein_g * 4.0
        carb_calories = max(0.0, target_calories - protein_calories - fat_calories)
        carb_g = carb_calories / 4.0
        
        # 4. Fiber Target (14g per 1000 kcal)
        fiber_g = (target_calories / 1000.0) * 14.0
        
        return {
            "protein": int(round(protein_g)),
            "carbs": int(round(carb_g)),
            "fat": int(round(fat_g)),
            "fiber": int(round(fiber_g))
        }

    @staticmethod
    def calculate_water(weight_kg: float, activity_level: str) -> int:
        """Estimates hydration goals in ml (Base: 35ml per kg, +500ml for active levels)."""
        if weight_kg <= 0:
            return 2000
            
        base_water = weight_kg * 35.0
        
        level = (activity_level or "").strip().lower()
        if level in ["very active", "athlete"]:
            base_water += 500.0
            
        return int(round(base_water))
