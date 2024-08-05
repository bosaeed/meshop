import dspy
import os
from app.utils.database import hybrid_search, get_unique
import requests

from typing import List, Dict
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from functools import partial
import logging
import json
from fastapi import WebSocket
import asyncio

dspy.logger.level =  logging.INFO
# Create a console handler

# Load environment variables
AI71_API_KEY = os.getenv("AI71_API_KEY")
AI71_BASE_URL = os.getenv("AI71_BASE_URL")
AI71_MODEL_11 = os.getenv("AI71_MODEL_11")
AI71_MODEL_180 = os.getenv("AI71_MODEL_180")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_BASE_URL = os.getenv("BRAVE_BASE_URL")
LANGTRACE_API_KEY = os.getenv("LANGTRACE_API_KEY" ,None)

avaliable_intents = ['product_recommendation', 'add_to_cart', 'get_more_info' , 'unknown_intent']
avaliable_intents_start = ['product_recommendation', 'unknown_intent']

# Configure DSPy language model
lm = dspy.OpenAI(api_key=AI71_API_KEY,
                 api_base=AI71_BASE_URL,
                 model=AI71_MODEL_180,
                 model_type="text")
dspy.settings.configure(lm=lm, trace=[],experimental=True)

gwebsocket = None

if LANGTRACE_API_KEY:
    from langtrace_python_sdk import langtrace

    langtrace.init(api_key = LANGTRACE_API_KEY )


# Define signatures
class UserInputToKeywordExtraction(dspy.Signature):
    """Convert user input into a keyword for product recommendation."""
    user_input = dspy.InputField()
    available_categories = dspy.InputField()
    keywords = dspy.OutputField()

class IntentClassificationStart(dspy.Signature):
    """Classify user intent based on input. new user do not have any products shown in his screen yet"""
    user_input = dspy.InputField()
    intent = dspy.OutputField(desc=f"One of: {' , '.join(avaliable_intents_start)}")

class IntentClassification(dspy.Signature):
    """Classify user intent based on input."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    intent = dspy.OutputField(desc=f"One of: {' , '.join(avaliable_intents)}")

class AddToCartExtraction(dspy.Signature):
    """Extract product IDs and quantities for add to cart intent."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    products_with_quantity = dspy.OutputField(desc="List of dicts with 'product_id' and 'quantity' if quantity not provided put 1")

class ProductInfoExtraction(dspy.Signature):
    """Extract one product ID user need to know more info about."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    product_id = dspy.OutputField(desc="ID of product ")
    query = dspy.OutputField(desc="query to search for searching internet to get more info about the product.")

class SummerizeProductInfo(dspy.Signature):
    """use search results to summerize product info that user need to know more info about."""
    user_input = dspy.InputField()
    additional_info = dspy.InputField()
    product = dspy.InputField()
    summery = dspy.OutputField(desc="summery of the product info that user need to know more info about. limit to 100 words or less.")


# Define the recommendation system pipeline
class RecommendationSystem(dspy.Module):
    def __init__(self):
        super().__init__()
        self.user_input_to_query = dspy.ChainOfThought(UserInputToKeywordExtraction)
        self.intent_classifier = dspy.ChainOfThought(IntentClassification)
        self.intent_classifier_start = dspy.ChainOfThought(IntentClassificationStart)
        self.add_to_cart_extractor = dspy.ChainOfThought(AddToCartExtraction)
        self.ProductInfoExtraction = dspy.ChainOfThought(ProductInfoExtraction)
        self.SummerizeProductInfo = dspy.ChainOfThought(SummerizeProductInfo)

    async def forward(self, user_input: str, current_products: List[Dict] ):
        # Classify user intent
        global gwebsocket 
        self.websocket = gwebsocket
        print(f"start forward with user input {user_input}")
        await self.send_feedback("Thinking...")
        self.id_to_product = {}
        current_products_str = "No products shown"
        if current_products:  # Check if current_products is not empty

            for idx , p in enumerate(current_products):
                self.id_to_product[str(idx+1)] = p
                current_products_str += f"""
                {{Product_ID: {idx+1}, name: {p['name']}, description: {p['description']}}},
                """

        
        print(f"current_products_str: {current_products_str}")
        # intent_prediction = self.intent_classifier(user_input=user_input, current_products=current_products_str)
        # print(f"intent_prediction: {intent_prediction}")
        intent = self.classify_intent(user_input, current_products_str)

        
        print(f"Intent: {intent}")
        

        if intent == 'product_recommendation':
            return await self.get_recommendations(user_input)
        elif intent == 'add_to_cart':
            return await self.add_to_cart(user_input, current_products_str)
        elif intent == 'get_more_info':
            return await self.get_more_info(user_input, current_products_str)
        else:
            return dspy.Prediction(error="Unknown intent")

    
    def classify_intent(self, user_input, current_products_str):
        if current_products_str == "No products shown":

            intent_prediction = self.intent_classifier_start(user_input=user_input)
        else:
            intent_prediction = self.intent_classifier(user_input=user_input, current_products=current_products_str)

        print(f"intent_prediction: {intent_prediction}")
        intent = intent_prediction.intent.lower()
        dspy.Assert(
            intent in avaliable_intents,
            f"intent should be One of: {' , '.join(avaliable_intents)} nothing more",
        )

        return intent
    
    async def get_recommendations(self, user_input):
        print("getting recomandations")
        await self.send_feedback("Do not worry I'll find the perfect product for you")
        unique_categories =  get_unique("products", "categories")
        values_set = set()
        for dictionary in unique_categories:
            if "uniqueValue" in dictionary:
                values = dictionary["uniqueValue"].lower().split(">")
                values_set.update(map(str.strip, values))
        merged_uniquevalue = " , ".join(values_set)

        keywords_prediction = self.user_input_to_query(user_input=user_input, available_categories=merged_uniquevalue)
        keywords = keywords_prediction.keywords
        print(f"keywords: {keywords}")
        products =  hybrid_search("products", keywords, limit=5)
        print(f"products: {products}")
        return dspy.Prediction(products=products, action="recommend")

    async def add_to_cart(self, user_input, current_products):
        print("add to cart")
        await self.send_feedback("ok ok wil be added")
        cart_items_prediction = self.add_to_cart_extractor(user_input=user_input, current_products=current_products)
        cart_items = cart_items_prediction.products_with_quantity
        
        # Ensure each item has a quantity of at least 1
        # for item in cart_items:
        #     if 'quantity' not in item or item['quantity'] < 1:
        #         item['quantity'] = 1

        return dspy.Prediction(cart_items=cart_items, action="add_to_cart")

    async def get_more_info(self, user_input, current_products):
        print("get more info")
        await self.send_feedback("which one you mean???")
        product = self.ProductInfoExtraction(user_input=user_input, current_products=current_products)
        await self.send_feedback("searching...")
        print(product)
        product_id = product.product_id
        query = product.query
        if not product_id :
            return dspy.Prediction(error="No product specified for more information")

        # dspy.Assert(
        #     self.id_to_product.get(product_id) != None,
        #     f"product_id {product_id} not found in current_products"
        # )
        current_product = self.id_to_product.get(product_id)
        print(f"current_product: {current_product}")
        response = requests.get(
            BRAVE_BASE_URL,
            headers={"X-Subscription-Token": BRAVE_API_KEY},
            params={"q": query},
        )
        search_results = response.json()

        print(f"search_results: {search_results}")


        # Extract relevant information from search results
        # Concatenate the first 5 results' descriptions
        additional_info = " ".join(result['description'] for result in search_results['web']['results'][:5])

        summery = self.SummerizeProductInfo(user_input=user_input,additional_info=additional_info, product=current_product)

        return dspy.Prediction(product=current_product, additional_info=summery.summery, action="more_info")
    
    async def send_feedback(self, message):
        if self.websocket is not None:
            await self.websocket.send_text(json.dumps({
                "action":"feedback",
                "message": message
            }))
            

async def process_user_input(user_input: str, current_products: List[Dict] ,websocket:WebSocket|None = None):
    global gwebsocket 
    gwebsocket= websocket
    results =  await recommendation_system(user_input=user_input, current_products=current_products )

    # print(lm.inspect_history(3))
    return results


YOUR_SAVE_PATH = ".\\app\\services\\recomendation_system.json"
# Instantiate the recommendation system

two_retry = partial(backtrack_handler, max_backtracks=3)
recommendation_system = RecommendationSystem()
recommendation_system = assert_transform_module(recommendation_system.map_named_predictors(dspy.Retry) ,two_retry)
print(os.listdir('.'))
if os.path.exists(YOUR_SAVE_PATH):
    recommendation_system.load(path=YOUR_SAVE_PATH)
else:
    print("No model found, creating a new one...")