from flask import Blueprint, request, session
import x
import uuid
import time

ROUTE_VARIABLE_items = Blueprint("ROUTE_VARIABLE_items", __name__)

@ROUTE_VARIABLE_items.post("/items")
@x.no_cache
def create_item():
    try:
        if "restaurant" not in session.get("user", {}).get("roles", []):
            return """<template mix-target="#toast">Unauthorized</template>""", 401
            
        item_name = request.form.get("item_name", "").strip()
        item_description = request.form.get("item_description", "").strip()
        item_price = float(request.form.get("item_price", 0))
        item_category = request.form.get("item_category", "").strip()
        
        # Validate inputs
        if not 2 <= len(item_name) <= 100:
            return """<template mix-target="#toast">Item name must be 2-100 characters</template>""", 400
        if not 0 < item_price <= 10000:
            return """<template mix-target="#toast">Invalid price</template>""", 400
        if not 2 <= len(item_category) <= 50:
            return """<template mix-target="#toast">Category must be 2-50 characters</template>""", 400
            
        # Create item
        item_pk = str(uuid.uuid4())
        current_time = int(time.time())
        
        db, cursor = x.db()
        cursor.execute("""
            INSERT INTO items (
                item_pk, item_restaurant_fk, item_name, item_description,
                item_price, item_category, item_created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            item_pk, session["user"]["user_pk"], item_name, 
            item_description, item_price, item_category, current_time
        ))
        
        # Handle image uploads
        images = request.files.getlist("item_images")
        for idx, image in enumerate(images[:3]):  # Max 3 images
            if image and x.allowed_file(image.filename):
                image_pk = str(uuid.uuid4())
                filename = x.save_file(image, "items")
                cursor.execute("""
                    INSERT INTO item_images (image_pk, image_item_fk, image_url, image_order)
                    VALUES (%s, %s, %s, %s)
                """, (image_pk, item_pk, filename, idx))
        
        db.commit()
        return """<template mix-target="#toast">Item created</template>""", 201
        
    except Exception as ex:
        if "db" in locals(): db.rollback()
        return """<template mix-target="#toast">Error creating item</template>""", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()