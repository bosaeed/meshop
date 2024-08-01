import dspy
from app.utils.embedding import generate_embedding, compute_similarity
from app.utils.database import find_many

lm = dspy.OpenAI(api_key="your-openai-api-key")
dspy.settings.configure(lm=lm)

class RecommendationModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_keywords = dspy.Predict("User Input: {user_input}\nGenerate relevant product keywords:")

    def forward(self, user_input):
        keywords = self.generate_keywords(user_input=user_input)
        return keywords.split(', ')

recommendation_module = RecommendationModule()

async def get_recommendations(user_input: str, user_history: list):
    keywords = recommendation_module(user_input)
    keyword_embedding = generate_embedding(' '.join(keywords))
    
    products = await find_many('products', {})
    
    scored_products = []
    for product in products:
        similarity = compute_similarity(keyword_embedding, product['embedding'])
        scored_products.append((product, similarity))
    
    scored_products.sort(key=lambda x: x[1], reverse=True)
    return [product for product, _ in scored_products[:10]]