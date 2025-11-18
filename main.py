import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="Surf Shirts Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Surf Shirts Store Backend is running"}

# Utility to convert Mongo document to JSON-serializable

def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    return doc

# Seed some demo products if collection empty
@app.post("/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"seeded": False, "message": "Products already exist"}

    demo_products = [
        {
            "title": "Sunset Barrel Tee",
            "description": "Ultra-soft tee with sunset barrel graphic.",
            "price": 29.0,
            "category": "surf-shirts",
            "sizes": ["S","M","L","XL"],
            "colors": ["white","navy"],
            "image_url": "https://images.unsplash.com/photo-1490474418585-ba9bad8fd0ea?q=80&w=1600&auto=format&fit=crop",
            "featured": True,
            "stock_count": 80,
        },
        {
            "title": "Aqua Lineup Tee",
            "description": "Breathable cotton tee inspired by the lineup.",
            "price": 32.0,
            "category": "surf-shirts",
            "sizes": ["S","M","L"],
            "colors": ["black","aqua"],
            "image_url": "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?q=80&w=1600&auto=format&fit=crop",
            "featured": True,
            "stock_count": 60,
        },
        {
            "title": "Reef Break Tee",
            "description": "Minimal design with reef break coordinates.",
            "price": 27.0,
            "category": "surf-shirts",
            "sizes": ["M","L","XL"],
            "colors": ["navy","sand"],
            "image_url": "https://images.unsplash.com/photo-1482867899247-e295efdd8c1c?q=80&w=1600&auto=format&fit=crop",
            "featured": False,
            "stock_count": 40,
        },
    ]

    for p in demo_products:
        create_document("product", p)

    return {"seeded": True, "count": len(demo_products)}

@app.get("/products")
def list_products():
    products = get_documents("product")
    return [serialize_doc(p) for p in products]

@app.get("/products/featured")
def featured_products():
    products = db["product"].find({"featured": True}).limit(6)
    return [serialize_doc(p) for p in products]

@app.get("/products/{product_id}")
def get_product(product_id: str):
    try:
        obj_id = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    product = db["product"].find_one({"_id": obj_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_doc(product)

@app.post("/orders")
def create_order(order: Order):
    # Basic stock check (non-atomic, demo purposes)
    for item in order.items:
        try:
            obj_id = ObjectId(item.product_id)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid product id: {item.product_id}")
        product = db["product"].find_one({"_id": obj_id})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        if product.get("stock_count", 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['title']}")

    order_id = create_document("order", order)

    # Decrement stock (simple per item)
    for item in order.items:
        db["product"].update_one({"_id": ObjectId(item.product_id)}, {"$inc": {"stock_count": -item.quantity}})

    return {"id": order_id, "status": "received"}

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
            response["database_url"] = "✅ Configured"
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

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
