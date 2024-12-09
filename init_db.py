import mysql.connector
import os
import datetime
import uuid

DB_HOST = 'mysql'
DB_USER = 'root'
DB_PASSWORD = 'password'
DB_NAME = 'company'
BACKUP_DIR = '.'

def generate_initial_data():
    # Role constants
    ADMIN_ROLE = str(uuid.uuid4())
    CUSTOMER_ROLE = str(uuid.uuid4())
    RESTAURANT_ROLE = str(uuid.uuid4())
    PARTNER_ROLE = str(uuid.uuid4())

    create_tables = [
        """CREATE TABLE roles (
            role_pk CHAR(36) PRIMARY KEY,
            role_name VARCHAR(50) NOT NULL,
            role_created_at INTEGER UNSIGNED
        );""",
        
        """CREATE TABLE users (
            user_pk CHAR(36) PRIMARY KEY,
            user_name VARCHAR(20) NOT NULL,
            user_last_name VARCHAR(20) NOT NULL,
            user_email VARCHAR(100) NOT NULL UNIQUE,
            user_password VARCHAR(255) NOT NULL,
            user_avatar VARCHAR(50),
            user_created_at INTEGER UNSIGNED,
            user_deleted_at INTEGER UNSIGNED DEFAULT 0,
            user_blocked_at INTEGER UNSIGNED DEFAULT 0,
            user_updated_at INTEGER UNSIGNED DEFAULT 0,
            user_verified_at INTEGER UNSIGNED DEFAULT 0,
            user_verification_key CHAR(36)
        );""",

        """CREATE TABLE users_roles (
            user_role_pk INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_role_user_fk CHAR(36),
            user_role_role_fk CHAR(36),
            FOREIGN KEY (user_role_user_fk) REFERENCES users(user_pk),
            FOREIGN KEY (user_role_role_fk) REFERENCES roles(role_pk)
        );""",

        """CREATE TABLE restaurant_details (
            restaurant_pk CHAR(36) PRIMARY KEY,
            restaurant_user_fk CHAR(36),
            restaurant_name VARCHAR(100) NOT NULL,
            restaurant_phone VARCHAR(20) NOT NULL,
            restaurant_address VARCHAR(255) NOT NULL,
            restaurant_city VARCHAR(100) NOT NULL,
            restaurant_postal_code VARCHAR(10) NOT NULL,
            restaurant_created_at INTEGER UNSIGNED,
            restaurant_lat DECIMAL(10,8),
            restaurant_lng DECIMAL(11,8),
            FOREIGN KEY (restaurant_user_fk) REFERENCES users(user_pk)
        );""",

        """CREATE TABLE restaurant_hours (
            restaurant_hours_pk INTEGER PRIMARY KEY AUTO_INCREMENT,
            restaurant_hours_restaurant_fk CHAR(36),
            restaurant_hours_day VARCHAR(10) NOT NULL,
            restaurant_hours_open TIME NOT NULL,
            restaurant_hours_close TIME NOT NULL,
            FOREIGN KEY (restaurant_hours_restaurant_fk) REFERENCES restaurant_details(restaurant_pk)
        );""",

        """CREATE TABLE items (
            item_pk CHAR(36) PRIMARY KEY,
            item_restaurant_fk CHAR(36),
            item_name VARCHAR(100) NOT NULL,
            item_description TEXT,
            item_price DECIMAL(10,2) NOT NULL,
            item_created_at INTEGER UNSIGNED,
            item_deleted_at INTEGER UNSIGNED DEFAULT 0,
            item_blocked_at INTEGER UNSIGNED DEFAULT 0,
            FOREIGN KEY (item_restaurant_fk) REFERENCES restaurant_details(restaurant_pk)
        );""",

        """CREATE TABLE item_images (
            item_image_pk INTEGER PRIMARY KEY AUTO_INCREMENT,
            item_image_item_fk CHAR(36),
            item_image_filename VARCHAR(50) NOT NULL,
            item_image_order INTEGER DEFAULT 0,
            FOREIGN KEY (item_image_item_fk) REFERENCES items(item_pk)
        );""",

        """CREATE TABLE orders (
            order_pk CHAR(36) PRIMARY KEY,
            order_user_fk CHAR(36),
            order_restaurant_fk CHAR(36),
            order_created_at INTEGER UNSIGNED,
            order_total DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_user_fk) REFERENCES users(user_pk),
            FOREIGN KEY (order_restaurant_fk) REFERENCES restaurant_details(restaurant_pk)
        );""",

        """CREATE TABLE order_items (
            order_item_pk INTEGER PRIMARY KEY AUTO_INCREMENT,
            order_item_order_fk CHAR(36),
            order_item_item_fk CHAR(36),
            order_item_quantity INTEGER NOT NULL,
            order_item_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_item_order_fk) REFERENCES orders(order_pk),
            FOREIGN KEY (order_item_item_fk) REFERENCES items(item_pk)
        );""",

        """CREATE TABLE order_status_history (
            order_status_pk INTEGER PRIMARY KEY AUTO_INCREMENT,
            order_status_order_fk CHAR(36),
            order_status_name VARCHAR(50) NOT NULL,
            order_status_created_at INTEGER UNSIGNED,
            FOREIGN KEY (order_status_order_fk) REFERENCES orders(order_pk)
        );"""
    ]

    initial_data = [
        # Roles
        f"INSERT INTO roles VALUES ('{ADMIN_ROLE}', 'admin', {int(datetime.datetime.now().timestamp())});",
        f"INSERT INTO roles VALUES ('{CUSTOMER_ROLE}', 'customer', {int(datetime.datetime.now().timestamp())});",
        f"INSERT INTO roles VALUES ('{RESTAURANT_ROLE}', 'restaurant', {int(datetime.datetime.now().timestamp())});",
        f"INSERT INTO roles VALUES ('{PARTNER_ROLE}', 'partner', {int(datetime.datetime.now().timestamp())});",

        # Admin user
        f"""INSERT INTO users VALUES (
            '{str(uuid.uuid4())}', 'Admin', 'User', 'admin@foodhub.com',
            '$2y$10$abcdefghijklmnopqrstuv', NULL, {int(datetime.datetime.now().timestamp())},
            0, 0, 0, {int(datetime.datetime.now().timestamp())}, NULL
        );"""
    ]

    return create_tables, initial_data

def backup_database():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        cursor = connection.cursor()

        create_tables, initial_data = generate_initial_data()
        backup_file = os.path.join(BACKUP_DIR, 
            f"{DB_NAME}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")

        with open(backup_file, 'w') as f:
            # Write table creation
            for create_stmt in create_tables:
                f.write(f"{create_stmt}\n\n")

            # Write initial data
            for insert_stmt in initial_data:
                f.write(f"{insert_stmt}\n")

            # Backup existing data
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            for (table_name,) in tables:
                cursor.execute(f"SELECT * FROM {table_name};")
                rows = cursor.fetchall()
                for row in rows:
                    formatted_values = [
                        f'"{value}"' if isinstance(value, (str, datetime.date)) else str(value)
                        for value in row
                    ]
                    f.write(f"INSERT INTO {table_name} VALUES ({', '.join(formatted_values)});\n")
                f.write("\n")

        print(f"Backup successful! Saved to {backup_file}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'connection' in locals(): connection.close()

if __name__ == "__main__":
    backup_database()