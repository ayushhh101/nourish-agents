# shopping_list_agent.py
from collections import defaultdict
from typing import Dict, List, Optional

def _categorize(item: str, shopping_list: Dict[str, List[str]]):
    s = item.lower()
    if any(x in s for x in ["chicken","fish","egg","beef","tofu","paneer","lentil","chickpea","rajma","dal","kidney beans","black lentils"]):
        shopping_list["Protein"].append(item)
    elif any(x in s for x in ["rice","oats","bread","pasta","quinoa","wheat","poha","semolina","rava","couscous","tortilla","pita","dalia"]):
        shopping_list["Grains"].append(item)
    elif any(x in s for x in ["apple","banana","spinach","carrot","broccoli","peas","cucumber","tomato","onion","pepper","potato","mint","coriander","cilantro","parsley","zucchini","cauliflower","eggplant","bell peppers"]):
        shopping_list["Fruits & Vegetables"].append(item)
    elif any(x in s for x in ["milk","yogurt","curd","cheese","butter","ghee"]):
        shopping_list["Dairy or Alt"].append(item)
    elif any(x in s for x in ["olive oil","vegetable oil","coconut oil","sesame oil","mustard oil"]):
        shopping_list["Oils"].append(item)
    elif any(x in s for x in ["cumin","coriander powder","turmeric","chili powder","garam masala","oregano","paprika","hing","asafoetida","cinnamon","cardamom","saffron"]):
        shopping_list["Spices"].append(item)
    else:
        shopping_list["Others"].append(item)

def generate_shopping_list_from_meals(meal_plan: dict) -> dict:
    """
    Weekly list across all 7 days for all options (if ever needed).
    Not used by default anymore—prefer day-specific below.
    """
    shopping_list = defaultdict(list)
    for option in meal_plan.get("meal_plan_options", []):
        for day in option.get("days", []):
            for meal_type in ["breakfast","lunch","dinner"]:
                for item in (day.get(meal_type, {}) or {}).get("ingredients", []) or []:
                    _categorize(str(item), shopping_list)
    final = {k: sorted(set(v)) for k, v in shopping_list.items()}
    return {"shopping_list": final}

def generate_day_shopping_list(meal_plan: dict, option_index: int, day_name: str) -> dict:
    """
    Create a grocery list for a single day in a specific option.
    - option_index: which meal option (0-based)
    - day_name: e.g., "Monday"
    """
    options = meal_plan.get("meal_plan_options", [])
    if not options or option_index < 0 or option_index >= len(options):
        return {"shopping_list": {}}

    day = next((d for d in options[option_index].get("days", []) if d.get("day") == day_name), None)
    if not day:
        return {"shopping_list": {}}

    shopping_list = defaultdict(list)
    for meal_type in ["breakfast","lunch","dinner"]:
        for item in (day.get(meal_type, {}) or {}).get("ingredients", []) or []:
            _categorize(str(item), shopping_list)

    final = {k: sorted(set(v)) for k, v in shopping_list.items()}
    return {"shopping_list": final}
