import mysql.connector

connection = mysql.connector.connect(
    host="mysql",
    user="root",
    password="password",
    database="company"
)

cursor = connection.cursor()

try:
    # Check table structures
    cursor.execute("DESCRIBE orders")
    print("Orders columns:")
    for column in cursor.fetchall():
        print(column)
        
    cursor.execute("DESCRIBE items")
    print("\nItems columns:")
    for column in cursor.fetchall():
        print(column)
        
    cursor.execute("DESCRIBE item_images")
    print("\nItem_images columns:")
    for column in cursor.fetchall():
        print(column)

    cursor.execute("DESCRIBE restaurant_details")
    print("\nRestaurant_details columns:")
    for column in cursor.fetchall():
        print(column)

except mysql.connector.Error as error:
    print(f"Error: {error}")
finally:
    cursor.close()
    connection.close()