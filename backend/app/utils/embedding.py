# meshop/backend/app/utils/embedding.py

from openai import OpenAI
from typing import List
import os

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("NVIDIA_API_KEY"),
            base_url="https://integrate.api.nvidia.com/v1"
        )
        self.model = "nvidia/nv-embed-v1"
        self.embed_cache = {}
    def get_embedding(self, text: str, input_type: str = "query") -> List[float]:
        # Check embed_cache before request
        cache_key = (text, input_type)
        if cache_key in self.embed_cache:
            return self.embed_cache[cache_key]
        
        # Make a request if not present in cache
        response = self.client.embeddings.create(
            input=[text],
            model=self.model,
            encoding_format="float",
            extra_body={"input_type": input_type, "truncate": "NONE"}
        )
        
        # Extract and cache the embedding
        embedding = response.data[0].embedding
        self.embed_cache[cache_key] = embedding

        return embedding

    def get_embeddings(self, texts: List[str], input_type: str = "query") -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model,
            encoding_format="float",
            extra_body={"input_type": input_type, "truncate": "NONE"}
        )
        return [data.embedding for data in response.data]

embedding_service = EmbeddingService()

# Example usage:
if __name__ == "__main__":
    # Single embedding
    query = "What is the capital of France?"
    embedding = embedding_service.get_embedding(query)
    print(f"Embedding for '{query}':")
    print(embedding[:5])  # Print first 5 elements

    # Multiple embeddings
    texts = ["Hello, world!", "How are you?", "OpenAI is amazing"]
    embeddings = embedding_service.get_embeddings(texts)
    print("\nEmbeddings for multiple texts:")
    for text, emb in zip(texts, embeddings):
        print(f"'{text}': {emb[:5]}...")  # Print first 5 elements of each embedding