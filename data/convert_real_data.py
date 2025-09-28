import sqlite3
import pandas as pd

def convert_csv_to_sqlite():
    conn = sqlite3.connect('gaming_transactions.db')
    
    # Drop existing tables
    conn.execute('DROP TABLE IF EXISTS purchases')
    conn.execute('DROP TABLE IF EXISTS products')
    conn.execute('DROP TABLE IF EXISTS customers')
    
    # Create tables
    conn.execute('''CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        state TEXT NOT NULL,
        verified BOOLEAN NOT NULL
    )''')
    
    conn.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    )''')
    
    conn.execute('''CREATE TABLE purchases (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        date DATETIME NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    # Load and insert data
    customers = pd.read_csv('./data/customers.csv')
    customers['verified'] = customers['verified'].astype(bool)
    customers.to_sql('customers', conn, if_exists='replace', index=False)
    
    products = pd.read_csv('./data/products.csv')
    products.to_sql('products', conn, if_exists='replace', index=False)
    
    purchases = pd.read_csv('./data/purchases.csv')
    purchases['date'] = pd.to_datetime(purchases['date'])
    purchases.to_sql('purchases', conn, if_exists='replace', index=False)
    
    # Create indexes
    conn.execute('CREATE INDEX idx_customers_state ON customers(state)')
    conn.execute('CREATE INDEX idx_products_category ON products(category)')
    conn.execute('CREATE INDEX idx_purchases_customer_id ON purchases(customer_id)')
    conn.execute('CREATE INDEX idx_purchases_date ON purchases(date)')
    
    conn.commit()
    conn.close()
    print("Database created gaming_transactions.db")

if __name__ == "__main__":
    convert_csv_to_sqlite()