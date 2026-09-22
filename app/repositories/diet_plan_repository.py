import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_DIET_PLANS_FILE = os.path.join(os.path.dirname(__file__), "../../../data/diet_plans.json")
_DAILY_DISPATCH_FILE = os.path.join(os.path.dirname(__file__), "../../../data/daily_diet_dispatches.json")
_FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "../../../data/coach_feedback.json")


def _ensure_data_dir():
    os.makedirs(os.path.dirname(os.path.abspath(_DIET_PLANS_FILE)), exist_ok=True)


def _load_json_store(path: str) -> list:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {path}: {e}")
    return []


def _save_json_store(path: str, data: list):
    try:
        _ensure_data_dir()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Could not persist {path}: {e}")


def _get_supabase():
    try:
        from app.database.supabase import supabase_client
        return supabase_client
    except Exception:
        return None


# Built-in starter diet templates
DEFAULT_TEMPLATES = [
    {
        "id": "template-high-protein-shred",
        "title": "2,100 kcal High-Protein Shred Protocol",
        "description": "Optimized for fat loss while preserving lean muscle mass. Moderate carbs timed around training.",
        "coach_id": "coach_default",
        "client_id": None,
        "is_template": True,
        "dietary_tags": ["High Protein", "Fat Loss", "Lean Definition"],
        "total_calories": 2100,
        "protein_g": 175.0,
        "carbs_g": 180.0,
        "fats_g": 55.0,
        "water_liters": 3.5,
        "supplements": ["Whey Isolate (30g)", "Creatine Monohydrate (5g)", "Omega-3 Fish Oil (2000mg)", "Multivitamin"],
        "instructions": "Drink 500ml water immediately upon waking. Consume Meal 1 within 90 minutes of waking. Keep sodium consistent.",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "meals": [
            {
                "id": "m1",
                "slot_name": "Breakfast",
                "time": "08:00",
                "target_calories": 520,
                "target_protein": 42.0,
                "target_carbs": 48.0,
                "target_fats": 16.0,
                "instructions": "Whisk eggs with a splash of almond milk. Top oats with berries and pinch of cinnamon.",
                "foods": [
                    {"name": "Whole Eggs (3 large)", "portion": "3 eggs", "calories": 210, "protein": 18.0, "carbs": 1.0, "fats": 15.0},
                    {"name": "Egg Whites", "portion": "100g", "calories": 52, "protein": 11.0, "carbs": 0.5, "fats": 0.2},
                    {"name": "Rolled Oats", "portion": "50g", "calories": 185, "protein": 6.5, "carbs": 32.0, "fats": 3.0},
                    {"name": "Blueberries", "portion": "80g", "calories": 45, "protein": 0.5, "carbs": 11.0, "fats": 0.2}
                ]
            },
            {
                "id": "m2",
                "slot_name": "Lunch",
                "time": "13:00",
                "target_calories": 580,
                "target_protein": 48.0,
                "target_carbs": 55.0,
                "target_fats": 14.0,
                "instructions": "Grill chicken breast in olive oil spray. Steam jasmine rice with light salt.",
                "foods": [
                    {"name": "Chicken Breast (cooked)", "portion": "180g", "calories": 297, "protein": 45.0, "carbs": 0.0, "fats": 4.5},
                    {"name": "Steamed Jasmine Rice", "portion": "160g cooked", "calories": 208, "protein": 4.0, "carbs": 46.0, "fats": 0.5},
                    {"name": "Steamed Broccoli & Zucchini", "portion": "150g", "calories": 45, "protein": 3.5, "carbs": 8.0, "fats": 0.4},
                    {"name": "Olive Oil drizzle", "portion": "5ml", "calories": 40, "protein": 0.0, "carbs": 0.0, "fats": 4.5}
                ]
            },
            {
                "id": "m3",
                "slot_name": "Pre/Post-Workout Snack",
                "time": "17:00",
                "target_calories": 380,
                "target_protein": 34.0,
                "target_carbs": 42.0,
                "target_fats": 6.0,
                "instructions": "Consume 45-60 mins pre workout or directly post workout.",
                "foods": [
                    {"name": "Whey Protein Isolate", "portion": "1 scoop (32g)", "calories": 120, "protein": 26.0, "carbs": 2.0, "fats": 1.0},
                    {"name": "Medium Banana", "portion": "118g", "calories": 105, "protein": 1.3, "carbs": 27.0, "fats": 0.3},
                    {"name": "Rice Cakes (Lightly Salted)", "portion": "2 cakes", "calories": 70, "protein": 1.5, "carbs": 15.0, "fats": 0.5},
                    {"name": "Almond Butter", "portion": "10g", "calories": 65, "protein": 2.2, "carbs": 2.0, "fats": 5.5}
                ]
            },
            {
                "id": "m4",
                "slot_name": "Dinner",
                "time": "20:30",
                "target_calories": 540,
                "target_protein": 44.0,
                "target_carbs": 28.0,
                "target_fats": 18.0,
                "instructions": "Pan-sear salmon skin-down. Sauté asparagus with garlic and lemon squeeze.",
                "foods": [
                    {"name": "Wild Salmon Fillet", "portion": "170g", "calories": 310, "protein": 36.0, "carbs": 0.0, "fats": 16.0},
                    {"name": "Roasted Sweet Potato", "portion": "120g", "calories": 103, "protein": 1.9, "carbs": 24.0, "fats": 0.2},
                    {"name": "Grilled Asparagus", "portion": "140g", "calories": 30, "protein": 3.0, "carbs": 5.0, "fats": 0.3},
                    {"name": "Mixed Greens with Lemon juice", "portion": "80g", "calories": 18, "protein": 1.2, "carbs": 3.0, "fats": 0.2}
                ]
            }
        ]
    },
    {
        "id": "template-hypertrophy-clean-bulk",
        "title": "2,750 kcal Hypertrophy Clean Bulk Plan",
        "description": "High-carb caloric surplus geared for muscle growth without excess adipose accumulation.",
        "coach_id": "coach_default",
        "client_id": None,
        "is_template": True,
        "dietary_tags": ["Clean Bulk", "Muscle Growth", "Strength"],
        "total_calories": 2750,
        "protein_g": 190.0,
        "carbs_g": 330.0,
        "fats_g": 72.0,
        "water_liters": 4.0,
        "supplements": ["Creatine (5g)", "Whey Blend (40g)", "Zinc/Magnesium (ZMA) before bed"],
        "instructions": "Fuel workouts with complex carbs. Space protein feedings evenly every 3.5 to 4 hours.",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "meals": [
            {
                "id": "mb1",
                "slot_name": "Power Breakfast",
                "time": "08:00",
                "target_calories": 680,
                "target_protein": 45.0,
                "target_carbs": 80.0,
                "target_fats": 18.0,
                "instructions": "Combine oats, honey, protein powder, and chopped walnuts.",
                "foods": [
                    {"name": "Rolled Oats", "portion": "90g", "calories": 340, "protein": 12.0, "carbs": 60.0, "fats": 5.0},
                    {"name": "Greek Yogurt (0%)", "portion": "180g", "calories": 110, "protein": 20.0, "carbs": 7.0, "fats": 0.0},
                    {"name": "Raw Honey", "portion": "15g", "calories": 45, "protein": 0.1, "carbs": 12.0, "fats": 0.0},
                    {"name": "Crushed Walnuts", "portion": "15g", "calories": 100, "protein": 2.2, "carbs": 2.0, "fats": 10.0},
                    {"name": "Whole Eggs (Scrambled)", "portion": "2 eggs", "calories": 140, "protein": 12.0, "carbs": 1.0, "fats": 10.0}
                ]
            },
            {
                "id": "mb2",
                "slot_name": "Lean Lunch",
                "time": "12:30",
                "target_calories": 750,
                "target_protein": 52.0,
                "target_carbs": 95.0,
                "target_fats": 18.0,
                "instructions": "Brown rice with lean 93/7 minced beef, avocado, and salsa.",
                "foods": [
                    {"name": "Lean Minced Beef (93/7)", "portion": "200g", "calories": 320, "protein": 44.0, "carbs": 0.0, "fats": 14.0},
                    {"name": "Cooked Brown Basmati Rice", "portion": "240g", "calories": 266, "protein": 6.0, "carbs": 56.0, "fats": 2.0},
                    {"name": "Fresh Avocado", "portion": "50g", "calories": 80, "protein": 1.0, "carbs": 4.0, "fats": 7.0},
                    {"name": "Black Beans & Corn mix", "portion": "80g", "calories": 84, "protein": 4.5, "carbs": 16.0, "fats": 0.5}
                ]
            },
            {
                "id": "mb3",
                "slot_name": "Afternoon Mass Fuel",
                "time": "16:30",
                "target_calories": 520,
                "target_protein": 38.0,
                "target_carbs": 68.0,
                "target_fats": 10.0,
                "instructions": "Blend into high-performance mass shake.",
                "foods": [
                    {"name": "Whey Protein Powder", "portion": "35g", "calories": 135, "protein": 28.0, "carbs": 3.0, "fats": 1.5},
                    {"name": "Skim Milk or Oat Milk", "portion": "300ml", "calories": 120, "protein": 10.0, "carbs": 15.0, "fats": 1.0},
                    {"name": "Large Banana", "portion": "140g", "calories": 125, "protein": 1.5, "carbs": 32.0, "fats": 0.4},
                    {"name": "Natural Peanut Butter", "portion": "18g", "calories": 110, "protein": 4.5, "carbs": 4.0, "fats": 9.0}
                ]
            },
            {
                "id": "mb4",
                "slot_name": "Recovery Dinner",
                "time": "20:00",
                "target_calories": 700,
                "target_protein": 52.0,
                "target_carbs": 85.0,
                "target_fats": 16.0,
                "instructions": "Turkey breast tenderloin roasted with baby red potatoes and green beans.",
                "foods": [
                    {"name": "Turkey Breast Tenderloin", "portion": "200g", "calories": 260, "protein": 48.0, "carbs": 0.0, "fats": 4.0},
                    {"name": "Roasted Baby Potatoes", "portion": "280g", "calories": 240, "protein": 5.0, "carbs": 54.0, "fats": 0.5},
                    {"name": "Steamed French Green Beans", "portion": "150g", "calories": 48, "protein": 2.5, "carbs": 10.0, "fats": 0.3},
                    {"name": "Extra Virgin Olive Oil", "portion": "12ml", "calories": 105, "protein": 0.0, "carbs": 0.0, "fats": 12.0}
                ]
            }
        ]
    },
    {
        "id": "template-vegetarian-balanced",
        "title": "1,950 kcal Plant-Powered High-Protein Plan",
        "description": "Nutrient-dense vegetarian plan rich in legumes, paneer/tofu, seeds, and leafy greens.",
        "coach_id": "coach_default",
        "client_id": None,
        "is_template": True,
        "dietary_tags": ["Vegetarian", "High Fiber", "Balanced Health"],
        "total_calories": 1950,
        "protein_g": 135.0,
        "carbs_g": 210.0,
        "fats_g": 62.0,
        "water_liters": 3.2,
        "supplements": ["Vitamin B12 (1000mcg)", "Vitamin D3 (2000IU)", "Plant Protein Isolate (25g)"],
        "instructions": "Ensure diverse whole food protein pairing. Soak lentils before cooking for optimal digestion.",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "meals": [
            {
                "id": "mv1",
                "slot_name": "Morning Fuel",
                "time": "08:30",
                "target_calories": 480,
                "target_protein": 32.0,
                "target_carbs": 52.0,
                "target_fats": 14.0,
                "instructions": "High-protein paneer bhurji or scrambled tofu with whole wheat toast.",
                "foods": [
                    {"name": "Low-Fat Paneer / Organic Tofu", "portion": "140g", "calories": 240, "protein": 22.0, "carbs": 4.0, "fats": 14.0},
                    {"name": "100% Whole Wheat Sourdough", "portion": "2 slices (70g)", "calories": 170, "protein": 8.0, "carbs": 32.0, "fats": 2.0},
                    {"name": "Sautéed Bell Peppers & Spinach", "portion": "100g", "calories": 40, "protein": 2.5, "carbs": 7.0, "fats": 0.5}
                ]
            },
            {
                "id": "mv2",
                "slot_name": "Lentil & Quinoa Bowl",
                "time": "13:00",
                "target_calories": 560,
                "target_protein": 36.0,
                "target_carbs": 75.0,
                "target_fats": 12.0,
                "instructions": "Mix cooked sprouted lentils, cooked quinoa, shredded carrots, and tahini drizzle.",
                "foods": [
                    {"name": "Cooked Yellow / Green Lentils (Dal)", "portion": "180g", "calories": 210, "protein": 16.0, "carbs": 34.0, "fats": 1.0},
                    {"name": "Cooked Quinoa", "portion": "150g", "calories": 180, "protein": 6.5, "carbs": 32.0, "fats": 2.8},
                    {"name": "Hemp Seeds / Chia Seeds", "portion": "15g", "calories": 85, "protein": 5.0, "carbs": 2.0, "fats": 6.5},
                    {"name": "Lemon Tahini Dressing", "portion": "12g", "calories": 75, "protein": 2.2, "carbs": 3.0, "fats": 6.5}
                ]
            },
            {
                "id": "mv3",
                "slot_name": "Evening Energy Boost",
                "time": "17:00",
                "target_calories": 360,
                "target_protein": 30.0,
                "target_carbs": 35.0,
                "target_fats": 7.0,
                "instructions": "Mix plant protein with chilled soy or almond milk and roasted chickpeas.",
                "foods": [
                    {"name": "Pea & Rice Protein Isolate", "portion": "32g", "calories": 125, "protein": 24.0, "carbs": 3.0, "fats": 1.5},
                    {"name": "Roasted Spiced Chickpeas", "portion": "45g", "calories": 160, "protein": 7.0, "carbs": 24.0, "fats": 3.5},
                    {"name": "Green Apple", "portion": "1 apple", "calories": 75, "protein": 0.4, "carbs": 18.0, "fats": 0.3}
                ]
            },
            {
                "id": "mv4",
                "slot_name": "Nourishing Dinner",
                "time": "20:30",
                "target_calories": 520,
                "target_protein": 34.0,
                "target_carbs": 55.0,
                "target_fats": 18.0,
                "instructions": "Tofu vegetable curry cooked in light coconut milk, served with steamed edamame.",
                "foods": [
                    {"name": "Firm Tofu", "portion": "150g", "calories": 185, "protein": 19.0, "carbs": 4.0, "fats": 11.0},
                    {"name": "Steamed Edamame (shelled)", "portion": "80g", "calories": 100, "protein": 9.0, "carbs": 7.0, "fats": 4.0},
                    {"name": "Steamed Brown Rice or Millets", "portion": "120g", "calories": 150, "protein": 3.5, "carbs": 32.0, "fats": 1.2},
                    {"name": "Curry Veggies in light broth", "portion": "150g", "calories": 65, "protein": 2.5, "carbs": 11.0, "fats": 1.5}
                ]
            }
        ]
    }
]


class DietPlanRepository:
    def __init__(self):
        plans = _load_json_store(_DIET_PLANS_FILE)
        if not plans:
            plans = list(DEFAULT_TEMPLATES)
            _save_json_store(_DIET_PLANS_FILE, plans)
        self._in_memory_plans: List[Dict[str, Any]] = plans
        self._daily_dispatches: List[Dict[str, Any]] = _load_json_store(_DAILY_DISPATCH_FILE)
        self._feedback_store: List[Dict[str, Any]] = _load_json_store(_FEEDBACK_FILE)

    # --- Diet Plans CRUD ---
    def get_plans(self, coach_id: Optional[str] = None, client_id: Optional[str] = None, is_template: Optional[bool] = None) -> List[Dict[str, Any]]:
        results = self._in_memory_plans
        if is_template is not None:
            results = [p for p in results if p.get("is_template") == is_template]
        if client_id is not None:
            results = [p for p in results if p.get("client_id") == client_id]
        if coach_id is not None and coach_id != "all":
            results = [p for p in results if p.get("coach_id") in [coach_id, "coach_default"]]
        return results

    def get_plan_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        for p in self._in_memory_plans:
            if p.get("id") == plan_id:
                return p
        return None

    def create_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        plan_id = plan_data.get("id") or f"plan_{int(datetime.utcnow().timestamp() * 1000)}"
        now_str = datetime.utcnow().isoformat()
        
        new_plan = {
            **plan_data,
            "id": plan_id,
            "created_at": plan_data.get("created_at") or now_str,
            "updated_at": now_str
        }
        self._in_memory_plans.insert(0, new_plan)
        _save_json_store(_DIET_PLANS_FILE, self._in_memory_plans)

        # Attempt Supabase sync if configured
        sb = _get_supabase()
        if sb:
            try:
                sb.from_("diet_plans").insert(new_plan).execute()
            except Exception as e:
                logger.warning(f"Supabase diet plan sync failed: {e}")

        return new_plan

    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for idx, p in enumerate(self._in_memory_plans):
            if p.get("id") == plan_id:
                updated = {**p, **updates, "id": plan_id, "updated_at": datetime.utcnow().isoformat()}
                self._in_memory_plans[idx] = updated
                _save_json_store(_DIET_PLANS_FILE, self._in_memory_plans)
                return updated
        return None

    def delete_plan(self, plan_id: str) -> bool:
        initial_len = len(self._in_memory_plans)
        self._in_memory_plans = [p for p in self._in_memory_plans if p.get("id") != plan_id]
        if len(self._in_memory_plans) < initial_len:
            _save_json_store(_DIET_PLANS_FILE, self._in_memory_plans)
            return True
        return False

    # --- Daily Dispatch Engine ---
    def send_daily_diet_plan(self, dispatch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a daily diet plan sent directly from coach/trainer to a client.
        This updates or registers the client's assigned plan for that target date.
        """
        dispatch_id = f"dispatch_{int(datetime.utcnow().timestamp() * 1000)}"
        now_str = datetime.utcnow().isoformat()
        
        client_id = dispatch_data.get("client_id")
        target_date = dispatch_data.get("target_date") or datetime.utcnow().strftime("%Y-%m-%d")

        record = {
            **dispatch_data,
            "id": dispatch_id,
            "client_id": client_id,
            "target_date": target_date,
            "sent_at": now_str,
            "status": "active"
        }

        # Replace existing dispatch for same client & date if present
        self._daily_dispatches = [
            d for d in self._daily_dispatches
            if not (d.get("client_id") == client_id and d.get("target_date") == target_date)
        ]
        self._daily_dispatches.insert(0, record)
        _save_json_store(_DAILY_DISPATCH_FILE, self._daily_dispatches)

        # Also create or link a plan record
        self.create_plan({
            "id": f"plan_client_{client_id}_{target_date}",
            "title": dispatch_data.get("title") or f"Daily Diet Plan ({target_date})",
            "description": dispatch_data.get("description") or "Customized daily nutritional target sent by your coach.",
            "coach_id": dispatch_data.get("coach_id") or "coach_default",
            "client_id": client_id,
            "target_date": target_date,
            "is_template": False,
            "total_calories": dispatch_data.get("total_calories") or 2000,
            "protein_g": dispatch_data.get("protein_g") or 140.0,
            "carbs_g": dispatch_data.get("carbs_g") or 200.0,
            "fats_g": dispatch_data.get("fats_g") or 65.0,
            "water_liters": dispatch_data.get("water_liters") or 3.0,
            "supplements": dispatch_data.get("supplements") or [],
            "instructions": dispatch_data.get("instructions") or "",
            "meals": dispatch_data.get("meals") or []
        })

        return record

    def get_client_today_plan(self, client_id: str, date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        target_date = date_str or datetime.utcnow().strftime("%Y-%m-%d")
        
        # 1. Check exact date dispatch
        for d in self._daily_dispatches:
            if d.get("client_id") == client_id and d.get("target_date") == target_date:
                return d
                
        # 2. Check latest dispatch for this client
        client_dispatches = [d for d in self._daily_dispatches if d.get("client_id") == client_id]
        if client_dispatches:
            return client_dispatches[0]

        # 3. Check direct assigned plan
        for p in self._in_memory_plans:
            if p.get("client_id") == client_id:
                return p

        # 4. Fallback default active protocol
        if self._in_memory_plans:
            return self._in_memory_plans[0]
        return None

    def get_client_plan_history(self, client_id: str) -> List[Dict[str, Any]]:
        return [d for d in self._daily_dispatches if d.get("client_id") == client_id]

    # --- Coach Feedback ---
    def save_coach_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        fid = f"feedback_{int(datetime.utcnow().timestamp() * 1000)}"
        entry = {
            **feedback_data,
            "id": fid,
            "created_at": datetime.utcnow().isoformat()
        }
        self._feedback_store.insert(0, entry)
        _save_json_store(_FEEDBACK_FILE, self._feedback_store)
        return entry

    def get_feedback_for_client(self, client_id: str, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        results = [f for f in self._feedback_store if f.get("client_id") == client_id]
        if date_str:
            results = [f for f in results if f.get("date") == date_str]
        return results


diet_plan_repository = DietPlanRepository()
