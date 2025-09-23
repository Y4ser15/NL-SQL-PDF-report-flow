"""
Simple database setup script for mock data generation
Creates 50k customers, 5k products, 300k purchases as required
"""

import sqlite3
import random
import string
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)  # Reproducible data


def create_database():
    """Create SQLite database with sample data"""
    conn = sqlite3.connect('sample_data.db')
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute('DROP TABLE IF EXISTS purchases')
    cursor.execute('DROP TABLE IF EXISTS products') 
    cursor.execute('DROP TABLE IF EXISTS customers')
    
    # Create tables
    cursor.execute('''
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        state TEXT NOT NULL,
        verified BOOLEAN NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        purchase_date DATE NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    print("Tables created successfully")
    
    # Generate customers (50k)
    print("Generating 50k customers...")
    us_states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
    
    customers_data = []
    used_emails = set()
    
    for i in range(50000):
        # Ensure unique email
        while True:
            email = fake.email()
            if email not in used_emails:
                used_emails.add(email)
                break
        
        customers_data.append((
            fake.name(),
            email,
            random.choice(us_states),
            random.choice([True, False])
        ))
        
        # Insert in batches for better performance
        if i % 10000 == 0 and i > 0:
            cursor.executemany(
                'INSERT INTO customers (name, email, state, verified) VALUES (?, ?, ?, ?)',
                customers_data
            )
            customers_data = []
            conn.commit()
            print(f"Inserted {i} customers...")
    
    # Insert remaining customers
    if customers_data:
        cursor.executemany(
            'INSERT INTO customers (name, email, state, verified) VALUES (?, ?, ?, ?)',
            customers_data
        )
        conn.commit()
    
    print("Customers generation complete!")
    
    # Generate products (5k)
    print("Generating 5k products...")
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports', 'Beauty', 'Toys']
    
    products_data = []
    for i in range(5000):
        products_data.append((
            fake.word().title() + ' ' + fake.word().title(),
            random.choice(categories),
            round(random.uniform(5.99, 999.99), 2)
        ))
    
    cursor.executemany(
        'INSERT INTO products (name, category, price) VALUES (?, ?, ?)',
        products_data
    )
    conn.commit()
    print("Products generation complete!")
    
    # Generate purchases (300k)
    print("Generating 300k purchases...")
    start_date = datetime.now() - timedelta(days=365)
    
    # Pre-load all product prices for efficiency
    cursor.execute('SELECT id, price FROM products')
    product_prices = dict(cursor.fetchall())
    
    purchases_data = []
    for i in range(300000):
        customer_id = random.randint(1, 50000)
        product_id = random.randint(1, 5000)
        quantity = random.randint(1, 5)
        
        # Get product price from pre-loaded dict
        price = product_prices[product_id]
        
        purchase_date = start_date + timedelta(days=random.randint(0, 365))
        total_amount = round(price * quantity, 2)
        
        purchases_data.append((
            customer_id,
            product_id, 
            quantity,
            purchase_date.date(),
            total_amount
        ))
        
        # Commit in batches for performance
        if i % 10000 == 0 and i > 0:
            cursor.executemany(
                'INSERT INTO purchases (customer_id, product_id, quantity, purchase_date, total_amount) VALUES (?, ?, ?, ?, ?)',
                purchases_data
            )
            purchases_data = []
            conn.commit()
            print(f"Inserted {i} purchases...")
    
    # Insert remaining purchases
    if purchases_data:
        cursor.executemany(
            'INSERT INTO purchases (customer_id, product_id, quantity, purchase_date, total_amount) VALUES (?, ?, ?, ?, ?)',
            purchases_data
        )
    
    conn.commit()
    conn.close()
    print("Database setup complete!")
    print("Final result: 50k customers, 5k products, 300k purchases created successfully!")


if __name__ == "__main__":
    create_database()
