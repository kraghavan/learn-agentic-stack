"""
Creates a sample SQLite database for testing the SQL Query Agent.
Run this once to generate the test data.
"""

import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "sample_store.db"

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript("""
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
        
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            city TEXT,
            signup_date DATE,
            is_premium BOOLEAN DEFAULT 0
        );
        
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price DECIMAL(10, 2),
            stock_quantity INTEGER DEFAULT 0
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_amount DECIMAL(10, 2),
            order_date DATE,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)
    
    # Sample data
    customers = [
        ("Alice Johnson", "alice@email.com", "New York", "2025-06-15", 1),
        ("Bob Smith", "bob@email.com", "Los Angeles", "2025-08-22", 0),
        ("Carol White", "carol@email.com", "Chicago", "2025-09-10", 1),
        ("David Brown", "david@email.com", "Houston", "2025-11-05", 0),
        ("Eva Martinez", "eva@email.com", "Phoenix", "2025-12-01", 1),
        ("Frank Lee", "frank@email.com", "New York", "2026-01-10", 0),
        ("Grace Kim", "grace@email.com", "Los Angeles", "2026-01-15", 1),
        ("Henry Wilson", "henry@email.com", "Chicago", "2026-01-20", 0),
        ("Ivy Chen", "ivy@email.com", "Seattle", "2026-02-01", 1),
        ("Jack Davis", "jack@email.com", "Boston", "2026-02-05", 0),
    ]
    
    products = [
        ("Laptop Pro", "Electronics", 1299.99, 50),
        ("Wireless Mouse", "Electronics", 29.99, 200),
        ("USB-C Hub", "Electronics", 49.99, 150),
        ("Mechanical Keyboard", "Electronics", 149.99, 75),
        ("Monitor 27inch", "Electronics", 399.99, 30),
        ("Python Handbook", "Books", 45.99, 100),
        ("AI Fundamentals", "Books", 59.99, 80),
        ("Data Science Guide", "Books", 54.99, 90),
        ("Coffee Mug", "Accessories", 12.99, 500),
        ("Desk Lamp", "Accessories", 34.99, 120),
    ]
    
    cursor.executemany(
        "INSERT INTO customers (name, email, city, signup_date, is_premium) VALUES (?, ?, ?, ?, ?)",
        customers
    )
    
    cursor.executemany(
        "INSERT INTO products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
        products
    )
    
    # Generate random orders
    statuses = ["pending", "shipped", "delivered", "cancelled"]
    orders = []
    
    for i in range(50):
        customer_id = random.randint(1, len(customers))
        product_id = random.randint(1, len(products))
        quantity = random.randint(1, 5)
        
        # Get product price
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        price = cursor.fetchone()[0]
        total = round(price * quantity, 2)
        
        # Random date in last 3 months
        days_ago = random.randint(0, 90)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        status = random.choice(statuses)
        
        orders.append((customer_id, product_id, quantity, total, order_date, status))
    
    cursor.executemany(
        "INSERT INTO orders (customer_id, product_id, quantity, total_amount, order_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        orders
    )
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database created: {DB_PATH}")
    print(f"   - {len(customers)} customers")
    print(f"   - {len(products)} products")
    print(f"   - {len(orders)} orders")

if __name__ == "__main__":
    create_database()
