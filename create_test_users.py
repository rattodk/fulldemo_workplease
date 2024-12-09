from werkzeug.security import generate_password_hash
import mysql.connector
import uuid
import time

# Constants for role IDs (from your database)
ADMIN_ROLE_PK = "16fd2706-8baf-433b-82eb-8c7fada847da"
CUSTOMER_ROLE_PK = "c56a4180-65aa-42ec-a945-5fd21dec0538"
RESTAURANT_ROLE_PK = "9f8c8d22-5a67-4b6c-89d7-58f8b8cb4e15"

# Database connection
connection = mysql.connector.connect(
    host="mysql",
    user="root",
    password="password",
    database="company"
)

cursor = connection.cursor()

def create_user(name, email, role_pk, is_restaurant=False):
    user_pk = str(uuid.uuid4())
    current_time = int(time.time())
    
    # Create base user
    user = {
        "user_pk": user_pk,
        "user_name": name,
        "user_last_name": "Test",
        "user_email": email,
        "user_password": generate_password_hash("password123"),
        "user_avatar": "",
        "user_created_at": current_time,
        "user_deleted_at": 0,
        "user_blocked_at": 0,
        "user_updated_at": 0,
        "user_verified_at": current_time,  # Auto verified
        "user_verification_key": str(uuid.uuid4())
    }
    
    cursor.execute("""
        INSERT INTO users VALUES (
            %(user_pk)s, %(user_name)s, %(user_last_name)s,
            %(user_email)s, %(user_password)s, %(user_avatar)s,
            %(user_created_at)s, %(user_deleted_at)s, %(user_blocked_at)s,
            %(user_updated_at)s, %(user_verified_at)s, %(user_verification_key)s
        )
    """, user)
    
    # Assign role
    cursor.execute("""
        INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
        VALUES (%s, %s)
    """, (user_pk, role_pk))
    
    # If restaurant, create restaurant details
    if is_restaurant:
        restaurant_pk = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO restaurant_details (
                restaurant_pk, restaurant_user_fk, restaurant_name,
                restaurant_description, restaurant_phone, restaurant_address,
                restaurant_city, restaurant_postal_code, restaurant_created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            restaurant_pk, user_pk, f"{name}'s Restaurant",
            "A test restaurant", "12345678",
            "Test Street 123", "Test City", "1234",
            current_time
        ))
    
    return user_pk

try:
    # Create customer
    customer_pk = create_user("Customer", "customer@test.com", CUSTOMER_ROLE_PK)
    print("Created customer user:")
    print("Email: customer@test.com")
    print("Password: password123")
    print()
    
    # Create admin
    admin_pk = create_user("Admin", "admin@test.com", ADMIN_ROLE_PK)
    print("Created admin user:")
    print("Email: admin@test.com")
    print("Password: password123")
    print()
    
    # Create restaurant
    restaurant_pk = create_user("Restaurant", "restaurant@test.com", RESTAURANT_ROLE_PK, True)
    print("Created restaurant user:")
    print("Email: restaurant@test.com")
    print("Password: password123")
    print()
    
    connection.commit()
    print("All test users created successfully!")

except Exception as e:
    print(f"Error creating test users: {e}")
    connection.rollback()
finally:
    cursor.close()
    connection.close()