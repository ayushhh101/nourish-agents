# llm_main.py
import os
from typing import List, Literal, TypedDict, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

# ---- Set Gemini API key manually (consider env var in production) ----
API_KEY = "AIzaSyAgxSTK353KHYVshnaJtITos0nqqQqRBhM"
os.environ["GEMINI_API_KEY"] = API_KEY

# -------- Structured output schemas (TypedDicts) --------
class Macro(TypedDict):
    protein: float
    carbs: float
    fat: float

class Recipe(TypedDict):
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    ingredients: List[str]
    youtube_link: str

class DayPlan(TypedDict):
    day: Literal[
        "Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"
    ]
    breakfast: Recipe
    lunch: Recipe
    dinner: Recipe

class MealOption(TypedDict):
    option_name: str
    days: List[DayPlan]

class MealPlanResponse(TypedDict):
    meal_plan_options: List[MealOption]

# -------- Create LangChain LLM with structured outputs --------
# Method json_mode uses Gemini responseSchema under the hood to force JSON
llm_base = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=API_KEY,
    temperature=0,
)

# Bind schema: returns parsed Python objects that conform to MealPlanResponse
llm_structured = llm_base.with_structured_output(
    schema=MealPlanResponse,  # Pydantic or TypedDict-like schema
    method="json_mode",       # Gemini native structured output
)
