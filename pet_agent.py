# pet_agent.py
from langchain.prompts import PromptTemplate
from llm_main import llm

def create_pet_agent(pet_type: str):
    """Creates a basic AI agent that returns average lifespan and random 5 pet names for a pet type."""

    prompt_template = """
    You are a pet expert assistant.
    For the pet type "{pet_type}", do the following:
    1. Give the **average lifespan** in years.
    2. Suggest **5 unique and fun pet names** (avoid duplicates).

    Return the answer in JSON format only:
    {{
        "avg_lifespan": <integer>,
        "pet_names": [<name1>, <name2>, <name3>, <name4>, <name5>]
    }}
    """

    prompt = PromptTemplate(
        input_variables=["pet_type"],
        template=prompt_template,
    )

    formatted_prompt = prompt.format(pet_type=pet_type)
    response = llm.invoke(formatted_prompt)

    return response.content if hasattr(response, "content") else response

if __name__ == "__main__":
    pet_type = input("Enter a pet type (e.g., dog, cat, parrot): ")
    result = create_pet_agent(pet_type)
    print("\n--- Pet Info ---")
    print(result)
