# orchestrator_agent.py
from meal_optimizer_agent import generate_meal_plan
from shopping_list_agent import generate_day_shopping_list
from restaurant_agent import get_nearby_restaurants  # Free OSM/Overpass-backed agent
from insights_agent import generate_insight

def orchestrate_meal_plan(user_profile: dict, include_shopping_list: bool = False) -> dict:
    """
    Always generates a 7-day meal plan per option and stores it in context.
    Does NOT compute any shopping list by default.
    """
    preferences = user_profile.get("preferences", {})
    meal_plans = generate_meal_plan(preferences)
    return {"meal_plans": meal_plans}

def orchestrate_day_shopping_list(context: dict, option_index: int, day_name: str) -> dict:
    """
    Given existing context with 7-day meal plans, produce a grocery list
    for a single day and return it alongside the context.
    """
    meal_plans = context.get("meal_plans", {})
    shopping = generate_day_shopping_list(meal_plans, option_index, day_name)
    return {"meal_plans": meal_plans, "shopping_list": shopping}

def orchestrate_restaurants(context: dict, location: dict, cuisines: list = None, radius_m: int = 3000, limit: int = 7) -> dict:
    """
    Suggest nearby restaurants using Swiggy's live API
    location: {"lat": float, "lng": float} from browser geolocation
    cuisines: User preference cuisines for ranking
    Returns top 6-7 restaurants by default
    """
    lat = float(location.get("lat"))
    lng = float(location.get("lng"))
    recs = get_nearby_restaurants(lat, lng, cuisines or [], radius_m=radius_m, limit=limit)
    new_ctx = dict(context or {})
    new_ctx["restaurants"] = recs
    return new_ctx

def orchestrate_insight(context: dict, user_profile: dict, completed_meals: list) -> dict:
    """
    Generates a smart insight based on the user's profile and their history of completed meals.
    """
    insight_result = generate_insight(user_profile, completed_meals)
    new_ctx = dict(context or {})
    new_ctx["insight"] = insight_result
    return new_ctx

if __name__ == "__main__":
    user_profile = {
        "name": "Ayush",
        "preferences": {
            "cuisines": ["Chinese", "North Indian"],
            "goals": ["Build Muscle", "Lose Fat"],
            "allergies": ["Dairy"],
            "dietaryRestrictions": ["Vegetarian"]
        }
    }

    # Step 1: Generate meals only (7 days stored)
    context = orchestrate_meal_plan(user_profile, include_shopping_list=False)
    print("\n--- Meal Plan Options (7 days) ---")
    print(context["meal_plans"])

    # Step 2: Later, user asks grocery list for Monday from option 0
    context = orchestrate_day_shopping_list(context, option_index=0, day_name="Monday")
    print("\n--- Monday Shopping List (Option 0) ---")
    print(context["shopping_list"])

    # Step 3: User shares location, get nearby restaurants (free via Overpass/OSM)
    location = {"lat": 18.9323, "lng": 72.8316}
    cuisines = user_profile["preferences"]["cuisines"]
    context = orchestrate_restaurants(context, location, cuisines=cuisines, radius_m=3500, limit=25)
    print("\n--- Nearby Restaurants (OSM/Overpass) ---")
    print(context["restaurants"])
