import mysql.connector
from werkzeug.security import generate_password_hash
import uuid
import time

# Database connection details
DB_HOST = "mysql"
DB_USER = "root"
DB_PASSWORD = "password"  # Replace with your actual database password
DB_NAME = "company"  # Replace with your actual database name

# Admin user details
admin_email = 'admin@test.com'
admin_password = 'password123'  # Replace with desired password

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

        # Hash the password using werkzeug
        hashed_password = generate_password_hash(admin_password)

        # Admin user data
        user_pk = str(uuid.uuid4())  # Generate unique user_pk
        verification_key = str(uuid.uuid4())  # Generate unique verification key
        current_time = int(time.time())  # Get current timestamp

        # Insert the admin user into the users table
        cursor.execute("""
            INSERT INTO users (user_pk, user_name, user_last_name, user_email, 
                               user_password, user_avatar, user_created_at, 
                               user_deleted_at, user_blocked_at, user_updated_at, 
                               user_verified_at, user_verification_key)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_pk, 'Admin', 'User', admin_email, hashed_password, '', current_time, 0, 0, 0, current_time, verification_key))

        # Get the role PK for 'admin' role
        cursor.execute("SELECT role_pk FROM roles WHERE role_name = 'admin'")
        role_data = cursor.fetchone()
        if role_data:
            role_pk = role_data['role_pk']

            # Insert into users_roles to assign the 'admin' role to the admin user
            cursor.execute("""
                INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
                VALUES (%s, %s)
            """, (user_pk, role_pk))

            # Commit the changes
            db.commit()
            print(f"Admin user created and role assigned: {admin_email}")
        else:
            print("Error: Admin role not found")
            db.rollback()

    except mysql.connector.Error as e:
        print(f"Error creating admin user: {e}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

# Call the function to create the admin user
create_admin_user()
