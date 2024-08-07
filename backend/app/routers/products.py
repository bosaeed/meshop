from typing import Dict, List
from fastapi import APIRouter, HTTPException ,status
from app.models.product import Product, ProductCreate
from app.utils.database import insert_one, find_many, find_one
from app.utils.embedding import EmbeddingService
from bson import ObjectId
import os
from dotenv import load_dotenv
load_dotenv()


def get_embedding_text(product: Dict) -> str:
    return f"{product['name']} {product['description']} {' '.join(product['categories'])} {' '.join(product['sizes'])} {' '.join(product['colors'])} {product['vendor']} {product['type']} {' '.join(product['tags'])}"

collection_name = os.getenv("COLLECTION_NAME")

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/",  response_model=Product ,  response_description="Add new product",
            status_code=status.HTTP_201_CREATED,  response_model_by_alias=False,)
async def create_product(product: ProductCreate):
    product_dict = product.model_dump(by_alias=True, exclude=["id"])
    print(product_dict)
    # Get embedding for a product description
    embedding_service = EmbeddingService()
    product_dict["embedding"] = embedding_service.get_embedding(get_embedding_text(product), input_type="query")
    product_id = await insert_one(collection_name, product_dict)
    return {**product_dict, "id": product_id}


@router.post("/batch", response_model=List[Product])
async def create_products(products: List[ProductCreate]):
    product_dicts = [product.model_dump(by_alias=True, exclude=["id"]) for product in products]
    texts = [get_embedding_text(product) for product in products]
    embedding_service = EmbeddingService()
    lazy_embeddings = embedding_service.get_embeddings(texts, input_type="document")
    
    created_products = []
    for product_dict, lazy_embedding in zip(product_dicts, lazy_embeddings):
        product_dict["embedding"] = lazy_embedding.get()
        product_id = await insert_one(collection_name, product_dict)
        created_products.append({**product_dict, "id": product_id})
    
    return created_products


@router.get("/", 
            response_model=list[Product],
             response_model_by_alias=False,)
async def get_products():
    limit = 5
    projection = {"embedding": 0}
    products = await find_many(collection_name, {},projection ,limit=limit)
    print(products)
    return products

@router.get("/{product_id}", 
            response_model=Product,
             response_model_by_alias=False,)
async def get_product(product_id: str):
    projection = {"embedding": 0}
    product = await find_one(collection_name, {"_id": ObjectId(product_id)},projection)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product