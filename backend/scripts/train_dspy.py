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
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import asyncio

load_dotenv()

YOUR_SAVE_PATH = "recomendation_system.json"
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL")
AI71_API_KEY = os.getenv("AI71_API_KEY")
AI71_BASE_URL = os.getenv("AI71_BASE_URL")
AI71_MODEL_11 = os.getenv("AI71_MODEL_11")
AI71_MODEL_180 = os.getenv("AI71_MODEL_180")
# Instantiate the recommendation system
recommendation_system = RecommendationSystem()
recommendation_system = assert_transform_module(recommendation_system.map_named_predictors(dspy.Retry) ,backtrack_handler)
gpt4llm = dspy.OpenAI(api_key=OPENAI_API_KEY, api_base=OPENAI_BASE_URL, model="gpt-4o-mini")
lm = dspy.OpenAI(api_key=AI71_API_KEY,
                 api_base=AI71_BASE_URL,
                 model=AI71_MODEL_180,
                 model_type="text")
dspy.settings.configure(lm=lm, trace=[],experimental=True)


#%%

# Define the signature for automatic assessments.
class Assess(dspy.Signature):
    """Assess the quality of a output."""

    # assessed_text = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer = dspy.OutputField(desc="Yes or No")

# Define a metric for optimization
def recomendation_system_metric(example, pred, trace=None):
    pred =  pred
    print("strart recomendation_system_metric")
    print(example)
    print(pred)

    i=0
    if pred.get( "products") is not None:
        for product in pred.products:
            product.pop("_id")
            product.pop("images")
            product['id'] =i
            i+=1
    print(pred)
    user_input, current_products , output = example.user_input, example.current_products, pred.action
    print(user_input)
    print(current_products)
    print(output)
    correct = f"Does output action `{output}` correctly respond to the user's input `{user_input}` and the current products `{current_products}`?"
    info_extracted = f"Does output action `{output}` extract all the necessary information from the user's input `{user_input}`?"
    
    with dspy.context(lm=gpt4llm):
        correct =  dspy.Predict(Assess)( assessment_question=correct)
        info_extracted = dspy.Predict(Assess)( assessment_question=info_extracted)

    print(correct)
    print(info_extracted)
    correct, info_extracted = [m.assessment_answer.lower() == 'yes' for m in [correct, info_extracted]]
    score = (correct + info_extracted) 
    # if trace is not None: return score >= 2
    return score / 2.0

# Prepare training data
trainset = [
    dspy.Example( user_input="need nice cloth" , user_id="123").with_inputs("user_input","user_id"),
    # dspy.Example( user_input="hoodies are perfect" , user_id="123").with_inputs("user_input","user_id"),
    # dspy.Example( user_input="give more info about the black hoodie" , user_id="123").with_inputs("user_input","user_id"),
    # dspy.Example( user_input="add three blue hood" ,  user_id="123").with_inputs("user_input","user_id"),

]

# Optimize the pipeline using BootstrapFewShot
optimizer = BootstrapFewShot(metric=recomendation_system_metric, max_bootstrapped_demos=4, max_labeled_demos=4)
optimized_recommendation_system = optimizer.compile(recommendation_system, trainset=trainset)

# Replace the original module with the optimized one

optimized_recommendation_system.save(YOUR_SAVE_PATH)



# %%
