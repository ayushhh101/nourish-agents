from typing import Dict, List
from llm_main import llm_structured_insight, InsightResponse


def _build_prompt(user_profile: Dict, completed_meals: List[Dict]) -> str:
    """
    Constructs the detailed prompt for the AI model, instructing it to
    provide a structured JSON response with a title, feedback, and recommendation.
    """
    preferences = user_profile.get("preferences", {})
    goals = preferences.get("goals") or ["Not specified"]
    cuisines = preferences.get("cuisines") or ["Not specified"]
    allergies = preferences.get("allergies") or ["None"]

    meals_text = "\n".join(
        [
            f"- {meal.get('name', 'N/A')} "
        f"(Calories: {meal.get('calories', 0)}, Protein: {meal.get('protein', 0)}g, "
        f"Carbs: {meal.get('carbs', 0)}g, Fat: {meal.get('fat', 0)}g)" 
        for meal in completed_meals
        ]
    )

    return f"""
You are a friendly and encouraging nutritionist AI for an app called "Nourish".
Your task is to provide a smart insight and a recommendation for a user based on their goals and what they've recently eaten.

Here is the user's data:
## User's Name:
{user_profile.get("name", "User")}

## User's Goals and Preferences:
- Goals: {', '.join(goals)}
- Cuisines they like: {', '.join(cuisines)}
- Allergies: {', '.join(allergies)}

## User's Recently Eaten Meals:
{meals_text}

## Your Task:
Analyze the eaten meals in the context of their goals.
Your response MUST be a JSON object that strictly follows this schema: {{ "title": "string", "positive_feedback": "string", "actionable_recommendation": "string" }}.

- title: A short, catchy title for the insight.
- positive_feedback: Start by congratulating the user on what they did well.
- actionable_recommendation: Provide one specific, actionable tip for the upcoming week.

Keep the tone positive and motivating. Do not sound like a robot.
"""

def generate_insight(user_profile: Dict, completed_meals: List[Dict]) -> Dict:
    """
    Generates a personalized, structured insight using the LangChain agent.

    Args:
        user_profile: A dictionary containing user info like name and preferences.
        completed_meals: A list of dictionaries representing eaten meals.

    Returns:
        A dictionary with the success status and the structured insight object.
    """
    if not completed_meals or len(completed_meals) < 3:
        return {
            "success": False,
            "insight": "Not enough data for an insight. Mark at least 3 meals as eaten!"
        }

    try:
        prompt = _build_prompt(user_profile, completed_meals)

       
        ai_response_dict = llm_structured_insight.invoke(prompt)

        return {"success": True, "insight": ai_response_dict}
    
    except Exception as e:
        print(f"❌ Error in insights_agent: {e}")
        return {
            "success": False,
            "insight": "Sorry, I couldn't generate an insight at this time. Please try again later."
        }