# meal_optimizer_agent.py
import json
from typing import Dict, List
from langchain.prompts import PromptTemplate
from llm_main import llm_structured

VALID_DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def _trim_to_seven_days(meal_plan: Dict) -> Dict:
    """
    Return each option with exactly the 7 canonical days (Mon..Sun), in order.
    - Deduplicate by day name (first occurrence wins).
    - Keep only VALID_DAYS.
    - If a weekday is missing, it is omitted (no padding), and result is sliced to max 7.
    """
    options = meal_plan.get("meal_plan_options", [])
    trimmed_options: List[Dict] = []

    for opt in options:
        # Collect first occurrence by weekday
        first_seen = {}
        for d in opt.get("days", []):
            if not isinstance(d, dict):
                continue
            day_name = d.get("day")
            if isinstance(day_name, str):
                day_name = day_name.capitalize()  # <-- convert 'monday' -> 'Monday'
                if day_name in VALID_DAYS and day_name not in first_seen:
                    first_seen[day_name] = d

        # Order by canonical weekdays and strictly cap to 7
        ordered_days = [first_seen[d] for d in VALID_DAYS if d in first_seen][:7]

        trimmed_options.append({
            "option_name": opt.get("option_name", "Option"),
            "days": ordered_days
        })

    return {"meal_plan_options": trimmed_options}

def generate_meal_plan(preferences: dict) -> dict:
    """
    Generates 3 structured weekly meal plan options (exactly 7 days each after trimming).
    """
    prompt_template = """
You are a professional meal planning and nutrition assistant.
Generate exactly 3 meal plan options based on the following preferences.

Preferences:
- Cuisines: {cuisines}
- Goals: {goals}
- Allergies: {allergies}
- Dietary Restrictions: {dietaryRestrictions}

Rules:
1. Weekly plan with exactly these 7 days in order: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday.
2. For each day, include Breakfast, Lunch, Dinner.
3. Each recipe must include:
   - Name
   - Calories
   - Macronutrients (protein, carbs, fat) as numbers
   - Full ingredient list (quantities and units)
   - A valid YouTube link
4. Avoid restricted or allergen ingredients.
5. Do NOT generate any shopping list.
6. Return strictly valid JSON matching the bound schema.
"""
    prompt = PromptTemplate(
        input_variables=["cuisines", "goals", "allergies", "dietaryRestrictions"],
        template=prompt_template,
    )

    formatted_prompt = prompt.format(
        cuisines=preferences.get("cuisines", []),
        goals=preferences.get("goals", []),
        allergies=preferences.get("allergies", []),
        dietaryRestrictions=preferences.get("dietaryRestrictions", []),
    )

    try:
        response = llm_structured.invoke(formatted_prompt)
        print("LLM structured response:", response)
        data = response if isinstance(response, dict) else dict(response)
        return _trim_to_seven_days(data)
    except Exception:
        from llm_main import llm_base
        text = llm_base.invoke(formatted_prompt).content
        try:
            data = json.loads(text)
        except Exception:
            return {"meal_plan_options": []}
        return _trim_to_seven_days(data)
