import sqlite3
import os

DB_NAME = "ecommerce.db"

def setup_database():
    # Delete old database if it exists to start fresh
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Removed old database: {DB_NAME}")

    # Connect to SQLite (this creates the file if it doesn't exist)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Customers Table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            loyalty_status TEXT,  -- e.g., Gold, Silver, Bronze, or NULL
            account_created TEXT,
            phone_number TEXT     -- Added this because real data has messy phone numbers
        )
    """)

    # 2. Orders Table
    cursor.execute("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_date TEXT,
            total_amount REAL,
            payment_status TEXT,  -- e.g., Paid, Refunded, Failed, Pending
            shipping_address TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    """)

    # 3. Order Items Table
    cursor.execute("""
        CREATE TABLE order_items (
            item_id TEXT PRIMARY KEY,
            order_id TEXT,
            product_name TEXT,
            price REAL,
            is_return_eligible INTEGER, -- SQLite uses 1 (True) or 0 (False)
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        )
    """)

    # 4. Shipments Table
    cursor.execute("""
        CREATE TABLE shipments (
            tracking_number TEXT PRIMARY KEY,
            order_id TEXT,
            carrier TEXT,
            status TEXT,          -- e.g., In Transit, Delivered, Delayed, Damaged, Lost
            current_location TEXT,
            estimated_delivery TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database schema created successfully in {DB_NAME}!")

if __name__ == "__main__":
    setup_database()
