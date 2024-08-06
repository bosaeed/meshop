# meshop/backend/app/scripts/init_database.py

import asyncio
import csv
import sys
import os


# Assuming `init_database.py` is in the `scripts` directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.database import insert_one
from app.utils.embedding import embedding_service
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
collection_name = os.getenv("COLLECTION_NAME")
client = AsyncIOMotorClient(MONGO_URL)
db = client.meshop
products_csv = 'products.csv'

def get_embedding_text(product: Dict) -> str:
    return f"{product['name']} {product['description']} {' '.join(product['categories'])} {' '.join(product['sizes'])} {' '.join(product['colors'])} {product['vendor']} {product['type']} {' '.join(product['tags'])}"

async def insert_products(products: List[Dict]):
    # Generate embeddings for 10 products at a time
    texts = [get_embedding_text(product) for product in products]
    lazy_embeddings = embedding_service.get_embeddings(texts, input_type="query")
    
    for product, lazy_embedding in zip(products, lazy_embeddings):
        product['embedding'] = lazy_embedding
        product_id = await insert_one(collection_name, product)
        print(f"Inserted product: {product['name']} with ID: {product_id}")

async def init_database():
    # Clear existing products
    await db.products.delete_many({})

    products = []
    # print(os.path.join(os.path.dirname(__file__), products_csv))
    p_path = os.path.join(os.path.dirname(__file__), products_csv)
    with open(p_path, 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            product = {
                'name': row['Name'],
                'description': row['Description'],
                'sale_price': float(row['Sale price']),
                'regular_price': float(row['Regular price']),
                'categories': row['Categories'].split(','),
                'sizes': row['Sizes'].split(','),
                'colors': row['Colors'].split(','),
                'vendor': row['Vendor'],
                'type': row['Type'],
                'tags': row['Tags'].split(','),
                'images': row['Images'].split(',')
            }
            products.append(product)
            
            # Process in batches of 10
            if len(products) == 30:
                await insert_products(products)
                products = []
    
    # Insert any remaining products
    if products:
        await insert_products(products)

if __name__ == "__main__":
    asyncio.run(init_database())