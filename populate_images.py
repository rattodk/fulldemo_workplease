import os
import random
import mysql.connector

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="mysql",  # Update with your host
        user="root",  # Update with your user
        password="password",  # Update with your password
        database="company"  # Update with your database name
    )

# Replace current images with new random images
def replace_images():
    try:
        # Connect to the database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get all dishes with images
        cursor.execute("""
            SELECT image_pk, image_url
            FROM item_images
        """)
        images = cursor.fetchall()

        if not images:
            print("No images found in the database.")
            return

        # Get all images from the uploads folder
        uploads_folder = "static/uploads"
        new_images = [img for img in os.listdir(uploads_folder) if img.lower().startswith('dish_') and img.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]

        if not new_images:
            print("No new images found in the uploads folder.")
            return

        # Replace old images with random new ones
        for image in images:
            random_image = random.choice(new_images)
            cursor.execute("""
                UPDATE item_images
                SET image_url = %s
                WHERE image_pk = %s
            """, (random_image, image['image_pk']))
            print(f"Updated image_pk {image['image_pk']} with new image {random_image}")

        # Commit changes
        db.commit()
        print("Images successfully replaced.")

    except Exception as e:
        print("An error occurred:", e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

# Run the script
if __name__ == "__main__":
    replace_images()
