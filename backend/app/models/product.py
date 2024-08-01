# meshop/backend/app/models/products.py

from pydantic import BaseModel , Field ,ConfigDict
from typing import List , Optional
from bson import ObjectId
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]
class Product(BaseModel):
    id: Optional[PyObjectId]  = Field( alias="_id", default=None)
    name: str = Field(...)
    description: str = Field(...)
    sale_price: float
    regular_price: float
    categories: List[str]
    sizes: List[str]
    colors: List[str]
    vendor: str
    type: str
    tags: List[str]
    images: List[str]
    embedding: Optional[List[float]] = Field( default=None) 
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "blue t-shirt",
                "description": "blue t-shirt large",
                "sale_price": 10.55,
                "regular_price": 15.99,
                "categories": ["clothes", "t-shirts"],
                "sizes": ["S", "M", "L"],
                "colors": ["blue"],
                "vendor": "Example Vendor",
                "type": "clothing",
                "tags": ["casual", "summer"],
                "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
            }
        },
    )
class ProductCreate(BaseModel):
    name: str
    description: str
    sale_price: float
    regular_price: float
    categories: List[str]
    sizes: List[str]
    colors: List[str]
    vendor: str
    type: str
    tags: List[str]
    images: List[str]