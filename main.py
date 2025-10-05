# main.py - Fixed API Server with CORS support

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List

# Import orchestrator functions
from orchestrator_agent import (
    orchestrate_meal_plan,
    orchestrate_day_shopping_list,
    orchestrate_restaurants
)

app = FastAPI()

# --- Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow all origins (change to ["http://localhost:5173"] for stricter security)
    allow_credentials=True,
    allow_methods=["*"],   # Allow all HTTP methods: GET, POST, OPTIONS, etc.
    allow_headers=["*"],   # Allow all headers
)

# --- Pydantic Models ---
class UserProfile(BaseModel):
    name: str
    preferences: Dict[str, Any]

class ShoppingListRequest(BaseModel):
    context: Dict[str, Any]
    option_index: int
    day_name: str

class RestaurantRequest(BaseModel):
    context: Dict[str, Any]
    location: Dict[str, float]  # e.g., {"lat": 18.9323, "lng": 72.8316}
    cuisines: List[str] = []


# --- API Endpoints ---

@app.post("/meal-plan")
async def get_meal_plan(profile: UserProfile):
    meal_plan_context = orchestrate_meal_plan(profile.dict())
    meal_plans_data = meal_plan_context.get("meal_plans", {})
    return {
        "data": {
            "meal_plans": {
                "meal_plan_options": meal_plans_data.get("meal_plan_options", [])
            }
        }
    }

@app.post("/shopping-list")
async def get_shopping_list(request: ShoppingListRequest):
    updated_context = orchestrate_day_shopping_list(
        context=request.context,
        option_index=request.option_index,
        day_name=request.day_name
    )
    return updated_context

@app.post("/restaurants")
async def find_restaurants(request: RestaurantRequest):
    restaurant_context = orchestrate_restaurants(
        context=request.context,
        location=request.location,
        cuisines=request.cuisines
    )
    return restaurant_context
