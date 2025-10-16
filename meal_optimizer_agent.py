# meal_optimizer_agent.py
import json
import requests
import urllib.parse
from typing import Dict, List
from langchain.prompts import PromptTemplate
from llm_main import llm_structured


VALID_DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# API Configuration (choose one)
UNSPLASH_ACCESS_KEY = "qbf2kqYke18O6b-YxcRJNz8aa0KQrtYGicHihvyW49A"  # Get from https://unsplash.com/developers
PEXELS_API_KEY = "igvWvmGGYhqTqB2dLgFCisHeazMmgWPUPoAzfdIYfMoP0cZIErbPUzl3"  # Get from https://www.pexels.com/api/


def generate_youtube_search_url(recipe_name: str) -> str:
    """
    Generate a YouTube search URL for a given recipe name.
    """
    # Clean up the recipe name and encode it for URL
    search_query = f"{recipe_name} recipe"
    encoded_query = urllib.parse.quote_plus(search_query)
    return f"https://www.youtube.com/results?search_query={encoded_query}"


def fetch_food_image(food_name: str, api_choice: str = "unsplash") -> str:
    """
    Fetch a food image URL from Unsplash or Pexels API.
    Returns image URL or None if not found.
    """
    try:
        if api_choice == "unsplash":
            # Unsplash API search
            url = f"https://api.unsplash.com/search/photos"
            params = {
                "query": f"{food_name} food",
                "client_id": UNSPLASH_ACCESS_KEY,
                "per_page": 1,
                "orientation": "landscape"
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                return data["results"][0]["urls"]["regular"]  # 1080px width
                
        elif api_choice == "pexels":
            # Pexels API search
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": PEXELS_API_KEY}
            params = {
                "query": f"{food_name} food",
                "per_page": 1,
                "orientation": "landscape"
            }
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get("photos") and len(data["photos"]) > 0:
                return data["photos"][0]["src"]["large"]  # Large size
                
    except Exception as e:
        print(f"Error fetching image for {food_name}: {e}")
        return None
    
    return None


def add_images_to_meals(meal_plan: Dict, api_choice: str = "unsplash") -> Dict:
    """
    Add image URLs and YouTube search URLs to each meal in the meal plan.
    """
    for option in meal_plan.get("meal_plan_options", []):
        for day in option.get("days", []):
            if not isinstance(day, dict):
                continue
                
            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_type)
                if isinstance(meal, dict) and "name" in meal:
                    # Fetch image for this meal
                    image_url = fetch_food_image(meal["name"], api_choice)
                    meal["image_url"] = image_url if image_url else ""
                    
                    # Generate YouTube search URL
                    meal["youtube_link"] = generate_youtube_search_url(meal["name"])
                    
    return meal_plan


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
                day_name = day_name.capitalize()
                if day_name in VALID_DAYS and day_name not in first_seen:
                    first_seen[day_name] = d

        # Order by canonical weekdays and strictly cap to 7
        ordered_days = [first_seen[d] for d in VALID_DAYS if d in first_seen][:7]

        trimmed_options.append({
            "option_name": opt.get("option_name", "Option"),
            "days": ordered_days
        })

    return {"meal_plan_options": trimmed_options}


def generate_meal_plan(preferences: dict, include_images: bool = True, image_api: str = "unsplash") -> dict:
    """
    Generates 1 structured weekly meal plan option (exactly 7 days after trimming).
    
    Args:
        preferences: User preferences for meal planning
        include_images: Whether to fetch images for meals (default: True)
        image_api: Which API to use - "unsplash" or "pexels" (default: "unsplash")
    """
    prompt_template = """
You are a professional meal planning and nutrition assistant.
Generate exactly 1 meal plan option based on the following preferences.

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
   - A YouTube search URL in the format: https://www.youtube.com/results?search_query=RECIPE_NAME+recipe (replace spaces with +)
4. Avoid restricted or allergen ingredients.
5. Make sure the meals are mix of easy-to-cook and moderately complex recipes and according to the preferences. They should be familiar to Indian diet and should amaze the user.
6. Do NOT generate any shopping list.
7. Return strictly valid JSON matching the bound schema.
8. For youtube_link, use actual YouTube search URLs like: https://www.youtube.com/results?search_query=Keto+Coconut+Flour+Idli+recipe
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
        trimmed_data = _trim_to_seven_days(data)
        
        # Add images if requested
        if include_images:
            trimmed_data = add_images_to_meals(trimmed_data, image_api)
            
        return trimmed_data
    except Exception:
        from llm_main import llm_base
        text = llm_base.invoke(formatted_prompt).content
        try:
            data = json.loads(text)
        except Exception:
            return {"meal_plan_options": []}
        trimmed_data = _trim_to_seven_days(data)
        
        # Add images if requested
        if include_images:
            trimmed_data = add_images_to_meals(trimmed_data, image_api)
            
        return trimmed_data
