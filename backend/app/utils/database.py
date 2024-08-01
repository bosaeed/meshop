# meshop/backend/app/utils/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client.meshop

PRODUCT_SEARCH_INDEX = "product_search_index"
PRODUCTS_VECTOR_INDEX = "products_vector_index"
PRODUCT_SEARCH_FIELD = "name"
PRODUCTS_VECTOR_FIELD= "embedding"

async def get_collection(collection_name: str):
    return db[collection_name]

async def insert_one(collection_name: str, document: dict):
    collection = await get_collection(collection_name)
    result = await collection.insert_one(document)
    return str(result.inserted_id)

async def find_one(collection_name: str, query: dict , projection: dict = None):
    collection = await get_collection(collection_name)
    return await collection.find_one(query,projection)

async def find_many(collection_name: str, query: dict, projection: dict = None, limit: int = 0):
    collection = await get_collection(collection_name)
    cursor = collection.find(query,projection)
    if limit > 0:
        cursor = cursor.limit(limit)
    return await cursor.to_list(length=None)

async def update_one(collection_name: str, query: dict, update: dict):
    collection = await get_collection(collection_name)
    result = await collection.update_one(query, {"$set": update})
    return result.modified_count

async def delete_one(collection_name: str, query: dict):
    collection = await get_collection(collection_name)
    result = await collection.delete_one(query)
    return result.deleted_count



async def hybrid_search(collection_name: str, vector_query: list, text_query: str,  limit: int = 20):
    collection = await get_collection(collection_name)
    

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
                "vscore": 1,
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
                                "query": text_query,
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
                            "name": f"$docs.{PRODUCT_SEARCH_FIELD}"
                        }
                    }
                ]
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "name": {"$first": "$name"},
                "vs_score": {"$max": "$vs_score"},
                "vscore": {"$max": "$vscore"},
                "fts_score": {"$max": "$fts_score"}
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "vs_score": {"$ifNull": ["$vs_score", 0]},
                "vscore": {"$ifNull": ["$vscore", 0]},
                "fts_score": {"$ifNull": ["$fts_score", 0]}
            }
        },
        {
            "$project": {
                "score": {"$add": ["$fts_score", "$vs_score"]},
                "_id": 1,
                "name": 1,
                "vs_score": 1,
                "vscore": 1,
                "fts_score": 1
            }
        },
        {"$sort": {"score": -1}},
        {"$limit": limit}
    ]
    
    return await collection.aggregate(pipeline).to_list(length=None)

async def get_autocomplete(collection_name: str,query: str):
    collection = await get_collection(collection_name)
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
    return await collection.aggregate(pipeline).to_list(length=None)