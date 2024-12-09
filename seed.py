import mysql.connector
from faker import Faker
import random
import uuid
import time
from werkzeug.security import generate_password_hash

fake = Faker()
RESTAURANT_ROLE_PK = "9f8c8d22-5a67-4b6c-89d7-58f8b8cb4e15"
CUSTOMER_ROLE_PK = "c56a4180-65aa-42ec-a945-5fd21dec0538"
current_time = int(time.time())

connection = mysql.connector.connect(
   host="mysql",
   user="root",
   password="password", 
   database="company"
)

cursor = connection.cursor()

try:
   cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
   cursor.execute("DELETE FROM items")
   cursor.execute("DELETE FROM item_images")
   cursor.execute("DELETE FROM orders")
   cursor.execute("DELETE FROM order_items")
   cursor.execute("DELETE FROM order_status_history")
   cursor.execute("DELETE FROM restaurant_details")
   cursor.execute("DELETE FROM restaurant_hours")
   cursor.execute("DELETE FROM users_roles WHERE user_role_role_fk != 'admin'")
   cursor.execute("DELETE FROM users WHERE user_email != 'admin@foodhub.com'")
   cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
   connection.commit()

   # Create customers
   customer_pks = []
   for _ in range(20):
       user_pk = str(uuid.uuid4())
       customer_pks.append(user_pk)
       user = {
           'user_pk': user_pk,
           'user_name': fake.first_name(),
           'user_last_name': fake.last_name(),
           'user_email': fake.email(),
           'user_password': generate_password_hash('password'),
           'user_avatar': None,
           'user_created_at': current_time,
           'user_deleted_at': 0,
           'user_blocked_at': 0,
           'user_updated_at': 0,
           'user_verified_at': current_time,
           'user_verification_key': str(uuid.uuid4())
       }
       
       cursor.execute("""
           INSERT INTO users VALUES (
               %(user_pk)s, %(user_name)s, %(user_last_name)s,
               %(user_email)s, %(user_password)s, %(user_avatar)s,
               %(user_created_at)s, %(user_deleted_at)s, %(user_blocked_at)s,
               %(user_updated_at)s, %(user_verified_at)s, %(user_verification_key)s
           )
       """, user)

       cursor.execute("""
           INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
           VALUES (%s, %s)
       """, (user_pk, CUSTOMER_ROLE_PK))

   # Create restaurants
   restaurant_pks = []
   for _ in range(10):
       user_pk = str(uuid.uuid4()) 
       restaurant_pk = str(uuid.uuid4())
       restaurant_pks.append(restaurant_pk)

       user = {
           'user_pk': user_pk,
           'user_name': fake.company(),
           'user_last_name': 'Restaurant',
           'user_email': fake.email(),
           'user_password': generate_password_hash('password'),
           'user_avatar': None,
           'user_created_at': current_time,
           'user_deleted_at': 0,
           'user_blocked_at': 0,
           'user_updated_at': 0, 
           'user_verified_at': current_time,
           'user_verification_key': str(uuid.uuid4())
       }

       cursor.execute("""
           INSERT INTO users VALUES (
               %(user_pk)s, %(user_name)s, %(user_last_name)s,
               %(user_email)s, %(user_password)s, %(user_avatar)s,
               %(user_created_at)s, %(user_deleted_at)s, %(user_blocked_at)s,
               %(user_updated_at)s, %(user_verified_at)s, %(user_verification_key)s
           )
       """, user)

       cursor.execute("""
           INSERT INTO users_roles (user_role_user_fk, user_role_role_fk)
           VALUES (%s, %s)
       """, (user_pk, RESTAURANT_ROLE_PK))

       restaurant = {
           'restaurant_pk': restaurant_pk,
           'restaurant_user_fk': user_pk,
           'restaurant_name': user['user_name'],
           'restaurant_description': fake.paragraph(),
           'restaurant_phone': fake.phone_number(),
           'restaurant_address': fake.street_address(),
           'restaurant_city': fake.city(),
           'restaurant_postal_code': str(random.randint(1000, 9999)),
           'restaurant_latitude': random.uniform(55.0, 58.0),
           'restaurant_longitude': random.uniform(8.0, 13.0),
           'restaurant_created_at': current_time,
           'restaurant_updated_at': current_time,
           'restaurant_rating': round(random.uniform(3.5, 5.0), 1),
           'restaurant_rating_count': random.randint(10, 100),
           'restaurant_min_order': round(random.uniform(50, 150), 2),
           'restaurant_delivery_fee': round(random.uniform(29, 49), 2)
       }

       cursor.execute("""
           INSERT INTO restaurant_details VALUES (
               %(restaurant_pk)s, %(restaurant_user_fk)s, %(restaurant_name)s,
               %(restaurant_description)s, %(restaurant_phone)s, %(restaurant_address)s,
               %(restaurant_city)s, %(restaurant_postal_code)s, %(restaurant_latitude)s,
               %(restaurant_longitude)s, %(restaurant_created_at)s, %(restaurant_updated_at)s,
               %(restaurant_rating)s, %(restaurant_rating_count)s, %(restaurant_min_order)s,
               %(restaurant_delivery_fee)s
           )
       """, restaurant)

       # Create menu items
       for _ in range(random.randint(5, 10)):
           item_pk = str(uuid.uuid4())
           item = {
               'item_pk': item_pk,
               'item_restaurant_fk': restaurant_pk,
               'item_name': fake.sentence(nb_words=3),
               'item_description': fake.paragraph(nb_sentences=2),
               'item_price': round(random.uniform(5, 30), 2),
               'item_category': random.choice(['Appetizers', 'Main Course', 'Desserts', 'Drinks']),
               'item_created_at': current_time,
               'item_updated_at': current_time,
               'item_deleted_at': None,
               'item_available': 1
           }
           
           cursor.execute("""
               INSERT INTO items VALUES (
                   %(item_pk)s, %(item_restaurant_fk)s, %(item_name)s,
                   %(item_description)s, %(item_price)s, %(item_category)s,
                   %(item_created_at)s, %(item_updated_at)s, %(item_deleted_at)s,
                   %(item_available)s
               )
           """, item)

           for image_order in range(1, random.randint(2, 4)):
               image = {
                   'image_pk': str(uuid.uuid4()),
                   'image_item_fk': item_pk,
                   'image_url': f"food_{random.randint(1,10)}.jpg",
                   'image_order': image_order
               }
               
               cursor.execute("""
                   INSERT INTO item_images VALUES (
                       %(image_pk)s, %(image_item_fk)s, %(image_url)s, %(image_order)s
                   )
               """, image)

   # Create orders
   for _ in range(30):
       order_pk = str(uuid.uuid4())
       restaurant_pk = random.choice(restaurant_pks)
       
       cursor.execute("SELECT item_pk, item_price FROM items WHERE item_restaurant_fk = %s", (restaurant_pk,))
       available_items = cursor.fetchall()
       
       if available_items:
           order_items = random.sample(available_items, random.randint(1, 3))
           total = sum(float(item[1]) for item in order_items)
           
           order = {
               'order_pk': order_pk,
               'order_user_fk': random.choice(customer_pks),
               'order_restaurant_fk': restaurant_pk,
               'order_status': random.choice(['delivering', 'delivered']),
               'order_total': total,
               'order_delivery_fee': round(random.uniform(29, 49), 2),
               'order_address': fake.street_address(),
               'order_city': fake.city(),
               'order_postal_code': str(random.randint(1000, 9999)),
               'order_phone': fake.phone_number(),
               'order_notes': fake.text(max_nb_chars=100),
               'order_created_at': current_time,
               'order_updated_at': current_time,
               'order_delivered_at': current_time
           }

           cursor.execute("""
               INSERT INTO orders VALUES (
                   %(order_pk)s, %(order_user_fk)s, %(order_restaurant_fk)s,
                   %(order_status)s, %(order_total)s, %(order_delivery_fee)s,
                   %(order_address)s, %(order_city)s, %(order_postal_code)s,
                   %(order_phone)s, %(order_notes)s, %(order_created_at)s,
                   %(order_updated_at)s, %(order_delivered_at)s
               )
           """, order)

   connection.commit()
   print("Test data seeded successfully!")

except mysql.connector.Error as error:
   print(f"Error seeding test data: {error}")
   connection.rollback()

finally:
   cursor.close()
   connection.close()