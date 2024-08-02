import dspy
import os
from app.utils.database import hybrid_search, get_autocomplete ,get_unique
from dspy.teleprompt import BootstrapFewShot

# Load environment variables
AI71_API_KEY = os.getenv("AI71_API_KEY")
AI71_BASE_URL = os.getenv("AI71_BASE_URL")
AI71_MODEL_11 = os.getenv("AI71_MODEL_11")
AI71_MODEL_180 = os.getenv("AI71_MODEL_180")

# Configure DSPy language model
lm = dspy.OpenAI(api_key=AI71_API_KEY,
                  api_base=AI71_BASE_URL,
                    model=AI71_MODEL_11,
                    model_type="chat")
dspy.settings.configure(lm=lm)



# Define signatures
class UserInputToKeywordextraction(dspy.Signature):
    """Convert user input into a keyword for product recommendation."""
    user_input = dspy.InputField()
    avaliable_catagories = dspy.InputField()
    keywords = dspy.OutputField()

class UserInputToAutocomplete(dspy.Signature):
    """Convert user input with autocomplete suggestions into a string for autocomplete."""
    user_input = dspy.InputField()
    autocomplete_suggestions = dspy.InputField()
    autocomplete_string = dspy.OutputField()


# Define the recommendation system pipeline
class RecommendationSystem(dspy.Module):
    def __init__(self):
        super().__init__()
        self.user_input_to_query = dspy.ChainOfThought(UserInputToKeywordextraction)
        self.user_input_to_autocomplete = dspy.ChainOfThought(UserInputToAutocomplete)

    async def forward(self, user_input):

        unique_catagories = await get_unique("products" , "categories")


        values_set = set()
        for dictionary in unique_catagories:
            if "uniqueValue" in dictionary:
                values = dictionary["uniqueValue"].lower().split(">")
                values_set.update(map(str.strip, values))
        list(values_set)
        merged_uniquevalue = " , ".join(values_set)
        # Convert user input to keywords for product recommendation
        keywords_prediction = self.user_input_to_query(user_input=user_input , avaliable_catagories=merged_uniquevalue)
        keywords = keywords_prediction.keywords
        print(keywords)
        # Perform hybrid search on MongoDB
        products = await hybrid_search("products", keywords)
        print(products)
        # Get autocomplete suggestions from MongoDB
        autocomplete_suggestions = await get_autocomplete("products", user_input)
        print(autocomplete_suggestions)
        # Convert autocomplete suggestions to string for autocomplete suggestions
        autocomplete_prediction = self.user_input_to_autocomplete(user_input=user_input , autocomplete_suggestions=",".join(autocomplete_suggestions))
        autocomplete_string = autocomplete_prediction.autocomplete_string

        return dspy.Prediction(products=products, autocomplete_suggestions=autocomplete_suggestions, autocomplete_string=autocomplete_string)



YOUR_SAVE_PATH="recomendation_system.json"
# Instantiate the recommendation system
recommendation_system = RecommendationSystem()
if(os.path.exists(YOUR_SAVE_PATH)):
    recommendation_system.load(path=YOUR_SAVE_PATH)
else:
    print("No model found, creating a new one...")
