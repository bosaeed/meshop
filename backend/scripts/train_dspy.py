# %%
# meshop/backend/app/scripts/train_dspy.py

import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dspy
import os
from dspy.teleprompt import BootstrapFewShot
from app.services.recommendation_service import RecommendationSystem , process_user_input
from dotenv import load_dotenv
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import nest_asyncio

nest_asyncio.apply()
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

class DummySender():

    async def send_text(self,messageData ,isText = False):
        print(messageData)

dummy_sender = DummySender()
#%%
process_user_input(user_input="need hoodies",websocket=dummy_sender , user_id="123")

#%%
process_user_input(user_input="please add two Mens Divi Hoodie to cart and Hoodie - Green",websocket=dummy_sender , user_id="123")

#%%
process_user_input(user_input="give me more information about Mens Divi Hoodie",websocket=dummy_sender , user_id="123")

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
    user_input, user_id ,action = example.user_input, example.user_id ,pred.action

    print(user_input)


    correct = f"Does output action `{action}` correctly respond to the user's input `{user_input}`?"
    info_extracted = f"Does output action `{action}` extract all the necessary information from the user's input `{user_input}`?"
    
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
    dspy.Example( user_input="need nice hoodie" , user_id="10").with_inputs("user_input","user_id"),
    dspy.Example( user_input="give more information about the first hoodie" , user_id="10").with_inputs("user_input","user_id"),
    dspy.Example( user_input="add three from first hoodie to cart and also two from product 5" , user_id="10").with_inputs("user_input","user_id"),
    dspy.Example( user_input="i need do some excersise do you have workout equipment" , user_id="20").with_inputs("user_input","user_id"),
    dspy.Example( user_input="how to use the third one" , user_id="20").with_inputs("user_input","user_id"),
    dspy.Example( user_input="add thired one to cart" , user_id="20").with_inputs("user_input","user_id"),

]

# Optimize the pipeline using BootstrapFewShot
optimizer = BootstrapFewShot(metric=recomendation_system_metric, max_bootstrapped_demos=4, max_labeled_demos=4 ,metric_threshold=0.85)
optimized_recommendation_system = optimizer.compile(recommendation_system, trainset=trainset)

# Replace the original module with the optimized one

optimized_recommendation_system.save(YOUR_SAVE_PATH)



# %%
