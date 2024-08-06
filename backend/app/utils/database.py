# meshop/backend/app/utils/database.py

# from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.utils.embedding import EmbeddingService
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
collection_name = os.getenv("COLLECTION_NAME")
# client = AsyncIOMotorClient(MONGO_URL)
client = MongoClient(MONGO_URL)
db = client.meshop

PRODUCT_SEARCH_INDEX = "product_search_index"
PRODUCTS_VECTOR_INDEX = "products_vector_index"
PRODUCT_SEARCH_FIELD = "name"
PRODUCTS_VECTOR_FIELD= "embedding"

unique_dict = {}

def get_collection(collection_name: str):
    return db[collection_name]

def get_unique(collection_name: str , field_name: str):
    collection = get_collection(collection_name)

    # if unique_dict.get(field_name):
    #     return unique_dict.get(field_name)
    # Define the aggregation pipeline
    pipeline = [
        { "$unwind": f"${field_name}" },  # Step 1: Unwind the list field
        { "$group": { "_id": f"${field_name}" } },  # Step 2: Group by the list element
        { "$project": { "_id": 0, "uniqueValue": "$_id" } }  # Step 3: Project the unique values
    ]

    # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))#.to_list(length=None)
    # results = await collection.distinct(field_name)
    unique_dict[field_name] = results
    return results

def insert_one(collection_name: str, document: dict):
    collection =  get_collection(collection_name)
    result =  collection.insert_one(document)
    return str(result.inserted_id)

def find_one(collection_name: str, query: dict , projection: dict = None):
    collection =  get_collection(collection_name)
    return  collection.find_one(query,projection)

def find_many(collection_name: str, query: dict, projection: dict = None, limit: int = 0):
    collection =  get_collection(collection_name)
    cursor = collection.find(query,projection)
    if limit > 0:
        cursor = cursor.limit(limit)
    return  list(cursor)#.to_list(length=None)

def update_one(collection_name: str, query: dict, update: dict):
    collection =  get_collection(collection_name)
    result =  collection.update_one(query, {"$set": update})
    return result.modified_count

def delete_one(collection_name: str, query: dict):
    collection =  get_collection(collection_name)
    result =  collection.delete_one(query)
    return result.deleted_count



def hybrid_search(collection_name: str, query: str,  limit: int = 20):
    collection =  get_collection(collection_name)
    embedding_service = EmbeddingService()
    vector_query = embedding_service.get_embedding(query)
    

    pipeline = [
        {
            "$vectorSearch": {
                "index": PRODUCTS_VECTOR_INDEX,
                "path": PRODUCTS_VECTOR_FIELD,
                "queryVector": vector_query,
                "numCandidates": 1000,
                "limit": limit
            }
        },
        {
            "$group": {
                "_id": None,
                "docs": {"$push": "$$ROOT"}
            }
        },
        {
            "$unwind": {
                "path": "$docs",
                "includeArrayIndex": "rank"
            }
        },
        {
            "$addFields": {
                "vs_score": {
                    "$divide": [1.0, {"$add": ["$rank", 1, 1]}]
                },
                "vscore": {
                "$meta": "vectorSearchScore"
            }
            }
        },
        {
            "$project": {
                "vs_score": 1,
                "_id": "$docs._id",
                "name": f"$docs.{PRODUCT_SEARCH_FIELD}",
                "description": "$docs.description",
                "sale_price": "$docs.sale_price",
                "regular_price": "$docs.regular_price",
                "categories": "$docs.categories",
                "vendor": "$docs.vendor",
                "type": "$docs.type",
                "tags": "$docs.tags",
                "images": "$docs.images",
                "vscore": 1
                # 'vscore': {
                #     '$meta': 'vectorSearchScore'
                # }
            }
        },
        {
            "$unionWith": {
                "coll": collection_name,
                "pipeline": [
                    {
                        "$search": {
                            "index": PRODUCT_SEARCH_INDEX,
                            "text": {
                                "query": query,
                                "path": ["name","description"],
                                 "fuzzy": {
                                    "maxEdits": 2,
                                    "prefixLength": 0,
                                    "maxExpansions": 50
                                }
                            }
                        }
                    },
                    {"$limit": limit},
                    {
                        "$group": {
                            "_id": None,
                            "docs": {"$push": "$$ROOT"}
                        }
                    },
                    {
                        "$unwind": {
                            "path": "$docs",
                            "includeArrayIndex": "rank"
                        }
                    },
                    {
                        "$addFields": {
                            "fts_score": {
                                "$divide": [1.0, {"$add": ["$rank", 10, 1]}]
                            }
                        }
                    },
                    {
                        "$project": {
                            "fts_score": 1,
                            "_id": "$docs._id",
                            "name": f"$docs.{PRODUCT_SEARCH_FIELD}",
                            "description": "$docs.description",
                            "sale_price": "$docs.sale_price",
                            "regular_price": "$docs.regular_price",
                            "categories": "$docs.categories",
                            "vendor": "$docs.vendor",
                            "type": "$docs.type",
                            "tags": "$docs.tags",
                            "images": "$docs.images",
                            "vscore":{"$add": [0, 0, 0]}
                            
                        }
                    }
                ]
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "name": {"$first": "$name"},
                "description": {"$first": "$description"},
                "sale_price": {"$first": "$sale_price"},
                "regular_price": {"$first": "$regular_price"},
                "categories": {"$first": "$categories"},
                "vendor": {"$first": "$vendor"},
                "type": {"$first": "$type"},
                "tags": {"$first": "$tags"},
                "images": {"$first": "$images"},
                "vs_score": {"$max": "$vs_score"},
                "vscore": {"$max": "$vscore"},
                "fts_score": {"$max": "$fts_score"}
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "description": 1,
                "sale_price": 1,
                "regular_price": 1,
                "categories": 1,
                "vendor": 1,
                "type": 1,
                "tags": 1,
                "images": 1,
                "vs_score": {"$ifNull": ["$vs_score", 0]},
                "vscore": {"$ifNull": ["$vscore", 0]},
                "fts_score": {"$ifNull": ["$fts_score", 0]}
            }
        },
        {
            "$project": {
                "score": {"$add": ["$fts_score", "$vs_score"]},
                "_id": 1,
                "id": "$_id",
                "name": 1,
                "description": 1,
                "sale_price": 1,
                "regular_price": 1,
                "categories": 1,
                "vendor": 1,
                "type": 1,
                "tags": 1,
                "images": 1,
                "vs_score": 1,
                "vscore": 1,
                "fts_score": 1
            }
        },
        {"$sort": {"score": -1}},
        {"$limit": limit}
    ]
    
    return list(collection.aggregate(pipeline))#.to_list(length=None)

def get_autocomplete(collection_name: str,query: str):
    collection = get_collection(collection_name)
    pipeline = [
        {"$search": 
         {
             "index": PRODUCT_SEARCH_INDEX,
             "autocomplete": {
                 "query": query, 
                 "path": "name", 
                "fuzzy": {
                    "maxEdits": 1, 
                    "prefixLength": 1, 
                    "maxExpansions": 256}
           }
        }},
        {"$limit": 10},
        {"$project": 
            {"_id": 0, "name": 1}
        }
    ]
    autocomplete_list = list(collection.aggregate(pipeline))#.to_list(length=None)
    return [item["name"] for item in autocomplete_list]