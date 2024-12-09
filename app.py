from flask import Flask, session, render_template, redirect, url_for, request, flash, get_flashed_messages
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import time
from db import get_db_connection
from config import EMAIL_CONFIG
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import mysql.connector
import random 
from datetime import datetime, timedelta
import math
from werkzeug.utils import secure_filename
import os


# Constants
CUSTOMER_ROLE_PK = "c56a4180-65aa-42ec-a945-5fd21dec0538"
RESTAURANT_ROLE_PK = "9f8c8d22-5a67-4b6c-89d7-58f8b8cb4e15"
DELIVERY_ROLE_PK = "f47ac10b-58cc-4372-a567-0e02b2c3d479"



class CustomException(Exception):
    def __init__(self, message, code=400):
        self.message = message
        self.code = code


def send_verify_email(email, verification_key):
    try:
        # Create the email message
        message = MIMEMultipart()
        message["From"] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message["To"] = email
        message["Subject"] = "Verify Your Email"

        # Email body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Verify Your Email</h2>
                    <p>Thank you for signing up! Please verify your email by clicking the link below:</p>
                    <div style="margin: 20px 0; text-align: center;">
                        <a href="{EMAIL_CONFIG['BASE_URL']}/verify/{verification_key}"
                           style="background-color: #0066cc; color: white; padding: 12px 25px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            Verify Account
                        </a>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        Verification Key: {verification_key}
                    </p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        If you did not sign up for this account, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Log email content for debugging
        print(f"Sending email to: {email}")
        print(f"Email subject: {message['Subject']}")
        print(f"Email body: {body}")

        # Connect to the SMTP server and send email
        print("Connecting to SMTP server...")
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            print("Starting TLS...")
            server.starttls()
            print("Logging in...")
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['APP_PASSWORD'])
            print("Sending email...")
            server.send_message(message)

        print("Email sent successfully!")
        return True

    except Exception as ex:
        import traceback
        print(f"Error sending email: {str(ex)}")
        traceback.print_exc()
        return False

# Initialize Flask App
app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# Add these configurations after your other app configurations
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Home Route
@app.route('/')
def view_index():
    return render_template("view_index.html")

# Sign-Up Routes
@app.route('/signup/customer')
def view_customer_signup():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return render_template("signup/customer.html")

def send_reset_email(email, reset_token):
    try:
        reset_url = f"{EMAIL_CONFIG['BASE_URL']}/reset-password/{reset_token}"
        message = MIMEMultipart()
        message["From"] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message["To"] = email
        message["Subject"] = "Reset Your Password"

        # Email body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Reset Your Password</h2>
                    <p>Please reset your password by clicking the link below:</p>
                    <div style="margin: 20px 0; text-align: center;">
                        <a href="{reset_url}"
                           style="background-color: #0066cc; color: white; padding: 12px 25px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        If you did not request this password reset, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Log email content for debugging
        print(f"Sending email to: {email}")
        print(f"Email subject: {message['Subject']}")
        print(f"Email body: {body}")

        # Connect to the SMTP server and send email
        print("Connecting to SMTP server...")
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            print("Starting TLS...")
            server.starttls()
            print("Logging in...")
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['APP_PASSWORD'])
            print("Sending email...")
            server.send_message(message)

        print("Email sent successfully!")
        return True

    except Exception as ex:
        import traceback
        print(f"Error sending email: {str(ex)}")
        traceback.print_exc()
        return False


@app.route('/reset-password/<reset_token>', methods=['GET', 'POST'])
def reset_password(reset_token):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Validate the reset token
        cursor.execute("""
            SELECT user_pk, reset_token_expiry FROM users 
            WHERE reset_token = %s AND reset_token_expiry > %s
        """, (reset_token, int(datetime.utcnow().timestamp())))
        user = cursor.fetchone()

        if not user:
            return render_template("reset_password.html", error="Invalid or expired reset token")

        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not new_password or not confirm_password:
                return render_template("reset_password.html", error="Please fill out all fields")
            if new_password != confirm_password:
                return render_template("reset_password.html", error="Passwords do not match")

            # Update the password
            hashed_password = generate_password_hash(new_password)
            cursor.execute("""
                UPDATE users SET user_password = %s, reset_token = NULL, reset_token_expiry = NULL
                WHERE user_pk = %s
            """, (hashed_password, user['user_pk']))
            db.commit()

            return redirect(url_for('login', message="Password reset successfully"))

        return render_template("reset_password.html")

    except Exception as e:
        print(f"Error in reset_password: {e}")
        return render_template("reset_password.html", error="An error occurred")

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()  # Normalize email
        print(f"Searching for email: {email}")  # Debugging

        if not email:
            return render_template("forgot_password.html", error="Please enter your email")

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            # Check if the email exists
            cursor.execute("""
                SELECT user_pk FROM users 
                WHERE LOWER(user_email) = LOWER(%s) AND (user_deleted_at IS NULL OR user_deleted_at = 0)
            """, (email,))
            user = cursor.fetchone()
            print(f"Query result: {user}")  # Debugging

            if not user:
                return render_template("forgot_password.html", error="Email not found")

            # Generate reset token and expiry
            reset_token = str(uuid.uuid4())
            reset_token_expiry = int((datetime.utcnow() + timedelta(hours=1)).timestamp())

            # Update database with the reset token and expiry
            cursor.execute("""
                UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE user_pk = %s
            """, (reset_token, reset_token_expiry, user['user_pk']))
            db.commit()

            # Send reset email
            if not send_reset_email(email, reset_token):
                return render_template("forgot_password.html", error="Failed to send reset email")

            return render_template("forgot_password.html", message="Check your email for a reset link")

        except Exception as e:
            print(f"Error in forgot_password: {e}")
            return render_template("forgot_password.html", error="An error occurred")

        finally:
            if 'cursor' in locals(): cursor.close()
            if 'db' in locals(): db.close()

    # Serve the forgot password page
    return render_template("forgot_password.html")

@app.route("/users/customer", methods=["POST"])
def signup_customer():
    try:
        print("Signup started")
        # Get form data
        user_name = request.form.get("user_name")
        user_last_name = request.form.get("user_last_name")
        user_email = request.form.get("user_email")
        user_password = request.form.get("user_password")
        print(f"Form data: {user_name}, {user_last_name}, {user_email}")

        # Validate input
        if not all([user_name, user_last_name, user_email, user_password]):
            print("Validation failed: Missing fields")
            return """<template mix-target="#toast">All fields are required</template>""", 400

        # Generate UUIDs and timestamps
        user_pk = str(uuid.uuid4())
        verification_key = str(uuid.uuid4())
        current_time = int(time.time())
        print(f"Generated user_pk: {user_pk}, verification_key: {verification_key}")

        # Establish database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        print("Database connection established")

        # Check if the email is already registered
        cursor.execute("SELECT user_pk FROM users WHERE user_email = %s", (user_email,))
        if cursor.fetchone():
            print("Email already registered")
            return """<template mix-target="#toast">Email already registered</template>""", 400

        # Hash the password
        hashed_password = generate_password_hash(user_password)
        print("Password hashed")

        # Prepare user data
        user = {
            "user_pk": user_pk,
            "user_name": user_name,
            "user_last_name": user_last_name,
            "user_email": user_email,
            "user_password": hashed_password,
            "user_avatar": "",
            "user_created_at": current_time,
            "user_deleted_at": 0,
            "user_blocked_at": 0,
            "user_updated_at": 0,
            "user_verified_at": 0,
            "user_verification_key": verification_key
        }

        # Insert user into the database (updated query)
        cursor.execute("""
            INSERT INTO users (
                user_pk, user_name, user_last_name, user_email, 
                user_password, user_avatar, user_created_at, 
                user_deleted_at, user_blocked_at, user_updated_at, 
                user_verified_at, user_verification_key, 
                reset_token, reset_token_expiry
            ) VALUES (
                %(user_pk)s, %(user_name)s, %(user_last_name)s, %(user_email)s, 
                %(user_password)s, %(user_avatar)s, %(user_created_at)s, 
                %(user_deleted_at)s, %(user_blocked_at)s, %(user_updated_at)s, 
                %(user_verified_at)s, %(user_verification_key)s, 
                NULL, NULL
            )
        """, user)
        print("User inserted into the database")

        # Assign role to the user
        cursor.execute("""
            INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
            VALUES (%s, %s)
        """, (user_pk, CUSTOMER_ROLE_PK))
        print("Role assigned to user")

        # Send verification email
        print(f"Sending email to: {user_email}")
        if not send_verify_email(user_email, verification_key):
            print("send_verify_email failed, rolling back database changes")
            db.rollback()
            return """<template mix-target="#toast">Email verification failed</template>""", 500

        # Commit the database transaction
        db.commit()
        print("Signup successful, transaction committed")

        # Success response
        return render_template("login.html", message="Please check your email to verify your account")

    except Exception as ex:
        import traceback
        print(f"Signup error: {str(ex)}")
        traceback.print_exc()
        if "db" in locals(): db.rollback()
        return """<template mix-target="#toast">System under maintenance</template>""", 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

# Use the DELIVERY_ROLE_PK from your database


@app.route('/signup/delivery')
def view_delivery_signup():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return render_template("signup/delivery.html")
@app.route('/signup/delivery', methods=['POST'])
def signup_delivery():
    try:
        print("Signup started")
        # Get form data
        user_name = request.form.get("user_name")
        user_last_name = request.form.get("user_last_name")
        user_email = request.form.get("user_email")
        user_password = request.form.get("user_password")
        vehicle_type = request.form.get("vehicle_type")
        print(f"Form data: {user_name}, {user_last_name}, {user_email}, {vehicle_type}")

        # Validate input
        if not all([user_name, user_last_name, user_email, user_password, vehicle_type]):
            print("Validation failed: Missing fields")
            return """<template mix-target="#toast">All fields are required</template>""", 400

        if len(user_password) < 6:
            print("Password is too short")
            return """<template mix-target="#toast">Password must be at least 6 characters</template>""", 400

        # Generate UUIDs and timestamps
        user_pk = str(uuid.uuid4())
        verification_key = str(uuid.uuid4())
        current_time = int(time.time())
        print(f"Generated user_pk: {user_pk}, verification_key: {verification_key}")

        # Establish database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        print("Database connection established")

        # Check if the email is already registered
        cursor.execute("SELECT user_pk FROM users WHERE user_email = %s", (user_email,))
        if cursor.fetchone():
            print("Email already registered")
            return """<template mix-target="#toast">Email already registered</template>""", 400

        # Hash the password
        hashed_password = generate_password_hash(user_password)
        print("Password hashed")

        # Prepare user data
        user = {
            "user_pk": user_pk,
            "user_name": user_name,
            "user_last_name": user_last_name,
            "user_email": user_email,
            "user_password": hashed_password,
            "user_avatar": "",
            "user_created_at": current_time,
            "user_deleted_at": 0,
            "user_blocked_at": 0,
            "user_updated_at": 0,
            "user_verified_at": 0,
            "user_verification_key": verification_key
        }

        # Insert user into the database
        cursor.execute("""
            INSERT INTO users (
                user_pk, user_name, user_last_name, user_email, 
                user_password, user_avatar, user_created_at, 
                user_deleted_at, user_blocked_at, user_updated_at, 
                user_verified_at, user_verification_key
            ) VALUES (
                %(user_pk)s, %(user_name)s, %(user_last_name)s, %(user_email)s, 
                %(user_password)s, %(user_avatar)s, %(user_created_at)s, 
                %(user_deleted_at)s, %(user_blocked_at)s, %(user_updated_at)s, 
                %(user_verified_at)s, %(user_verification_key)s
            )
        """, user)
        print("User inserted into the database")

        # Assign 'delivery' role to the user
        cursor.execute("""
            SELECT role_pk FROM roles WHERE role_name = 'delivery'
        """)
        role = cursor.fetchone()
        if not role:
            print("Delivery role does not exist")
            return """<template mix-target="#toast">Role does not exist</template>""", 400

        cursor.execute("""
            INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
            VALUES (%s, %s)
        """, (user_pk, role['role_pk']))
        print("Role assigned to user")

        # Send verification email
        print(f"Sending email to: {user_email}")
        if not send_verify_email(user_email, verification_key):
            print("send_verify_email failed, rolling back database changes")
            db.rollback()
            return """<template mix-target="#toast">Email verification failed</template>""", 500

        # Commit the database transaction
        db.commit()
        print("Signup successful, transaction committed")

        # Success response
        return render_template("login.html", message="Please check your email to verify your account")

    except Exception as ex:
        import traceback
        print(f"Signup error: {str(ex)}")
        traceback.print_exc()
        if "db" in locals(): db.rollback()
        return """<template mix-target="#toast">System under maintenance</template>""", 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

@app.route('/signup/restaurant', methods=['GET'])
def view_restaurant_signup():
    if session.get("user"):
        # Redirect to the dashboard if the user is already logged in
        return redirect(url_for("dashboard"))
    # Render the restaurant signup page
    return render_template("signup/restaurant.html")

@app.route("/users/restaurant", methods=["POST"])
def signup_restaurant():
    try:
        print("Restaurant signup started")

        # Collect form data
        user_name = request.form.get("user_name")
        user_email = request.form.get("user_email")
        user_password = request.form.get("user_password")
        restaurant_name = request.form.get("restaurant_name")
        restaurant_address = request.form.get("restaurant_address")
        restaurant_city = request.form.get("restaurant_city")
        restaurant_postal = request.form.get("restaurant_postal")
        restaurant_phone = request.form.get("restaurant_phone")
        print(f"Form data: {user_name}, {user_email}, {restaurant_name}")

        # Validate input
        if not all([
            user_name, user_email, user_password,
            restaurant_name, restaurant_address, restaurant_city, restaurant_postal, restaurant_phone
        ]):
            print("Validation failed: Missing fields")
            return """<template mix-target="#toast">All fields are required</template>""", 400

        # Generate UUIDs and timestamps
        user_pk = str(uuid.uuid4())
        restaurant_pk = str(uuid.uuid4())
        verification_key = str(uuid.uuid4())
        current_time = int(time.time())
        print(f"Generated user_pk: {user_pk}, restaurant_pk: {restaurant_pk}, verification_key: {verification_key}")

        # Establish database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        print("Database connection established")

        # Check if the email is already registered
        cursor.execute("SELECT user_pk FROM users WHERE user_email = %s", (user_email,))
        if cursor.fetchone():
            print("Email already registered")
            return """<template mix-target="#toast">Email already registered</template>""", 400

        # Hash the password
        hashed_password = generate_password_hash(user_password)
        print("Password hashed")

        # Insert user into `users` table
        user = {
            "user_pk": user_pk,
            "user_name": user_name,
            "user_last_name": restaurant_name,  # Optional if owner name is used
            "user_email": user_email,
            "user_password": hashed_password,
            "user_avatar": "",
            "user_created_at": current_time,
            "user_deleted_at": 0,
            "user_blocked_at": 0,
            "user_updated_at": 0,
            "user_verified_at": 0,
            "user_verification_key": verification_key
        }
        cursor.execute("""
            INSERT INTO users (
                user_pk, user_name, user_last_name, user_email,
                user_password, user_avatar, user_created_at,
                user_deleted_at, user_blocked_at, user_updated_at,
                user_verified_at, user_verification_key
            ) VALUES (
                %(user_pk)s, %(user_name)s, %(user_last_name)s, %(user_email)s,
                %(user_password)s, %(user_avatar)s, %(user_created_at)s,
                %(user_deleted_at)s, %(user_blocked_at)s, %(user_updated_at)s,
                %(user_verified_at)s, %(user_verification_key)s
            )
        """, user)
        print("User inserted into the database")

        # Assign role to the user
        cursor.execute("""
            INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
            VALUES (%s, %s)
        """, (user_pk, RESTAURANT_ROLE_PK))
        print("Role assigned to user")

        # Insert restaurant into `restaurant_details`
        restaurant = {
            "restaurant_pk": restaurant_pk,
            "restaurant_user_fk": user_pk,
            "restaurant_name": restaurant_name,
            "restaurant_address": restaurant_address,
            "restaurant_city": restaurant_city,
            "restaurant_postal": restaurant_postal,
            "restaurant_phone": restaurant_phone,
            "restaurant_created_at": current_time
        }
        cursor.execute("""
            INSERT INTO restaurant_details (
                restaurant_pk, restaurant_user_fk, restaurant_name,
                restaurant_address, restaurant_city, restaurant_postal,
                restaurant_phone, restaurant_created_at
            ) VALUES (
                %(restaurant_pk)s, %(restaurant_user_fk)s, %(restaurant_name)s,
                %(restaurant_address)s, %(restaurant_city)s, %(restaurant_postal)s,
                %(restaurant_phone)s, %(restaurant_created_at)s
            )
        """, restaurant)
        print("Restaurant inserted into the database")

        # Send verification email
        if not send_verify_email(user_email, verification_key):
            print("send_verify_email failed, rolling back database changes")
            db.rollback()
            return """<template mix-target="#toast">Email verification failed</template>""", 500

        # Commit the transaction
        db.commit()
        print("Signup successful, transaction committed")

        # Success response
        return render_template("login.html", message="Please check your email to verify your account.")

    except Exception as ex:
        import traceback
        print(f"Signup error: {str(ex)}")
        traceback.print_exc()
        if "db" in locals(): db.rollback()
        return """<template mix-target="#toast">System under maintenance</template>""", 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

        
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                return render_template("login.html", error="Please fill in all fields")

            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            # Debugging: Log email being checked
            print("[DEBUG] Fetching user details for email:", email)

            # Adjusted query to match database schema and ensure proper field checks
            cursor.execute("""
                SELECT u.user_pk, u.user_name, u.user_last_name, u.user_email, u.user_password, 
                       u.user_verified_at, u.user_deleted_at, u.user_blocked_at, r.role_name
                FROM users u
                JOIN users_roles ur ON u.user_pk = ur.user_role_user_fk
                JOIN roles r ON ur.user_role_role_fk = r.role_pk
                WHERE u.user_email = %s AND (u.user_deleted_at IS NULL OR u.user_deleted_at = 0) 
                      AND (u.user_blocked_at IS NULL OR u.user_blocked_at = 0)
            """, (email,))

            user_data = cursor.fetchall()
            print("[DEBUG] User data fetched:", user_data)

            if not user_data:
                print("[ERROR] No user found or user is blocked/deleted:", email)
                return render_template("login.html", error="Invalid email or password")

            # Check if user_verified_at is NULL
            if user_data[0]['user_verified_at'] is None:
                print("[ERROR] Email not verified for user:", email)
                return render_template("login.html", error="Please verify your email first")

            # Check password
            if not check_password_hash(user_data[0]['user_password'], password):
                print("[ERROR] Password mismatch for email:", email)
                return render_template("login.html", error="Invalid email or password")

            # Fetch roles
            roles = {row['role_name'] for row in user_data}
            print("[DEBUG] Roles fetched for user:", roles)

            # Save session
            session['user'] = {
                'user_pk': user_data[0]['user_pk'],
                'user_name': user_data[0]['user_name'],
                'roles': list(roles),
                'user_email': user_data[0]['user_email']
            }
            print("[DEBUG] Session created for user:", session['user'])

            # Redirect based on role
            if 'restaurant' in roles:
                print("[DEBUG] Redirecting to restaurant dashboard")
                return redirect(url_for('restaurant_dashboard'))
            if 'admin' in roles:
                print("[DEBUG] Redirecting to admin dashboard")
                return redirect(url_for('admin_dashboard'))
            elif 'delivery' in roles:
                print("[DEBUG] Redirecting to delivery dashboard")
                return redirect(url_for('delivery_dashboard'))
            else:
                print("[DEBUG] Redirecting to general dashboard")
                return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"[ERROR] Login exception: {e}")
        import traceback
        traceback.print_exc()
        return render_template("login.html", error="System under maintenance"), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

    return render_template("login.html")


@app.route('/restaurant/dashboard', methods=['GET'])
def restaurant_dashboard():
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        return redirect(url_for('login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get restaurant details
        cursor.execute("""
            SELECT rd.*, u.user_email 
            FROM restaurant_details rd
            JOIN users u ON rd.restaurant_user_fk = u.user_pk
            WHERE rd.restaurant_user_fk = %s
        """, (session['user']['user_pk'],))
        restaurant = cursor.fetchone()
        
        if not restaurant:
            print("Error: Restaurant not found for user")
            return render_template("error.html", error="Restaurant not found"), 404
        
        print("Restaurant Details:", restaurant)
        
        # Get recent orders with items and customer details
        cursor.execute("""
            SELECT o.*, u.user_name, u.user_last_name,
                   GROUP_CONCAT(CONCAT(IFNULL(i.item_name, 'Unknown Item'), ' x', IFNULL(oi.order_item_quantity, 0))) as order_items
            FROM orders o
            JOIN users u ON o.order_user_fk = u.user_pk
            JOIN order_items oi ON o.order_pk = oi.order_item_order_fk
            JOIN items i ON oi.order_item_item_fk = i.item_pk
            WHERE o.order_restaurant_fk = %s
            GROUP BY o.order_pk
            ORDER BY o.order_created_at DESC
        """, (restaurant['restaurant_pk'],))
        orders = cursor.fetchall()
        
        if not orders:
            print("No orders found for restaurant.")
        
        for order in orders:
            order['formatted_date'] = datetime.fromtimestamp(
                order.get('order_created_at', 0)
            ).strftime('%B %d, %Y %H:%M')
            order['items_list'] = order['order_items'].split(',') if order['order_items'] else []
        
        print("Orders Debug:", orders)

        # Fetch menu items for the restaurant
        cursor.execute("""
            SELECT i.*, GROUP_CONCAT(im.image_url) as item_images
            FROM items i
            LEFT JOIN item_images im ON i.item_pk = im.image_item_fk
            WHERE i.item_restaurant_fk = %s
            AND (i.item_deleted_at IS NULL OR i.item_deleted_at = 0)
            GROUP BY i.item_pk
        """, (restaurant['restaurant_pk'],))
        menu_items = cursor.fetchall()
        
        if not menu_items:
            print("No menu items found for restaurant.")
        
        print("Menu Items Debug:", menu_items)

        # Render template with restaurant details, orders, and menu items
        return render_template('restaurant/dashboard.html', 
                               restaurant=restaurant, 
                               orders=orders,
                               menu_items=menu_items,
                               user=session['user'])

    except Exception as e:
        import traceback
        print(f"Error loading dashboard: {e}")
        traceback.print_exc()  # Log the full error traceback for debugging
        return render_template("error.html", error="Failed to load dashboard"), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

@app.route('/api/restaurant/orders/<string:order_pk>/status', methods=['POST'])
def update_restaurant_order_status(order_pk):
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get the new status from the form
        new_status = request.form.get('status').strip()
        allowed_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivering', 'delivered', 'cancelled']

        if new_status not in allowed_statuses:
            return jsonify({"error": f"Invalid status: {new_status}"}), 400

        print(f"Updating order status: Order PK = {order_pk}, New Status = '{new_status}'")

        db = get_db_connection()
        cursor = db.cursor()

        # Update the order status
        cursor.execute("""
            UPDATE orders
            SET order_status = %s, order_updated_at = %s
            WHERE order_pk = %s
            AND order_restaurant_fk = (
                SELECT restaurant_pk FROM restaurant_details 
                WHERE restaurant_user_fk = %s
            )
        """, (new_status, int(time.time()), order_pk, session['user']['user_pk']))

        if cursor.rowcount == 0:
            return jsonify({"error": "Order not found or unauthorized"}), 404

        db.commit()
        print("Order status updated successfully.")
        return jsonify({"success": True, "order_pk": order_pk, "new_status": new_status}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An error occurred while updating order status"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()


@app.route('/restaurant/menu/add', methods=['GET', 'POST'])
def add_menu_item():
    print("Starting add_menu_item route") # Debug
    
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        print("User not authenticated or not a restaurant") # Debug
        return redirect(url_for('login'))
    
    try:
        if request.method == 'POST':
            print("Processing POST request") # Debug
            print("Form data:", request.form) # Debug
            print("Files:", request.files) # Debug
            
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            
            print("User PK:", session['user']['user_pk']) # Debug
            
            # Get restaurant details
            cursor.execute("""
                SELECT restaurant_pk FROM restaurant_details 
                WHERE restaurant_user_fk = %s
            """, (session['user']['user_pk'],))
            restaurant = cursor.fetchone()
            print("Restaurant details:", restaurant) # Debug
            
            if not restaurant:
                print("No restaurant found for user") # Debug
                return render_template("restaurant/menu_add.html", error="Restaurant not found")
            
            # Get form data
            item_name = request.form.get('item_name')
            item_description = request.form.get('item_description')
            item_price = request.form.get('item_price')
            item_category = request.form.get('item_category')
            
            print("Form data extracted:", { # Debug
                "name": item_name,
                "description": item_description,
                "price": item_price,
                "category": item_category
            })
            
            # Validate input
            if not all([item_name, item_description, item_price]):
                print("Missing required fields") # Debug
                return render_template("restaurant/menu_add.html", error="All fields are required")
            
            try:
                # Convert price to float and validate
                price = float(item_price)
                if price <= 0:
                    print("Invalid price value:", price) # Debug
                    return render_template("restaurant/menu_add.html", error="Price must be greater than 0")
            except ValueError:
                print("Price conversion error") # Debug
                return render_template("restaurant/menu_add.html", error="Invalid price format")
            
            # Create new menu item
            item_pk = str(uuid.uuid4())
            current_time = int(time.time())
            
            print("Inserting new item:", { # Debug
                "pk": item_pk,
                "restaurant_pk": restaurant['restaurant_pk'],
                "current_time": current_time
            })
            
            try:
                cursor.execute("""
                    INSERT INTO items (
                        item_pk, item_restaurant_fk, item_name, 
                        item_description, item_price, item_category,
                        item_created_at, item_updated_at, item_deleted_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item_pk, 
                    restaurant['restaurant_pk'],
                    item_name,
                    item_description,
                    price,
                    item_category,
                    current_time,
                    current_time,
                    0
                ))
                print("Item inserted successfully") # Debug
            except Exception as e:
                print("Error inserting item:", str(e)) # Debug
                raise
            
            # Handle image upload
            if 'item_image' in request.files:
                file = request.files['item_image']
                print("Processing image file:", file.filename if file else "No filename") # Debug
                
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        print("File path:", file_path) # Debug
                        
                        try:
                            # Ensure uploads directory exists
                            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                            
                            file.save(file_path)
                            print("File saved successfully") # Debug
                            
                            # Save image reference in database
                            image_pk = str(uuid.uuid4())
                            cursor.execute("""
                                INSERT INTO item_images (
                                    image_pk, image_item_fk, image_url, image_order
                                ) VALUES (%s, %s, %s, %s)
                            """, (image_pk, item_pk, filename, 1))
                            print("Image reference saved to database") # Debug
                        except Exception as e:
                            print("Error handling file:", str(e)) # Debug
                            raise
                    else:
                        print("Invalid file type") # Debug
                        return render_template("restaurant/menu_add.html", 
                                            error="Invalid file type. Allowed types are: png, jpg, jpeg, gif")
            
            db.commit()
            print("Transaction committed successfully") # Debug
            
            # After successful addition, redirect to profile
            return redirect(url_for('restaurant_profile'))

        # GET request - show the form
        print("Handling GET request") # Debug
        return render_template("restaurant/menu_add.html", 
                            user=session['user'])

    except Exception as e:
        print(f"Error adding menu item: {str(e)}") # Debug
        print("Full traceback:") # Debug
        import traceback
        traceback.print_exc()
        if 'db' in locals(): 
            db.rollback()
        return render_template("restaurant/menu_add.html", 
                            error="Failed to add menu item: " + str(e),
                            user=session['user']), 500
    finally:
        if 'cursor' in locals(): 
            cursor.close()
        if 'db' in locals(): 
            db.close()
        print("Database connections closed") # Debug
@app.route('/restaurant/menu', methods=['GET'])
def restaurant_menu():
    """
    Displays the restaurant's menu.
    """
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        return redirect(url_for('login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch restaurant details
        cursor.execute("""
            SELECT rd.*, u.user_email 
            FROM restaurant_details rd
            JOIN users u ON rd.restaurant_user_fk = u.user_pk
            WHERE rd.restaurant_user_fk = %s
        """, (session['user']['user_pk'],))
        restaurant = cursor.fetchone()

        if not restaurant:
            return render_template("error.html", error="Restaurant not found"), 404

        # Fetch menu items for the logged-in restaurant
        cursor.execute("""
            SELECT 
                i.item_pk,
                i.item_name,
                i.item_description,
                i.item_price,
                i.item_category,
                i.item_available,
                GROUP_CONCAT(im.image_url) AS item_images
            FROM items i
            LEFT JOIN item_images im ON i.item_pk = im.image_item_fk
            WHERE i.item_restaurant_fk = %s
            AND (i.item_deleted_at IS NULL OR i.item_deleted_at = 0)
            GROUP BY i.item_pk
        """, (restaurant['restaurant_pk'],))
        menu_items = cursor.fetchall()

        return render_template(
            'restaurant/restaurant_menu.html',
            restaurant=restaurant,
            menu_items=menu_items
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", error="An error occurred while fetching the menu."), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()
@app.route('/place-order', methods=['POST'])
def place_order():
    # Ensure user is logged in
    if 'user' not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Retrieve form data
        selected_address = request.form.get('selected_address')  # Optional saved address
        new_address_line_1 = request.form.get('new_address_line_1')
        new_address_line_2 = request.form.get('new_address_line_2')
        new_city = request.form.get('new_city')
        new_state = request.form.get('new_state')
        new_zip_code = request.form.get('new_zip_code')
        phone_number = request.form.get('phonenumber')
        order_notes = request.form.get('order_notes')
        cart_data = session.get('cart', {})

        if not cart_data:
            return jsonify({"success": False, "message": "Cart is empty"}), 400

        # Determine the address to use
        if selected_address:
            cursor.execute("""
                SELECT address_line_1, address_line_2, city, state, zip_code, phone
                FROM user_addresses
                WHERE address_pk = %s
            """, (selected_address,))
            saved_address = cursor.fetchone()

            if not saved_address:
                return jsonify({"success": False, "message": "Invalid saved address"}), 400

            order_address = saved_address['address_line_1']
            order_address_2 = saved_address['address_line_2']
            order_city = saved_address['city']
            order_state = saved_address['state']
            order_zip = saved_address['zip_code']
            order_phone = saved_address['phone']
        else:
            if not (new_address_line_1 and new_city and new_state and new_zip_code and phone_number):
                return jsonify({"success": False, "message": "Incomplete address details"}), 400

            order_address = new_address_line_1
            order_address_2 = new_address_line_2
            order_city = new_city
            order_state = new_state
            order_zip = new_zip_code
            order_phone = phone_number

        # Insert order into orders table
        order_pk = str(uuid.uuid4())
        subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart_data.values())
        delivery_fee = 29.00
        total_price = subtotal + delivery_fee
        current_time = int(time.time())

        cursor.execute("""
            INSERT INTO orders (
                order_pk, order_user_fk, order_restaurant_fk, order_status,
                order_total, order_delivery_fee, order_address, order_city,
                order_postal_code, order_phone, order_notes, order_created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            order_pk,
            session['user']['user_pk'],
            list(cart_data.values())[0]['restaurantId'],
            'pending',
            total_price,
            delivery_fee,
            order_address,
            order_city,
            order_zip,
            order_phone,
            order_notes,
            current_time
        ))

        # Insert items into order_items table
        for item_id, item in cart_data.items():
            cursor.execute("""
                INSERT INTO order_items (order_item_order_fk, order_item_item_fk, order_item_quantity, order_item_price)
                VALUES (%s, %s, %s, %s)
            """, (
                order_pk,
                item_id,
                item['quantity'],
                item['price']
            ))

        db.commit()

        # Prepare order details for the email
        order_details = {
            "items": [
                {
                    "name": item['name'],
                    "quantity": item['quantity'],
                    "subtotal": float(item['price']) * int(item['quantity']),
                }
                for item in cart_data.values()
            ],
            "delivery_fee": delivery_fee,
            "total_price": total_price
        }

        # Send order confirmation email
        customer_name = session['user']['user_name']
        customer_email = session['user']['user_email']
        if not send_order_confirmation_email(customer_email, order_details, customer_name):
            print("Failed to send order confirmation email")

        # Clear the cart from the session
        session.pop('cart', None)

        # Redirect the user to the order complete page
        return jsonify({"success": True, "redirect_url": url_for('order_complete')}), 200

    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error placing order: {e}")
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return jsonify({"success": False, "message": "Failed to place order"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()
def send_order_confirmation_email(email, order_details, customer_name):
    try:
        # Create the email message
        message = MIMEMultipart()
        message["From"] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message["To"] = email
        message["Subject"] = "Order Confirmation - Thank You for Your Order!"

        # Generate the order details as HTML
        order_items_html = "".join(
            f"<li>{item['quantity']} x {item['name']} - ${item['subtotal']:.2f}</li>"
            for item in order_details['items']
        )

        # Email body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Order Confirmation</h2>
                    <p>Hi {customer_name},</p>
                    <p>Thank you for your order! Here are the details of your order:</p>
                    <ul>
                        {order_items_html}
                    </ul>
                    <p><strong>Delivery Fee:</strong> ${order_details['delivery_fee']:.2f}</p>
                    <p><strong>Total:</strong> ${order_details['total_price']:.2f}</p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #666; font-size: 14px;">
                        If you have any questions about your order, feel free to contact us.
                    </p>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Connect to SMTP server and send email
        print("Connecting to SMTP server...")
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            print("Starting TLS...")
            server.starttls()
            print("Logging in...")
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['APP_PASSWORD'])
            print("Sending email...")
            server.send_message(message)

        print("Order confirmation email sent successfully!")
        return True

    except Exception as ex:
        import traceback
        print(f"Error sending order confirmation email: {str(ex)}")
        traceback.print_exc()
        return False

@app.route('/restaurant/menu/update', methods=['POST'])
def update_menu_item():
    """
    Updates a menu item.
    """
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        return {"error": "Unauthorized"}, 401

    try:
        item_pk = request.form.get('item_pk')
        item_name = request.form.get('item_name')
        item_description = request.form.get('item_description')
        item_price = request.form.get('item_price')
        item_available = request.form.get('item_available')

        db = get_db_connection()
        cursor = db.cursor()

        # Update menu item
        cursor.execute("""
            UPDATE items
            SET item_name = %s, item_description = %s, item_price = %s, item_available = %s, item_updated_at = %s
            WHERE item_pk = %s
            AND item_restaurant_fk = (
                SELECT restaurant_pk 
                FROM restaurant_details 
                WHERE restaurant_user_fk = %s
            )
        """, (item_name, item_description, item_price, item_available, int(time.time()), item_pk, session['user']['user_pk']))

        db.commit()
        if cursor.rowcount == 0:
            return {"error": "Item not found or unauthorized"}, 404

        return {"success": True}, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": "An error occurred while updating the item"}, 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()
@app.route('/restaurant/menu/edit', methods=['POST'])
def edit_menu_item():
    """
    Updates menu item details, including name, description, price, and images.
    """
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        return {"error": "Unauthorized"}, 401

    try:
        # Retrieve form data
        item_pk = request.form.get('item_pk')
        item_name = request.form.get('item_name')
        item_description = request.form.get('item_description')
        item_price = request.form.get('item_price')
        uploaded_files = request.files.getlist('item_images')

        # Validate data
        if not all([item_pk, item_name, item_description, item_price]):
            return render_template("error.html", error="All fields are required"), 400

        # Process uploaded files
        image_paths = []
        upload_folder = os.path.join(app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)

        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                image_paths.append(filename)

        db = get_db_connection()
        cursor = db.cursor()

        # Update item details in the database
        cursor.execute("""
            UPDATE items
            SET item_name = %s, item_description = %s, item_price = %s, item_updated_at = %s
            WHERE item_pk = %s
            AND item_restaurant_fk = (
                SELECT restaurant_pk 
                FROM restaurant_details 
                WHERE restaurant_user_fk = %s
            )
        """, (item_name, item_description, item_price, int(time.time()), item_pk, session['user']['user_pk']))

        # Update item images
        if image_paths:
            cursor.execute("DELETE FROM item_images WHERE image_item_fk = %s", (item_pk,))
            for index, path in enumerate(image_paths[:3]):  # Limit to 3 images
                cursor.execute("""
                    INSERT INTO item_images (image_pk, image_item_fk, image_url, image_order)
                    VALUES (%s, %s, %s, %s)
                """, (str(uuid.uuid4()), item_pk, path, index + 1))

        db.commit()
        return redirect(url_for('restaurant_menu'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", error="An error occurred while updating the menu item"), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

@app.route('/restaurant/menu/delete', methods=['POST'])
def delete_menu_item():
    """
    Deletes a menu item by setting its deleted_at field and re-renders the current page.
    """
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        return {"error": "Unauthorized"}, 401

    try:
        item_pk = request.form.get('item_pk')

        db = get_db_connection()
        cursor = db.cursor()

        # Soft delete the menu item
        cursor.execute("""
            UPDATE items
            SET item_deleted_at = %s
            WHERE item_pk = %s
            AND item_restaurant_fk = (
                SELECT restaurant_pk 
                FROM restaurant_details 
                WHERE restaurant_user_fk = %s
            )
        """, (int(time.time()), item_pk, session['user']['user_pk']))

        db.commit()
        if cursor.rowcount == 0:
            return {"error": "Item not found or unauthorized"}, 404

        # Redirect back to the restaurant menu page
        return redirect(url_for('restaurant_menu'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template(
            "error.html", error="An error occurred while deleting the item"
        ), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()



@app.route('/restaurant/profile', methods=['GET', 'POST'])
def restaurant_profile():
    print("Starting restaurant_profile route") # Debug
    
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        print("User not authenticated or not a restaurant") # Debug
        return redirect(url_for('login'))
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        print("User PK:", session['user']['user_pk']) # Debug
        
        # Get restaurant details
        cursor.execute("""
            SELECT rd.*, u.user_email 
            FROM restaurant_details rd
            JOIN users u ON rd.restaurant_user_fk = u.user_pk
            WHERE rd.restaurant_user_fk = %s
        """, (session['user']['user_pk'],))
        restaurant = cursor.fetchone()
        print("Restaurant details:", restaurant) # Debug
        
        # Get restaurant menu items
        cursor.execute("""
            SELECT i.*, GROUP_CONCAT(im.image_url) as item_images
            FROM items i
            LEFT JOIN item_images im ON i.item_pk = im.image_item_fk
            WHERE i.item_restaurant_fk = %s
            AND (i.item_deleted_at IS NULL OR i.item_deleted_at = 0)
            GROUP BY i.item_pk
        """, (restaurant['restaurant_pk'],))
        menu_items = cursor.fetchall()
        print("Menu items:", menu_items) # Debug

        return render_template(
            "restaurant/profile.html",
            user=session['user'],
            restaurant=restaurant,
            menu_items=menu_items
        )

    except Exception as e:
        print(f"Error in restaurant profile: {str(e)}") # Debug
        print("Full traceback:") # Debug
        import traceback
        traceback.print_exc()
        if 'db' in locals(): db.rollback()
        return render_template("error.html", error="Failed to load profile"), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()
        print("Database connections closed") # Debug



from flask import jsonify  # Add this import at the top
@app.route('/api/get-cart', methods=['GET'])
def get_cart():
    """
    Returns the user's cart stored in the session.
    If no cart exists, an empty object is returned.
    """
    try:
        # Retrieve the cart from the session
        cart = session.get('cart', {})
        print(f"[DEBUG] Retrieved cart: {cart}")  # Debugging
        return jsonify(cart), 200
    except Exception as e:
        print(f"[ERROR] Failed to retrieve cart: {e}")
        return jsonify({"error": "Failed to retrieve cart"}), 500

@app.route('/api/save-cart', methods=['POST'])
def save_cart():
    cart_data = request.json
    session['cart'] = cart_data
    session.modified = True
    return jsonify(success=True)

@app.route('/api/menu/<restaurant_pk>', methods=['GET'])
def get_menu(restaurant_pk):
    """
    Fetches the menu items for a specific restaurant and includes proper image paths.
    """
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                i.item_pk,
                i.item_name,
                i.item_description,
                i.item_price,
                i.item_category,
                i.item_available,
                GROUP_CONCAT(im.image_url) AS item_images
            FROM items i
            LEFT JOIN item_images im ON i.item_pk = im.image_item_fk
            WHERE i.item_restaurant_fk = %s
            AND (i.item_deleted_at IS NULL OR i.item_deleted_at = 0)
            GROUP BY i.item_pk
        """, (restaurant_pk,))
        
        menu_items = cursor.fetchall()

        # Process image paths
        for item in menu_items:
            if item['item_images']:
                item['item_images'] = [
                    f"/static/uploads/{img}" for img in item['item_images'].split(',')
                ]
            else:
                item['item_images'] = ["/static/images/default-placeholder.png"]

        return jsonify({"menu_items": menu_items})

    except Exception as e:
        print("Error fetching menu:", e)
        return jsonify({"error": "Failed to fetch menu items"}), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()
        
    # Ensure user is logged in
    if 'user' not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Retrieve form data
        selected_address = request.form.get('selected_address')  # Optional saved address
        new_address_line_1 = request.form.get('new_address_line_1')
        new_address_line_2 = request.form.get('new_address_line_2')
        new_city = request.form.get('new_city')
        new_state = request.form.get('new_state')
        new_zip_code = request.form.get('new_zip_code')
        phone_number = request.form.get('phonenumber')
        order_notes = request.form.get('order_notes')
        cart_data = session.get('cart', {})

        if not cart_data:
            return jsonify({"success": False, "message": "Cart is empty"}), 400

        # Determine the address to use
        if selected_address:
            cursor.execute("""
                SELECT address_line_1, address_line_2, city, state, zip_code, phone
                FROM user_addresses
                WHERE address_pk = %s
            """, (selected_address,))
            saved_address = cursor.fetchone()

            if not saved_address:
                return jsonify({"success": False, "message": "Invalid saved address"}), 400

            order_address = saved_address['address_line_1']
            order_address_2 = saved_address['address_line_2']
            order_city = saved_address['city']
            order_state = saved_address['state']
            order_zip = saved_address['zip_code']
            order_phone = saved_address['phone']
        else:
            if not (new_address_line_1 and new_city and new_state and new_zip_code and phone_number):
                return jsonify({"success": False, "message": "Incomplete address details"}), 400

            order_address = new_address_line_1
            order_address_2 = new_address_line_2
            order_city = new_city
            order_state = new_state
            order_zip = new_zip_code
            order_phone = phone_number

        # Insert order into orders table
        order_pk = str(uuid.uuid4())
        subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart_data.values())
        delivery_fee = 29.00
        total_price = subtotal + delivery_fee
        current_time = int(time.time())

        cursor.execute("""
            INSERT INTO orders (
                order_pk, order_user_fk, order_restaurant_fk, order_status,
                order_total, order_delivery_fee, order_address, order_city,
                order_postal_code, order_phone, order_notes, order_created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            order_pk,
            session['user']['user_pk'],
            list(cart_data.values())[0]['restaurantId'],
            'pending',
            total_price,
            delivery_fee,
            order_address,
            order_city,
            order_zip,
            order_phone,
            order_notes,
            current_time
        ))

        # Insert items into order_items table
        for item_id, item in cart_data.items():
            cursor.execute("""
                INSERT INTO order_items (order_item_order_fk, order_item_item_fk, order_item_quantity, order_item_price)
                VALUES (%s, %s, %s, %s)
            """, (
                order_pk,
                item_id,
                item['quantity'],
                item['price']
            ))

        db.commit()

        # Clear the cart from the session
        session.pop('cart', None)

        # Redirect the user to the order complete page
        return jsonify({"success": True, "redirect_url": url_for('order_complete')}), 200

    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error placing order: {e}")
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return jsonify({"success": False, "message": "Failed to place order"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user = session['user']
        user_roles = user.get('roles', [])
        print("User roles:", user_roles)  # Debug print
        
        if 'customer' in user_roles:
            try:
                db = get_db_connection()
                cursor = db.cursor(dictionary=True)
                
                cursor.execute("SELECT COUNT(*) as count FROM restaurant_details")
                count = cursor.fetchone()
                print("Total restaurants in DB:", count['count'])  # Debug print

                cursor.execute("""
                    SELECT restaurant_pk, restaurant_name, restaurant_address, restaurant_rating, restaurant_rating_count
                    FROM restaurant_details
                """)
                restaurants = cursor.fetchall()
                print("Fetched restaurants:", restaurants)  # Debug print
                
                return render_template("customer/dashboard.html", user=user, restaurants=restaurants)
            except Exception as db_error:
                print("Database error:", str(db_error))  # Debug print
                return render_template("customer/dashboard.html", user=user)
            finally:
                if cursor: cursor.close()
                if db: db.close()
        
        elif 'restaurant' in user_roles:
            template = "restaurant/dashboard.html"
        elif 'admin' in user_roles:
            template = "admin/dashboard.html"
        elif 'delivery' in user_roles:
            template = "delivery_dashboard.html"
        else:
            return render_template("error.html", error="Unauthorized access")
        
        return render_template(template, user=user)
    
    except Exception as e:
        print("General error:", str(e))  # Debug print
        return render_template("error.html", error=str(e))

import traceback

@app.route('/delivery/dashboard', methods=['GET'])
def delivery_dashboard():
    if 'user' not in session or 'delivery' not in session['user']['roles']:
        return redirect(url_for('login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get the delivery user details
        cursor.execute("""
            SELECT u.user_name, u.user_last_name, u.user_email
            FROM users u
            WHERE u.user_pk = %s
        """, (session['user']['user_pk'],))
        user_details = cursor.fetchone()

        if not user_details:
            return render_template("error.html", error="Delivery user not found"), 404

        # Fetch orders where 'order_delivery_user_fk' is NULL (available)
        cursor.execute("""
            SELECT o.order_pk, o.order_status, o.order_delivery_user_fk, 
                   o.order_created_at, o.order_total, u.user_name as customer_name,
                   u.user_email as customer_email,
                   GROUP_CONCAT(CONCAT(i.item_name, ' x', oi.order_item_quantity) SEPARATOR ', ') as order_items
            FROM orders o
            JOIN users u ON o.order_user_fk = u.user_pk
            LEFT JOIN order_items oi ON o.order_pk = oi.order_item_order_fk
            LEFT JOIN items i ON oi.order_item_item_fk = i.item_pk
            WHERE o.order_delivery_user_fk IS NULL AND o.order_status != 'completed'
            GROUP BY o.order_pk
            ORDER BY o.order_created_at DESC
        """)
        orders = cursor.fetchall()

        if not orders:
            print("[DEBUG] No available orders found.")
        
        for order in orders:
            order['formatted_date'] = datetime.fromtimestamp(order['order_created_at']).strftime('%B %d, %Y %H:%M')

        # Render template with orders and user details
        return render_template('delivery/dashboard.html', 
                               user=user_details, 
                               orders=orders)

    except Exception as e:
        print(f"[ERROR] Error fetching orders: {e}")
        traceback.print_exc()  # Print the full traceback for detailed error information
        return render_template("error.html", error="Failed to load dashboard"), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

import uuid

@app.route('/delivery/take_order/<uuid:order_id>', methods=['POST'])
def take_order(order_id):
    try:
        # Check if the user has the delivery role
        if 'user' not in session or 'delivery' not in session['user']['roles']:
            return redirect(url_for('login'))

        # Convert the UUID to string (MySQL expects UUID as a string)
        order_id_str = str(order_id)
        user_pk_str = str(session['user']['user_pk'])  # Ensure the user PK is a string

        # Connect to the database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Update the order to assign the delivery user
        cursor.execute("""
            UPDATE orders
            SET order_delivery_user_fk = %s, order_status = 'delivering'
            WHERE order_pk = %s AND order_delivery_user_fk IS NULL
        """, (user_pk_str, order_id_str))

        # Commit the changes
        db.commit()

        # Check if any rows were updated (if no rows were updated, the order was already taken)
        if cursor.rowcount == 0:
            flash("This order has already been taken or completed.", "error")
            return redirect(url_for('delivery_dashboard'))

        # Flash success message and redirect to the dashboard
        flash("Order successfully assigned to you!", "success")
        return redirect(url_for('delivery_dashboard'))

    except Exception as e:
        print(f"[ERROR] Error taking order: {e}")
        traceback.print_exc()  # Log the full traceback for detailed error information
        return render_template("error.html", error="Failed to take order"), 500

    finally:
        # Ensure resources are cleaned up
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()


@app.route('/delivery/my_orders', methods=['GET'])
def my_orders():
    try:
        # Ensure the user is logged in and has the 'delivery' role
        if 'user' not in session or 'delivery' not in session['user']['roles']:
            return redirect(url_for('login'))

        # Get the user from the session
        user = session['user']

        # Connect to the database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get orders assigned to the logged-in delivery user (where order_delivery_user_fk is not NULL)
        cursor.execute("""
            SELECT o.*, u.user_name, u.user_last_name, 
                   GROUP_CONCAT(CONCAT(IFNULL(i.item_name, 'Unknown Item'), ' x', IFNULL(oi.order_item_quantity, 0))) as order_items
            FROM orders o
            JOIN users u ON o.order_delivery_user_fk = u.user_pk
            LEFT JOIN order_items oi ON o.order_pk = oi.order_item_order_fk
            LEFT JOIN items i ON oi.order_item_item_fk = i.item_pk
            WHERE o.order_delivery_user_fk = %s
            GROUP BY o.order_pk
            ORDER BY o.order_created_at DESC
        """, (session['user']['user_pk'],))

        orders = cursor.fetchall()

        # Format the date for each order
        for order in orders:
            order['formatted_date'] = datetime.fromtimestamp(
                order.get('order_created_at', 0)
            ).strftime('%B %d, %Y %H:%M')
            order['items_list'] = order['order_items'].split(',') if order['order_items'] else []

        # Render the 'my_orders' page and pass the orders data along with the user data
        return render_template('delivery/my_orders.html', orders=orders, user=user)

    except Exception as e:
        print(f"[ERROR] Error fetching my orders: {e}")
        traceback.print_exc()  # Log the full traceback for debugging
        return render_template("error.html", error="Failed to load orders"), 500

    finally:
        # Ensure resources are cleaned up
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

@app.route('/delivery/profile', methods=['GET', 'POST'])
def delivery_profile():
    if 'user' not in session or 'delivery' not in session['user']['roles']:
        return redirect(url_for('login'))
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Fetch the delivery user's profile data
        cursor.execute("""
            SELECT u.user_name, u.user_last_name, u.user_email
            FROM users u
            WHERE u.user_pk = %s
        """, (session['user']['user_pk'],))
        user_details = cursor.fetchone()

        if not user_details:
            return render_template("error.html", error="User not found"), 404

        if request.method == 'POST':
            new_name = request.form.get('user_name')
            new_last_name = request.form.get('user_last_name')
            new_email = request.form.get('user_email')
            new_password = request.form.get('user_password')

            # Validate and update details
            if new_name and new_last_name and new_email:
                # Update name and email
                cursor.execute("""
                    UPDATE users
                    SET user_name = %s, user_last_name = %s, user_email = %s
                    WHERE user_pk = %s
                """, (new_name, new_last_name, new_email, session['user']['user_pk']))
                
                if new_password:
                    # Hash password and update if changed
                    hashed_password = generate_password_hash(new_password)
                    cursor.execute("""
                        UPDATE users
                        SET user_password = %s
                        WHERE user_pk = %s
                    """, (hashed_password, session['user']['user_pk']))

                db.commit()
                flash("Profile updated successfully", "success")
                return redirect(url_for('delivery_profile'))

            flash("Please fill out all fields correctly", "error")
        
        return render_template("delivery/profile.html", user=user_details)
    
    except Exception as e:
        print(f"[ERROR] Error updating profile: {e}")
        return render_template("error.html", error="Failed to update profile"), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('view_index'))
@app.route('/verify/<verification_key>', methods=['GET'])
def verify(verification_key):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch the user by verification key
        cursor.execute("""
            SELECT * FROM users WHERE user_verification_key = %s
        """, (verification_key,))
        user = cursor.fetchone()
        if not user:
            return render_template("verify.html", error="Invalid or expired verification link.")

        # Update the user_verified_at field to the current timestamp and clear verification key
        print("[DEBUG] Updating user_verified_at for user:", verification_key)
        cursor.execute("""
            UPDATE users
            SET user_verified_at = UNIX_TIMESTAMP(), user_verification_key = NULL
            WHERE user_verification_key = %s
        """, (verification_key,))
        db.commit()
        print("[DEBUG] User verified successfully.")

        return render_template("verify.html", success="Your account has been verified!")
    except Exception as e:
        print(f"[ERROR] Verification exception: {e}")
        return render_template("verify.html", error="An error occurred during verification.")
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

# Utility Routes
@app.route('/restaurants', methods=['GET'])
def list_restaurants():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch all restaurants
        cursor.execute("SELECT id, name, address FROM restaurants")
        restaurants = cursor.fetchall()

        return render_template("restaurants.html", restaurants=restaurants)

    except Exception as ex:
        print(f"Error fetching restaurants: {str(ex)}")
        return render_template("error.html", message="Failed to load restaurants"), 500

    finally:
        if db and db.is_connected():
            db.close()

@app.route('/signup/selection')
def view_signup_selection():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return render_template("signup/signup_selection.html")

@app.route('/restaurants/<int:restaurant_id>', methods=['GET'])
def restaurant_detail(restaurant_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch restaurant details
        cursor.execute("""
            SELECT id, name, address, description 
            FROM restaurants WHERE id = %s
        """, (restaurant_id,))
        restaurant = cursor.fetchone()

        if not restaurant:
            return render_template("error.html", message="Restaurant not found"), 404

        # Fetch menu items
        cursor.execute("""
            SELECT id, name, description, price 
            FROM menu_items WHERE restaurant_fk = %s
        """, (restaurant_id,))
        menu_items = cursor.fetchall()

        return render_template("restaurant_detail.html", restaurant=restaurant, menu_items=menu_items)

    except Exception as ex:
        print(f"Error fetching restaurant details: {str(ex)}")
        return render_template("error.html", message="Failed to load restaurant details"), 500

    finally:
        if db and db.is_connected():
            db.close()
   
import time  # For current_time

# Route: Place Order
import time
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Ensure user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get user's saved addresses
        cursor.execute("""
            SELECT * FROM user_addresses 
            WHERE address_user_fk = %s
        """, (session['user']['user_pk'],))
        addresses = cursor.fetchall()

        # Get cart data
        cart_data = session.get('cart', {})
        if not cart_data:
            return redirect(url_for('dashboard'))

        # Calculate totals
        subtotal = 0
        delivery_fee = 29.00  # Fixed delivery fee

        # Process cart items
        cart_items = []
        for item_id, item in cart_data.items():
            subtotal += float(item['price']) * int(item['quantity'])
            cart_items.append({
                'name': item['name'],
                'price': float(item['price']),
                'quantity': int(item['quantity']),
                'subtotal': float(item['price']) * int(item['quantity'])
            })

        total_price = subtotal + delivery_fee

        # If the request is POST, place the order
        if request.method == 'POST':
            # Save order to database (simplified for demonstration)
            cursor.execute("""
                INSERT INTO orders (order_user_fk, order_total, order_created_at) 
                VALUES (%s, %s, %s)
            """, (session['user']['user_pk'], total_price, int(time.time())))
            order_id = cursor.lastrowid

            # Save order items
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO order_items (order_item_order_fk, order_item_name, order_item_price, order_item_quantity) 
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['name'], item['price'], item['quantity']))
            
            db.commit()

            # Prepare and send order confirmation email
            user_email = session['user']['user_email']
            user_name = session['user']['user_name']
            order_summary = "\n".join([f"{item['quantity']} x {item['name']} - ${item['subtotal']:.2f}" for item in cart_items])
            email_body = f"""
            <html>
                <body>
                    <h2>Order Confirmation</h2>
                    <p>Thank you for your order, {user_name}!</p>
                    <h3>Order Details:</h3>
                    <ul>
                        {''.join([f"<li>{item['quantity']} x {item['name']} - ${item['subtotal']:.2f}</li>" for item in cart_items])}
                    </ul>
                    <p><b>Delivery Fee:</b> ${delivery_fee:.2f}</p>
                    <p><b>Total:</b> ${total_price:.2f}</p>
                </body>
            </html>
            """
            send_email(user_email, "Your Order Confirmation", email_body)

            # Clear cart
            session['cart'] = {}
            return redirect(url_for('order_complete'))

        return render_template(
            'checkout.html',
            addresses=addresses,
            cart_items=cart_items,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_price=total_price,
            user=session.get('user')
        )

    except Exception as e:
        print(f"Error in checkout: {e}")
        return render_template("error.html", error="Failed to load checkout page"), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/order-complete', methods=['GET'])
def order_complete():
    # Check if the user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    # Redirect to the order history page
    return redirect(url_for('order_history'))



@app.route('/order-history', methods=['GET'])
def order_history():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session.get('user')
    print(f"[DEBUG] User session: {user}")

    orders = []  # Default orders to an empty list in case of errors
    error_message = None  # For tracking errors during processing

    try:
        # Connect to the database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        print("[DEBUG] Database connection established.")

        # Fetch user's orders
        cursor.execute("""
            SELECT 
                o.order_pk, 
                o.order_total, 
                o.order_created_at, 
                o.order_status
            FROM orders o
            WHERE o.order_user_fk = %s
            ORDER BY o.order_created_at DESC
        """, (user['user_pk'],))
        orders_data = cursor.fetchall()
        print(f"[DEBUG] Orders fetched: {orders_data}")

        # Process each order
        for order in orders_data:
            try:
                cursor.execute("""
                    SELECT 
                        i.item_name,
                        oi.order_item_quantity AS quantity,
                        oi.order_item_price AS price,
                        (oi.order_item_quantity * oi.order_item_price) AS subtotal
                    FROM order_items oi
                    JOIN items i ON oi.order_item_item_fk = i.item_pk
                    WHERE oi.order_item_order_fk = %s
                """, (order['order_pk'],))
                items = cursor.fetchall()
                print(f"[DEBUG] Items for order {order['order_pk']}: {items}")

                # Format the order data
                order['items'] = [
                    {
                        'item_name': item['item_name'],
                        'quantity': int(item['quantity']),
                        'subtotal': float(item['subtotal']),
                    }
                    for item in items
                ]
                order['formatted_date'] = datetime.fromtimestamp(order['order_created_at']).strftime('%B %d, %Y %I:%M %p')
                order['order_total'] = float(order['order_total'])  # Convert Decimal to float if necessary

            except Exception as item_error:
                print(f"[ERROR] Failed to fetch items for order {order['order_pk']}: {item_error}")
                order['items'] = []  # Assign empty items on failure

        # Assign processed orders
        orders = orders_data

    except Exception as e:
        print(f"[ERROR] Failed to fetch orders: {e}")
        error_message = "Unable to load order history. Please try again later."

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

    # Debug the final processed orders
    print(f"[DEBUG] Final orders data: {orders}")

    # Include detailed debug information in logs
    if error_message:
        print(f"[DEBUG] Error Message: {error_message}")

    # Render the order history page
    return render_template(
        "customer/order_history.html",
        user=user,
        orders=orders,
        current_year=datetime.now().year,
        error_message=error_message,
    )

@app.route("/user/profile", methods=["GET"])
def user_profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session.get("user")
    return render_template("customer/profile.html", user=user)



def generate_random_coordinates(center_lat, center_lon, radius_miles):
    """
    Generate random coordinates within a certain radius from a center point.
    """
    radius_km = radius_miles * 1.60934  # Convert miles to kilometers
    radius_earth = 6371  # Earth's radius in km

    delta_lat = radius_km / radius_earth
    delta_lon = radius_km / (radius_earth * math.cos(math.pi * center_lat / 180))

    lat_offset = random.uniform(-delta_lat, delta_lat)
    lon_offset = random.uniform(-delta_lon, delta_lon)

    return center_lat + lat_offset, center_lon + lon_offset

@app.route('/api/random-restaurants')
def random_restaurants():
    """
    Fetch restaurants from the database and assign random coordinates around a center point.
    """
    try:
        # Central location for generating random displacements (e.g., city's center)
        center_lat = 37.7749  # Example: San Francisco latitude
        center_lon = -122.4194  # Example: San Francisco longitude
        radius = 5  # Radius in miles

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch restaurants from the database
        cursor.execute("""
            SELECT restaurant_pk AS restaurant_id, restaurant_name AS name, restaurant_address AS address
            FROM restaurant_details
            LIMIT 10
        """)
        restaurants = cursor.fetchall()

        # Assign random coordinates to each restaurant
        for restaurant in restaurants:
            restaurant['latitude'], restaurant['longitude'] = generate_random_coordinates(center_lat, center_lon, radius)

        return jsonify({"restaurants": restaurants})
    except Exception as e:
        print(f"Error fetching restaurants: {e}")
        return jsonify({"error": "Failed to fetch restaurants"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()



@app.route("/user/profile/edit", methods=["POST"])
def edit_profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        user = session.get("user")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users 
            SET user_name = %s, user_last_name = %s, user_updated_at = %s 
            WHERE user_pk = %s
        """, (first_name, last_name, int(time.time()), user["user_pk"]))
        
        db.commit()
        session["user"]["user_name"] = first_name
        session["user"]["user_last_name"] = last_name

        return redirect(url_for("user_profile"))

    except Exception as ex:
        print(f"[ERROR] Edit Profile Error: {ex}")
        if "db" in locals(): db.rollback()
        return "An error occurred while updating your profile", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


@app.route("/user/profile/email", methods=["POST"])
def update_email():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        user = session.get("user")
        new_email = request.form.get("email")
        verification_key = str(uuid.uuid4())

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users 
            SET user_email = %s, user_verification_key = %s, user_verified_at = 0, user_updated_at = %s
            WHERE user_pk = %s
        """, (new_email, verification_key, int(time.time()), user["user_pk"]))

        # Send verification email
        if not send_verify_email(new_email, verification_key):
            db.rollback()
            return "Failed to send verification email", 500

        db.commit()
        session["user"]["user_email"] = new_email

        return redirect(url_for("user_profile"))

    except Exception as ex:
        print(f"[ERROR] Update Email Error: {ex}")
        if "db" in locals(): db.rollback()
        return "An error occurred while updating your email", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

@app.route("/restaurant/profile/delete", methods=["POST"])
def delete_restaurant_account():
    if 'user' not in session or 'restaurant' not in session['user']['roles']:
        return redirect(url_for('login'))

    try:
        password = request.form.get("password")
        if not password:
            return render_template("restaurant/profile.html", error="Password is required")

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch the hashed password for verification
        cursor.execute("SELECT user_password FROM users WHERE user_pk = %s", (session['user']['user_pk'],))
        user = cursor.fetchone()

        if not user or not check_password_hash(user["user_password"], password):
            return render_template("restaurant/profile.html", error="Invalid password")

        # Mark the user and restaurant as deleted
        cursor.execute("""
            UPDATE users SET user_deleted_at = %s WHERE user_pk = %s
        """, (int(time.time()), session['user']['user_pk']))
        cursor.execute("""
            UPDATE restaurant_details SET restaurant_deleted_at = %s WHERE restaurant_user_fk = %s
        """, (int(time.time()), session['user']['user_pk']))

        db.commit()
        session.clear()  # Log the user out
        return redirect(url_for('view_index'))

    except Exception as ex:
        print(f"[ERROR] Delete Account Error: {ex}")
        if "db" in locals(): db.rollback()
        return "An error occurred while deleting your account", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

@app.route("/user/profile/delete", methods=["POST"])
def delete_account():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        user = session.get("user")
        verification_key = str(uuid.uuid4())

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users 
            SET user_deleted_at = %s, user_verification_key = %s
            WHERE user_pk = %s
        """, (int(time.time()), verification_key, user["user_pk"]))

        # Send verification email for account deletion
        if not send_verify_email(user["user_email"], verification_key):
            db.rollback()
            return "Failed to send account deletion verification email", 500

        db.commit()
        return "Check your email to verify account deletion", 200

    except Exception as ex:
        print(f"[ERROR] Delete Account Error: {ex}")
        if "db" in locals(): db.rollback()
        return "An error occurred while deleting your account", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

import logging


# Setup logging
logging.basicConfig(filename="admin_user_management.log", level=logging.INFO)

@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Fetch users (for managing users)
        cursor.execute("SELECT * FROM users WHERE user_deleted_at IS NULL OR user_deleted_at = 0")
        users = cursor.fetchall()

        # Fetch items (for managing items)
        cursor.execute("SELECT * FROM items WHERE item_deleted_at IS NULL")
        items = cursor.fetchall()

        # Render the dashboard template with both users and items
        return render_template('admin/dashboard.html', users=users, items=items)

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        return render_template("error.html", error="An error occurred while loading the dashboard"), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
def send_status_update_email(email, status):
    try:
        subject = "Account Status Update"
        if status == "blocked":
            body = "Your account has been blocked. Please contact support for further assistance."
        elif status == "unblocked":
            body = "Your account has been unblocked. You can now access your account."

        message = MIMEMultipart()
        message["From"] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message["To"] = email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send the email via SMTP
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['APP_PASSWORD'])
            server.send_message(message)

        print(f"Sent {status} email to {email}")
        return True

    except Exception as ex:
        print(f"Error sending status update email: {ex}")
        return False

@app.route('/admin/block_user/<user_pk>', methods=['POST'])
def block_user(user_pk):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Update the user as blocked in the database
        cursor.execute("""
            UPDATE users
            SET user_blocked_at = %s
            WHERE user_pk = %s
        """, (int(time.time()), user_pk))

        # Commit the changes
        db.commit()

        # Get the user's email
        cursor.execute("SELECT user_email FROM users WHERE user_pk = %s", (user_pk,))
        user = cursor.fetchone()

        if user:
            # Send the "blocked" email
            send_status_update_email(user['user_email'], "blocked")

        return jsonify({"success": True, "message": "User blocked successfully."}), 200

    except Exception as e:
        print(f"Error blocking user: {e}")
        return jsonify({"error": "An error occurred while blocking the user"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/admin/unblock_user/<user_pk>', methods=['POST'])
def unblock_user(user_pk):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Update the user as unblocked in the database
        cursor.execute("""
            UPDATE users
            SET user_blocked_at = NULL
            WHERE user_pk = %s
        """, (user_pk,))

        # Commit the changes
        db.commit()

        # Get the user's email
        cursor.execute("SELECT user_email FROM users WHERE user_pk = %s", (user_pk,))
        user = cursor.fetchone()

        if user:
            # Send the "unblocked" email
            send_status_update_email(user['user_email'], "unblocked")

        return jsonify({"success": True, "message": "User unblocked successfully."}), 200

    except Exception as e:
        print(f"Error unblocking user: {e}")
        return jsonify({"error": "An error occurred while unblocking the user"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

def send_item_status_update_email(restaurant_email, item_name, status):
    try:
        subject = "Dish Status Update"
        if status == "blocked":
            body = f"The dish '{item_name}' has been blocked. Please contact support if you have any questions."
        elif status == "unblocked":
            body = f"The dish '{item_name}' has been unblocked and is now available for ordering."

        message = MIMEMultipart()
        message["From"] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message["To"] = restaurant_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send the email via SMTP
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['APP_PASSWORD'])
            server.send_message(message)

        print(f"Sent {status} email for item '{item_name}' to {restaurant_email}")
        return True

    except Exception as ex:
        print(f"Error sending item status update email: {ex}")
        return False


@app.route('/admin/block_item/<item_pk>', methods=['POST'])
def block_item(item_pk):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Block the item (set item_blocked_at to the current timestamp)
        cursor.execute("""
            UPDATE items
            SET item_blocked_at = %s
            WHERE item_pk = %s
        """, (int(time.time()), item_pk))

        # Commit the changes
        db.commit()

        # Get the item details and restaurant owner email
        cursor.execute("""
            SELECT i.item_name, rd.restaurant_user_fk, u.user_email
            FROM items i
            JOIN restaurant_details rd ON i.item_restaurant_fk = rd.restaurant_pk
            JOIN users u ON rd.restaurant_user_fk = u.user_pk
            WHERE i.item_pk = %s
        """, (item_pk,))
        item = cursor.fetchone()

        if item:
            # Send email to the restaurant owner about the blocked item
            send_item_status_update_email(item['user_email'], item['item_name'], "blocked")

        return jsonify({"success": True, "message": "Item blocked successfully."}), 200

    except Exception as e:
        print(f"Error blocking item: {e}")
        return jsonify({"error": "An error occurred while blocking the item"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/admin/unblock_item/<item_pk>', methods=['POST'])
def unblock_item(item_pk):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Unblock the item (set item_blocked_at to NULL)
        cursor.execute("""
            UPDATE items
            SET item_blocked_at = NULL
            WHERE item_pk = %s
        """, (item_pk,))

        # Commit the changes
        db.commit()

        # Get the item details and restaurant owner email
        cursor.execute("""
            SELECT i.item_name, rd.restaurant_user_fk, u.user_email
            FROM items i
            JOIN restaurant_details rd ON i.item_restaurant_fk = rd.restaurant_pk
            JOIN users u ON rd.restaurant_user_fk = u.user_pk
            WHERE i.item_pk = %s
        """, (item_pk,))
        item = cursor.fetchone()

        if item:
            # Send email to the restaurant owner about the unblocked item
            send_item_status_update_email(item['user_email'], item['item_name'], "unblocked")

        return jsonify({"success": True, "message": "Item unblocked successfully."}), 200

    except Exception as e:
        print(f"Error unblocking item: {e}")
        return jsonify({"error": "An error occurred while unblocking the item"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()




@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

# Main Application Entry Point
if __name__ == '__main__':
    app.run(debug=True)