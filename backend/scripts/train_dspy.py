# %%
# meshop/backend/app/scripts/train_dspy.py

import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dspy
import os
from dspy.teleprompt import BootstrapFewShot
from app.services.recommendation_service import RecommendationSystem
from dotenv import load_dotenv

load_dotenv()

YOUR_SAVE_PATH = "recomendation_system.json"
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL")
AI71_MODEL_11 = os.getenv("AI71_MODEL_11")
AI71_MODEL_180 = os.getenv("AI71_MODEL_180")
# Instantiate the recommendation system
recommendation_system = RecommendationSystem()
# gpt4llm = dspy.OpenAI(api_key=OPENAI_API_KEY, api_base=OPENAI_BASE_URL, model="gpt-4o-mini")

#%%
print(await recommendation_system(user_input="hoodi"))


#%%
# Define a metric for optimization
def recomendation_system_metric(example, pred):
    return example.autocomplete_query.lower() == pred.autocomplete_query.lower()

# Prepare training data
trainset = [
    dspy.Example( user_input="laptop"),
    dspy.Example( user_input="smartphone"),

]

# Optimize the pipeline using BootstrapFewShot
optimizer = BootstrapFewShot(metric=recomendation_system_metric, max_bootstrapped_demos=5, max_labeled_demos=5)
optimized_recommendation_system = optimizer.compile(recommendation_system, trainset=trainset)

# Replace the original module with the optimized one

optimized_recommendation_system.save(YOUR_SAVE_PATH)

# Example usage
async def example_usage():
    user_input = "laptop"
    result = await recommendation_system(user_input=user_input)
    print("Products:", result["products"])
    print("Autocomplete Suggestions:", result["autocomplete_suggestions"])
    print("Autocomplete Query:", result["autocomplete_query"])


