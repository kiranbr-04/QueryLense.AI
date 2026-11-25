import os
import sqlite3
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "ecommerce_sample.db")

def create_sample_database():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Departments
    cursor.execute("""
    CREATE TABLE departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        budget REAL NOT NULL,
        location TEXT NOT NULL
    );
    """)

    departments_data = [
        ("Engineering", 1200000.0, "Building A, Floor 3"),
        ("Sales & Marketing", 850000.0, "Building B, Floor 1"),
        ("Finance", 450000.0, "Building A, Floor 2"),
        ("Customer Support", 300000.0, "Building C, Floor 4"),
        ("Human Resources", 250000.0, "Building A, Floor 1"),
    ]
    cursor.executemany("INSERT INTO departments (name, budget, location) VALUES (?, ?, ?);", departments_data)

    # 2. Employees
    cursor.execute("""
    CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department_id INTEGER NOT NULL,
        salary REAL NOT NULL,
        role TEXT NOT NULL,
        hire_date TEXT NOT NULL,
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
    );
    """)

    employees_data = [
        ("Alice Chen", "alice.chen@enterprise.com", 1, 145000.0, "Lead Architect", "2021-03-15"),
        ("Marcus Vance", "marcus.v@enterprise.com", 1, 132000.0, "Senior Backend Engineer", "2022-01-10"),
        ("Sarah Jenkins", "sarah.j@enterprise.com", 2, 125000.0, "VP of Sales", "2020-06-01"),
        ("David Ross", "david.ross@enterprise.com", 3, 110000.0, "Financial Controller", "2019-11-20"),
        ("Elena Rostova", "elena.r@enterprise.com", 1, 98000.0, "Data Engineer", "2023-04-12"),
        ("James Wilson", "j.wilson@enterprise.com", 2, 75000.0, "Account Executive", "2022-08-01"),
        ("Priya Patel", "priya.p@enterprise.com", 4, 62000.0, "Support Team Lead", "2021-09-15"),
        ("Lucas Miller", "lucas.m@enterprise.com", 5, 68000.0, "HR Manager", "2020-02-14"),
        ("Sofia Ramirez", "sofia.r@enterprise.com", 2, 58000.0, "Marketing Specialist", "2023-02-01"),
        ("Kevin Zhao", "kevin.z@enterprise.com", 1, 88000.0, "Full Stack Developer", "2023-09-01"),
    ]
    cursor.executemany("""
    INSERT INTO employees (full_name, email, department_id, salary, role, hire_date)
    VALUES (?, ?, ?, ?, ?, ?);
    """, employees_data)

    # 3. Categories
    cursor.execute("""
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    );
    """)

    categories_data = [
        ("Electronics", "Laptops, phones, accessories, and audio gear"),
        ("Office Supplies", "Desks, chairs, stationery, and organizers"),
        ("Software Licenses", "Cloud services, productivity suites, and developer tools"),
    ]
    cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?);", categories_data)

    # 4. Products
    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        sku TEXT UNIQUE NOT NULL,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    );
    """)

    products_data = [
        (1, "Pro UltraBook 16-inch", "ELEC-PRO-16", 1899.99, 45, "in_stock"),
        (1, "Wireless ANC Headphones", "ELEC-HEAD-01", 249.50, 120, "in_stock"),
        (1, "4K Curved Monitor 32-inch", "ELEC-MON-32", 599.00, 30, "in_stock"),
        (1, "Mechanical Ergonomic Keyboard", "ELEC-KEY-08", 129.99, 15, "low_stock"),
        (2, "Ergonomic Standing Desk", "OFF-DESK-01", 450.00, 25, "in_stock"),
        (2, "Mesh High-Back Task Chair", "OFF-CHR-05", 280.00, 40, "in_stock"),
        (3, "Enterprise Cloud DB Subscription (Annual)", "SFT-CLD-YR", 3600.00, 999, "available"),
        (3, "AI Analytics Suite (Per Seat)", "SFT-ANL-ST", 480.00, 500, "available"),
    ]
    cursor.executemany("""
    INSERT INTO products (category_id, name, sku, price, stock_quantity, status)
    VALUES (?, ?, ?, ?, ?, ?);
    """, products_data)

    # 5. Customers
    cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        country TEXT NOT NULL,
        city TEXT NOT NULL,
        registered_at TEXT NOT NULL
    );
    """)

    customers_data = [
        ("Global Dynamics Corp", "procurement@globaldyn.com", "USA", "New York", "2023-01-15"),
        ("Apex BioTech Labs", "admin@apexbio.org", "USA", "Boston", "2023-03-22"),
        ("Nippon FinTech Solutions", "it@nipponfintech.jp", "Japan", "Tokyo", "2023-05-10"),
        ("Nordic Retail Group", "orders@nordicretail.se", "Sweden", "Stockholm", "2023-08-01"),
        ("Helios Solar Energy", "supplies@heliossolar.de", "Germany", "Munich", "2023-11-04"),
    ]
    cursor.executemany("""
    INSERT INTO customers (full_name, email, country, city, registered_at)
    VALUES (?, ?, ?, ?, ?);
    """, customers_data)

    # 6. Orders
    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        total_amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    orders_data = [
        (1, "2024-01-15", "completed", 5699.97, "wire_transfer"),
        (2, "2024-01-28", "completed", 1250.00, "credit_card"),
        (3, "2024-02-10", "completed", 7200.00, "wire_transfer"),
        (4, "2024-02-20", "completed", 2490.50, "credit_card"),
        (1, "2024-03-05", "completed", 8400.00, "wire_transfer"),
        (5, "2024-03-18", "completed", 1120.00, "paypal"),
        (2, "2024-04-02", "completed", 3600.00, "wire_transfer"),
        (3, "2024-04-19", "completed", 4500.00, "credit_card"),
        (4, "2024-05-01", "completed", 1899.99, "credit_card"),
        (5, "2024-05-15", "completed", 3799.98, "wire_transfer"),
    ]
    cursor.executemany("""
    INSERT INTO orders (customer_id, order_date, status, total_amount, payment_method)
    VALUES (?, ?, ?, ?, ?);
    """, orders_data)

    # 7. Order Items
    cursor.execute("""
    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    order_items_data = [
        (1, 1, 3, 1899.99),
        (2, 2, 5, 249.50),
        (3, 7, 2, 3600.00),
        (4, 3, 3, 599.00),
        (4, 2, 2, 249.50),
        (5, 7, 2, 3600.00),
        (5, 8, 2, 480.00),
        (6, 6, 4, 280.00),
        (7, 7, 1, 3600.00),
        (8, 5, 10, 450.00),
        (9, 1, 1, 1899.99),
        (10, 1, 2, 1899.99),
    ]
    cursor.executemany("""
    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    VALUES (?, ?, ?, ?);
    """, order_items_data)

    conn.commit()
    conn.close()
    print(f"Sample E-Commerce database created at: {DB_PATH}")

if __name__ == "__main__":
    create_sample_database()
