from flask import Flask

# Flask app initialization (optional for a standalone test)
app = Flask(__name__)

# Database Configuration
DB_HOST = "mysql"  # Match your config
DB_USER = "root"
DB_PASSWORD = "password"
DB_NAME = "company"

def test_db_connection():
    try:
        # Establish connection
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print(f"Connected successfully to the database: {DB_NAME}")
        connection.close()
    except Exception as e:
        print(f"Failed to connect to the database: {e}")

# Run the test
if __name__ == "__main__":
    test_db_connection()
