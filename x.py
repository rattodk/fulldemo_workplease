from flask import request, make_response
from functools import wraps
import mysql.connector
import re
import os
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_CONFIG

from icecream import ic
ic.configureOutput(prefix=f'***** | ', includeContext=True)

# Role Constants
ADMIN_ROLE_PK = "16fd2706-8baf-433b-82eb-8c7fada847da"
CUSTOMER_ROLE_PK = "c56a4180-65aa-42ec-a945-5fd21dec0538"
DELIVERY_ROLE_PK = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
RESTAURANT_ROLE_PK = "9f8c8d22-5a67-4b6c-89d7-58f8b8cb4e15"

# File Upload Settings
UPLOAD_FOLDER = './static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class CustomException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code

def raise_custom_exception(error, status_code):
    raise CustomException(error, status_code)

##############################
# Database Connection
##############################
def db():
    db = mysql.connector.connect(
        host="mysql",
        user="root",
        password="password",
        database="company"
    )
    cursor = db.cursor(dictionary=True)
    return db, cursor

##############################
# Decorators
##############################
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache_view

##############################
# Validation Functions
##############################
# User Validation
USER_NAME_MIN = 2
USER_NAME_MAX = 20
USER_NAME_REGEX = f"^.{{{USER_NAME_MIN},{USER_NAME_MAX}}}$"
def validate_user_name():
    error = f"name must be {USER_NAME_MIN} to {USER_NAME_MAX} characters"
    user_name = request.form.get("user_name", "").strip()
    if not re.match(USER_NAME_REGEX, user_name): raise_custom_exception(error, 400)
    return user_name

USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
USER_LAST_NAME_REGEX = f"^.{{{USER_LAST_NAME_MIN},{USER_LAST_NAME_MAX}}}$"
def validate_user_last_name():
    error = f"last name must be {USER_LAST_NAME_MIN} to {USER_LAST_NAME_MAX} characters"
    user_last_name = request.form.get("user_last_name", "").strip()
    if not re.match(USER_LAST_NAME_REGEX, user_last_name): raise_custom_exception(error, 400)
    return user_last_name

REGEX_EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
def validate_user_email():
    error = "invalid email format"
    user_email = request.form.get("user_email", "").strip()
    if not re.match(REGEX_EMAIL, user_email): raise_custom_exception(error, 400)
    return user_email

USER_PASSWORD_MIN = 8
USER_PASSWORD_MAX = 50
REGEX_USER_PASSWORD = f"^.{{{USER_PASSWORD_MIN},{USER_PASSWORD_MAX}}}$"
def validate_user_password():
    error = f"password must be {USER_PASSWORD_MIN} to {USER_PASSWORD_MAX} characters"
    user_password = request.form.get("user_password", "").strip()
    if not re.match(REGEX_USER_PASSWORD, user_password): raise_custom_exception(error, 400)
    return user_password

# Restaurant Validation
def validate_restaurant_name():
    error = "restaurant name must be 2 to 100 characters"
    name = request.form.get("user_name", "").strip()
    if not 2 <= len(name) <= 100: raise_custom_exception(error, 400)
    return name

def validate_restaurant_phone():
    error = "invalid phone number format"
    phone = request.form.get("restaurant_phone", "").strip()
    if not re.match(r"^\+?[\d\s-]{8,20}$", phone): raise_custom_exception(error, 400)
    return phone

def validate_restaurant_address():
    error = "address must be 5 to 255 characters"
    address = request.form.get("restaurant_address", "").strip()
    if not 5 <= len(address) <= 255: raise_custom_exception(error, 400)
    return address

def validate_restaurant_city():
    error = "city must be 2 to 100 characters"
    city = request.form.get("restaurant_city", "").strip()
    if not 2 <= len(city) <= 100: raise_custom_exception(error, 400)
    return city

def validate_restaurant_postal():
    error = "invalid postal code"
    postal = request.form.get("restaurant_postal", "").strip()
    if not re.match(r"^\d{4}$", postal): raise_custom_exception(error, 400)
    return postal

# General Validation
REGEX_UUID4 = "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
def validate_uuid4(uuid4 = ""):
    error = "invalid uuid4"
    if not uuid4:
        uuid4 = request.values.get("uuid4", "").strip()
    if not re.match(REGEX_UUID4, uuid4): raise_custom_exception(error, 400)
    return uuid4

##############################
# File Handling
##############################
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder):
    if not file: raise_custom_exception("no file provided", 400)
    if file.filename == '': raise_custom_exception("no filename", 400)
    if not allowed_file(file.filename): raise_custom_exception("invalid file type", 400)
    
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    file.save(os.path.join(UPLOAD_FOLDER, folder, filename))
    return filename

##############################
# Email Functions
##############################
def send_verify_email(to_email, verification_key):
    try:
        message = MIMEMultipart()
        message["From"] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message["To"] = to_email
        message["Subject"] = "Verify Your Email"

        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Welcome to {EMAIL_CONFIG['SENDER_NAME']}!</h2>
                    <p>Please verify your email address by clicking the button below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{EMAIL_CONFIG['BASE_URL']}/verify/{verification_key}"
                           style="background-color: #0066cc; color: white; padding: 12px 25px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            Verify Email
                        </a>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        If the button doesn't work, copy and paste this link into your browser:
                        <br>
                        {EMAIL_CONFIG['BASE_URL']}/verify/{verification_key}
                    </p>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['APP_PASSWORD'])
            server.send_message(message)
        
        return True
    
    except Exception as ex:
        print(f"Email error: {str(ex)}")
        return False

##############################
# Helper Functions
##############################
def get_user_by_id(user_pk):
    try:
        db_conn, cursor = db()
        cursor.execute("""
            SELECT * FROM users 
            WHERE user_pk = %s AND user_deleted_at = 0
        """, (user_pk,))
        return cursor.fetchone()
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db_conn' in locals(): db_conn.close()

def get_restaurant_details(restaurant_pk):
    try:
        db_conn, cursor = db()
        cursor.execute("""
            SELECT * FROM restaurant_details 
            WHERE restaurant_pk = %s
        """, (restaurant_pk,))
        return cursor.fetchone()
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db_conn' in locals(): db_conn.close()

def format_timestamp(timestamp):
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')