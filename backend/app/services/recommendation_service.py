import dspy
import os
from app.utils.database import hybrid_search, get_unique
import aiohttp
from typing import List, Dict
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from functools import partial
import logging

dspy.logger.level =  logging.INFO
# Create a console handler



# os.environ["DSP_NOTEBOOK_CACHEDIR"] = os.path.join(os.getcwd(), 'cache')
# os.environ["DSP_CACHEDIR"] = os.path.join(os.getcwd(), 'cache')

# from dspy. import CacheMemory
# print(CacheMemory)

# Load environment variables
AI71_API_KEY = os.getenv("AI71_API_KEY")
AI71_BASE_URL = os.getenv("AI71_BASE_URL")
AI71_MODEL_11 = os.getenv("AI71_MODEL_11")
AI71_MODEL_180 = os.getenv("AI71_MODEL_180")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_BASE_URL = os.getenv("BRAVE_BASE_URL")
LANGTRACE_API_KEY = os.getenv("LANGTRACE_API_KEY" ,None)

avaliable_intents = ['product_recommendation', 'add_to_cart', 'more_info']

# Configure DSPy language model
lm = dspy.OpenAI(api_key=AI71_API_KEY,
                 api_base=AI71_BASE_URL,
                 model=AI71_MODEL_180,
                 model_type="text")
dspy.settings.configure(lm=lm, trace=[],experimental=True)



if LANGTRACE_API_KEY:
    from langtrace_python_sdk import langtrace

    langtrace.init(api_key = LANGTRACE_API_KEY )


# Define signatures
class UserInputToKeywordExtraction(dspy.Signature):
    """Convert user input into a keyword for product recommendation."""
    user_input = dspy.InputField()
    available_categories = dspy.InputField()
    keywords = dspy.OutputField()

class IntentClassification(dspy.Signature):
    """Classify user intent based on input."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    intent = dspy.OutputField(desc=f"One of: {" , ".join(avaliable_intents)}")
    # target_products = dspy.OutputField(desc="List of product IDs relevant to the intent")

class AddToCartExtraction(dspy.Signature):
    """Extract product IDs and quantities for add to cart intent."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    products_with_quantity = dspy.OutputField(desc="List of dicts with 'product_id' and 'quantity' if quantity not provided put 1")

class ProductInfoExtraction(dspy.Signature):
    """Extract one product ID user need to know more info about."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    product = dspy.OutputField(desc="product ID")




# Define the recommendation system pipeline
class RecommendationSystem(dspy.Module):
    def __init__(self):
        super().__init__()
        self.user_input_to_query = dspy.ChainOfThought(UserInputToKeywordExtraction)
        self.intent_classifier = dspy.ChainOfThought(IntentClassification)
        self.add_to_cart_extractor = dspy.ChainOfThought(AddToCartExtraction)
        self.ProductInfoExtraction = dspy.ChainOfThought(ProductInfoExtraction)

    async def forward(self, user_input: str, current_products: List[Dict]):
        # Classify user intent
        print(f"start forward with user input {user_input}")
        if current_products:  # Check if current_products is not empty
            current_products_str = ", ".join([f"{p['name']} (ID: {p['_id']})" for p in current_products])
        else:
            current_products_str = "No products shown"
        
        # intent_prediction = self.intent_classifier(user_input=user_input, current_products=current_products_str)
        # print(f"intent_prediction: {intent_prediction}")
        intent = self.classify_intent(user_input, current_products_str)



        
        print(f"Intent: {intent}")
        

        if intent == 'product_recommendation':
            return await self.get_recommendations(user_input)
        elif intent == 'add_to_cart':
            return await self.add_to_cart(user_input, current_products)
        elif intent == 'more_info':
            return await self.get_more_info(user_input, current_products)
        else:
            return dspy.Prediction(error="Unknown intent")

    
    def classify_intent(self, user_input, current_products_str):
        intent_prediction = self.intent_classifier(user_input=user_input, current_products=current_products_str)
        intent = intent_prediction.intent.lower()
        dspy.Assert(
            intent in avaliable_intents,
            f"intent should be One of: {" , ".join(avaliable_intents)} nothing more",
        )

        return intent
    
    async def get_recommendations(self, user_input):
        print("getting recomandations")
        unique_categories = await get_unique("products", "categories")
        values_set = set()
        for dictionary in unique_categories:
            if "uniqueValue" in dictionary:
                values = dictionary["uniqueValue"].lower().split(">")
                values_set.update(map(str.strip, values))
        merged_uniquevalue = " , ".join(values_set)

        keywords_prediction = self.user_input_to_query(user_input=user_input, available_categories=merged_uniquevalue)
        keywords = keywords_prediction.keywords
        print(f"keywords: {keywords}")
        products = await hybrid_search("products", keywords, limit=5)
        print(f"products: {products}")
        return dspy.Prediction(products=products, action="recommend")

    async def add_to_cart(self, user_input, current_products):
        print("add to cart")
        cart_items_prediction = self.add_to_cart_extractor(user_input=user_input, current_products=current_products)
        cart_items = cart_items_prediction.cart_items
        
        # Ensure each item has a quantity of at least 1
        for item in cart_items:
            if 'quantity' not in item or item['quantity'] < 1:
                item['quantity'] = 1

        return dspy.Prediction(cart_items=cart_items, action="add_to_cart")

    async def get_more_info(self, user_input, current_products):
        print("more info")
        product = self.ProductInfoExtraction(user_input=user_input, current_products=current_products)
        product = product.product
        
        if not product :
            return dspy.Prediction(error="No product specified for more information")


        # Use Brave API to get more information about the product
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BRAVE_BASE_URL,
                headers={"X-Subscription-Token": BRAVE_API_KEY},
                params={"q": product},
            ) as response:
                search_results = await response.json()
        
        # Extract relevant information from search results
        additional_info = search_results['web']['results'][0]['description']
        return dspy.Prediction(product=product, additional_info=additional_info, action="more_info")

async def process_user_input(user_input: str, current_products: List[Dict]):

    results = await recommendation_system.forward(user_input=user_input, current_products=current_products)

    print(lm.inspect_history(2))
    return results


YOUR_SAVE_PATH = "recommendation_system.json"
# Instantiate the recommendation system

two_retry = partial(backtrack_handler, max_backtracks=3)
recommendation_system = RecommendationSystem()
recommendation_system = assert_transform_module(recommendation_system.map_named_predictors(dspy.Retry) ,two_retry)
if os.path.exists(YOUR_SAVE_PATH):
    recommendation_system.load(path=YOUR_SAVE_PATH)
else:
    print("No model found, creating a new one...")