import dspy
import os
from app.utils.database import hybrid_search, get_unique
import requests

from typing import List, Dict
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from functools import partial
import logging
import json
import asyncio
import nest_asyncio
nest_asyncio.apply()

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

system_prompt = "You are sales person at meshop, answering customers and knowing what they want and help them."

# Configure DSPy language model
lm = dspy.OpenAI(api_key=AI71_API_KEY,
                 api_base=AI71_BASE_URL,
                 model=AI71_MODEL_180,
                 model_type="chat"
                 ,system_prompt=system_prompt)
dspy.settings.configure(lm=lm, trace=[],experimental=True)

gwebsocket = None

# if LANGTRACE_API_KEY:
#     from langtrace_python_sdk import langtrace

#     langtrace.init(api_key = LANGTRACE_API_KEY )


class UserSession:
    def __init__(self):
        self.current_products = []
        self.cart_items = []
        self.chat_history = []

    def add_to_history(self, **kwargs):
        
        self.chat_history.append({k: v for k, v in kwargs.items()})

    def get_chat_history(self):
        output = ""
        for item in self.chat_history[-5:]: 
            output += "\n".join([f"{k}: {v}" for k, v in item.items()])
        return output
    
    def print(self):
        print("current_products:", self.current_products)
        print("cart_items:", self.cart_items)
        print("chat_history:", self.chat_history)
    

# Define signatures
class UserInputToKeywordExtraction(dspy.Signature):
    """Convert user input into a keyword for product recommendation."""
    user_input = dspy.InputField()
    available_categories = dspy.InputField()
    chat_history = dspy.InputField()
    keywords = dspy.OutputField()
    feedback = dspy.OutputField(desc="tell to user brive feedback. limit to 10 words or less.")

class IntentClassificationStart(dspy.Signature):
    """Classify user intent based on input. new user do not have any products shown in his screen yet"""
    user_input = dspy.InputField()
    chat_history = dspy.InputField()
    intent = dspy.OutputField(desc=f"One of: {' , '.join(avaliable_intents_start)}")
    feedback = dspy.OutputField(desc="tell to user brive feedback. limit to 10 words or less.")

class IntentClassification(dspy.Signature):
    """Classify user intent based on input."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    chat_history = dspy.InputField()
    intent = dspy.OutputField(desc=f"One of: {' , '.join(avaliable_intents)}")
    feedback = dspy.OutputField(desc="tell to user brive feedback. limit to 10 words or less.")

class AddToCartExtraction(dspy.Signature):
    """Extract product IDs and quantities for add to cart intent."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    chat_history = dspy.InputField()
    products_with_quantity = dspy.OutputField(desc="List of dicts with 'product_id' and 'quantity' if quantity not provided put 1")
    feedback = dspy.OutputField(desc="tell to user brive feedback. limit to 10 words or less.")

class ProductInfoExtraction(dspy.Signature):
    """Extract one product ID user need to know more info about."""
    user_input = dspy.InputField()
    current_products = dspy.InputField()
    chat_history = dspy.InputField()
    product_id = dspy.OutputField(desc="ID of product ")
    query = dspy.OutputField(desc="query to search for searching internet to get more information. write keywords dirctle limit 5 words or less")
    feedback = dspy.OutputField(desc="tell to user brive feedback. limit to 10 words or less.")

class SummerizeProductInfo(dspy.Signature):
    """use search results to summerize product info that user need to know more info about."""
    user_input = dspy.InputField()
    additional_info = dspy.InputField()
    product = dspy.InputField()
    chat_history = dspy.InputField()
    summery = dspy.OutputField(desc="summery of the product info that user need to know more info about. limit to 100 words or less.")


# Define the recommendation system pipeline
class RecommendationSystem(dspy.Module):
    def __init__(self):
        super().__init__()
        self.user_sessions = {}
        self.user_input_to_query = dspy.ChainOfThought(UserInputToKeywordExtraction)
        self.intent_classifier = dspy.ChainOfThought(IntentClassification)
        self.intent_classifier_start = dspy.ChainOfThought(IntentClassificationStart)
        self.add_to_cart_extractor = dspy.ChainOfThought(AddToCartExtraction)
        self.ProductInfoExtraction = dspy.ChainOfThought(ProductInfoExtraction)
        self.SummerizeProductInfo = dspy.ChainOfThought(SummerizeProductInfo)

    def get_or_create_session(self, user_id):
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession()
        return self.user_sessions[user_id]

    def forward(self, user_input: str, user_id: str ):
        session = self.get_or_create_session(user_id)
        print(self.user_sessions)
        session.print()
        current_products = session.current_products
        chat_history = session.get_chat_history()

        global gwebsocket 
        self.websocket = gwebsocket
        print(f"start forward with user input {user_input}")
        if self.websocket:call_async(self.send_feedback("wait⏳..."))
        self.id_to_product = {}
        current_products_str = "No products shown"
        if current_products:  # Check if current_products is not empty
            current_products_str = ""
            for idx , p in enumerate(current_products):
                self.id_to_product[str(idx+1)] = p
                current_products_str += f"""
                {{Product_ID: {idx+1}, name: {p.get('name','')}, description: {p.get('description','')}}},
                """

        
        # print(f"current_products_str: {current_products_str}")
        # intent_prediction = self.intent_classifier(user_input=user_input, current_products=current_products_str)
        # print(f"intent_prediction: {intent_prediction}")
        intent ,feedback = self.classify_intent(user_input, current_products_str,chat_history,user_id)

        
        print(f"Intent: {intent}")
        
        
        if intent == 'product_recommendation':
            return self.get_recommendations(user_input, chat_history,user_id)
        elif intent == 'add_to_cart':
            return self.add_to_cart(user_input, current_products_str, chat_history,user_id)
        elif intent == 'get_more_info':
            return self.get_more_info(user_input, current_products_str, chat_history,user_id)
        else:
            return dspy.Prediction(error="Unknown intent" , feedback=feedback , action="unknown_intent")

    
    def classify_intent(self, user_input, current_products_str, chat_history, user_id):
        session = self.get_or_create_session(user_id)
        session.print()
        if current_products_str == "No products shown":

            intent_prediction = self.intent_classifier_start(user_input=user_input, chat_history=chat_history)
        else:
            intent_prediction = self.intent_classifier(user_input=user_input, current_products=current_products_str, chat_history=chat_history)

        session.add_to_history(user=user_input, assistant=intent_prediction.rationale)
        print(f"intent_prediction: {intent_prediction}")
        if self.websocket:call_async(self.send_feedback(intent_prediction.feedback))
        intent = intent_prediction.intent.lower()
        dspy.Assert(
            intent in avaliable_intents,
            f"intent should be One of: {' , '.join(avaliable_intents)} nothing more",
        )

        return intent , intent_prediction.feedback
    
    def get_recommendations(self, user_input, chat_history, user_id):
        session = self.get_or_create_session(user_id)
        session.print()
        print("getting recomandations")
        if self.websocket:call_async(self.send_feedback("Do not worry I'll find the perfect product for you"))
        unique_categories =  get_unique("products", "categories")
        values_set = set()
        for dictionary in unique_categories:
            if "uniqueValue" in dictionary:
                values = dictionary["uniqueValue"].lower().split(">")
                values_set.update(map(str.strip, values))
        merged_uniquevalue = " , ".join(values_set)

        keywords_prediction = self.user_input_to_query(user_input=user_input, available_categories=merged_uniquevalue, chat_history=chat_history)
        session.add_to_history( assistant=keywords_prediction.rationale)
        keywords = keywords_prediction.keywords
        print(f"keywords: {keywords}")
        products =  hybrid_search("products", keywords, limit=5)
        # print(f"products: {products}")
        if self.websocket:call_async(self.send_feedback(keywords_prediction.feedback))
        return dspy.Prediction(products=products, action="recommend")

    def add_to_cart(self, user_input, current_products, chat_history, user_id):
        session = self.get_or_create_session(user_id)
        session.print()
        print("add to cart")
        if self.websocket:call_async(self.send_feedback("ok ok wil be added"))
        cart_items_prediction = self.add_to_cart_extractor(user_input=user_input, current_products=current_products, chat_history=chat_history)
        cart_items = cart_items_prediction.products_with_quantity
        session.add_to_history( assistant=cart_items_prediction.rationale)
        if self.websocket:call_async(self.send_feedback(cart_items_prediction.feedback))

        # Gather detailed cart items info
        detailed_cart_items = []
        for item in cart_items:
            product_id = item["product_id"]
            quantity = item.get("quantity", 1)
            
            current_product = self.id_to_product.get(product_id)
            if current_product:
                # Add detailed info to cart item
                detailed_item = {
                    "product_id": product_id,
                    "name": current_product.get("name", "Unknown Product"),
                    "price": current_product.get("price", "Unknown Price"),
                    "quantity": quantity
                }
                detailed_cart_items.append(detailed_item)
        session.cart_items.extend(detailed_cart_items)
        return dspy.Prediction(cart_items=detailed_cart_items, action="add_to_cart")

    def get_more_info(self, user_input, current_products, chat_history, user_id):
        session = self.get_or_create_session(user_id)
        session.print()
        print("get more info")
        if self.websocket:call_async(self.send_feedback("which one you mean???"))
        product = self.ProductInfoExtraction(user_input=user_input, current_products=current_products, chat_history=chat_history)
        session.add_to_history( assistant=product.rationale)
        if self.websocket:call_async(self.send_feedback(product.feedback))
        print(product)
        product_id = product.product_id
        query = product.query
        if not product_id :
            return dspy.Prediction(error="No product specified for more information",feedback=product.feedback ,action="no_product")

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

        # print(f"search_results: {search_results}")


        # Extract relevant information from search results
        # Concatenate the first 5 results' descriptions
        if(search_results.get('web')):
            additional_info = " ".join(result['description'] for result in search_results['web']['results'][:5])
        else:
            additional_info = "no additional information"

        summery = self.SummerizeProductInfo(user_input=user_input,additional_info=additional_info, product=current_product, chat_history=chat_history)

        return dspy.Prediction(product=current_product, additional_info=additional_info ,summery=summery.summery, action="more_info")
    
    async def send_feedback(self, message):
        if self.websocket is not None:
            await self.websocket.send_text(json.dumps({
                "action":"feedback",
                "message": message
            }))
            
def call_async(coro):
    loop = asyncio.get_running_loop()
    return loop.run_until_complete(coro)

    
def process_user_input(user_input: str ,websocket = None, user_id = ""):
    print("process_user_input")
    print(user_id)
    
    global gwebsocket 
    gwebsocket= websocket
    results =  recommendation_system(user_input=user_input, user_id=user_id )

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