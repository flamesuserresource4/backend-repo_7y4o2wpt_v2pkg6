import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order, OrderItem

app = FastAPI(title="Soni Zi Creations API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc = dict(doc)
    if doc.get("_id"):
        doc["id"] = str(doc.pop("_id"))
    # Convert datetimes to isoformat
    for k, v in list(doc.items()):
        if hasattr(v, "isoformat"):
            doc[k] = v.isoformat()
    return doc

@app.get("/")
def read_root():
    return {"message": "Soni Zi Creations API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from Soni Zi Creations backend!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Products Endpoints
@app.get("/api/products")
def list_products(category: Optional[str] = None):
    try:
        filter_q = {"category": category} if category else {}
        docs = get_documents("product", filter_q)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products", status_code=201)
def create_product(product: Product):
    try:
        new_id = create_document("product", product)
        doc = db["product"].find_one({"_id": ObjectId(new_id)})
        return serialize_doc(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Orders Endpoints
class CheckoutPayload(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    shipping_address: str
    items: List[OrderItem]

@app.post("/api/orders", status_code=201)
def create_order(payload: CheckoutPayload):
    try:
        # Calculate subtotal and total (no tax/shipping for demo)
        subtotal = 0.0
        for item in payload.items:
            prod = db["product"].find_one({"_id": PyObjectId.validate(item.product_id)})
            if not prod:
                raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
            subtotal += float(prod.get("price", 0)) * item.quantity
        order = Order(
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            customer_phone=payload.customer_phone,
            shipping_address=payload.shipping_address,
            items=payload.items,
            subtotal=round(subtotal, 2),
            total=round(subtotal, 2),
        )
        new_id = create_document("order", order)
        doc = db["order"].find_one({"_id": ObjectId(new_id)})
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
def list_orders(email: Optional[str] = None):
    try:
        q = {"customer_email": email} if email else {}
        docs = get_documents("order", q)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Seed demo products for quick start
@app.post("/api/seed", status_code=201)
def seed_products():
    try:
        if db["product"].count_documents({}) > 0:
            return {"message": "Products already exist"}
        sample_products = [
            {
                "title": "Handcrafted Silk Scarf",
                "description": "Premium silk scarf with elegant patterns",
                "price": 1499.0,
                "category": "Accessories",
                "in_stock": True,
                "stock_qty": 25,
                "image": "https://images.unsplash.com/photo-1520975693411-b40e8f1de1e5?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "title": "Artisanal Pottery Vase",
                "description": "Handmade ceramic vase with glaze finish",
                "price": 2299.0,
                "category": "Home Decor",
                "in_stock": True,
                "stock_qty": 12,
                "image": "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "title": "Embroidered Tote Bag",
                "description": "Canvas tote with traditional embroidery",
                "price": 999.0,
                "category": "Bags",
                "in_stock": True,
                "stock_qty": 40,
                "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=1200&auto=format&fit=crop"
            }
        ]
        inserted = db["product"].insert_many(sample_products)
        return {"inserted": len(inserted.inserted_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
