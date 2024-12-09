import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_db_connection():
    try:
        print(f"Attempting to connect to database: {DB_NAME} on host: {DB_HOST}")
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("Database connection successful")
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        raise Exception("Database connection error")