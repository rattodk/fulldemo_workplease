import mysql.connector
import uuid
import time
from werkzeug.security import generate_password_hash
import logging

# Setup logging
logging.basicConfig(filename="admin_creation.log", level=logging.INFO)

# Database connection details
DB_HOST = "mysql"
DB_USER = "root"
DB_PASSWORD = "password"  # Replace with your actual database password
DB_NAME = "company"  # Replace with your actual database name

def create_admin_user():
    db = None
    cursor = None
    try:
        # Establish database connection
        db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = db.cursor()

        # Admin user data
        email = "admin@test.com"
        password = "password123"
        role = "admin"
        
        user_pk = str(uuid.uuid4())  # Generate unique user_pk
        verification_key = str(uuid.uuid4())  # Generate unique verification key
        current_time = int(time.time())  # Get current timestamp
        hashed_password = generate_password_hash(password)  # Hash the password

        # Insert admin user into the 'users' table
        cursor.execute("""
            INSERT INTO users (user_pk, user_name, user_last_name, user_email, 
                               user_password, user_avatar, user_created_at, 
                               user_deleted_at, user_blocked_at, user_updated_at, 
                               user_verified_at, user_verification_key)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_pk, "Admin", "User", email, hashed_password, "", current_time, 0, 0, 0, current_time, verification_key))

        # Get the role PK
        cursor.execute("SELECT role_pk FROM roles WHERE role_name = %s", (role,))
        role_data = cursor.fetchone()
        if role_data:
            role_pk = role_data[0]

            # Assign role to the admin user
            cursor.execute("""
                INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
                VALUES (%s, %s)
            """, (user_pk, role_pk))

            # Commit the transaction
            db.commit()
            logging.info(f"Created admin account for {email}")
        else:
            logging.error(f"Role '{role}' not found for user {email}")
            db.rollback()

    except mysql.connector.Error as e:
        logging.error(f"Error creating admin user: {str(e)}")
    finally:
        # Ensure resources are cleaned up
        if cursor:
            cursor.close()
        if db:
            db.close()

# Run the function to create the admin user
create_admin_user()
