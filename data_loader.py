import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'practice.db')

CUSTOMERS = [
    (1, 'Alice Martin', 'Paris', '2022-01-15', 'gold'),
    (2, 'Bob Dupont', 'Lyon', '2022-03-20', 'silver'),
    (3, 'Claire Bernard', 'Paris', '2021-11-05', 'gold'),
    (4, 'David Moreau', 'Marseille', '2023-02-10', 'bronze'),
    (5, 'Emma Leroy', 'Bordeaux', '2022-07-30', 'silver'),
    (6, 'François Petit', 'Paris', '2021-08-12', 'gold'),
    (7, 'Gabrielle Simon', 'Lyon', '2023-04-05', 'bronze'),
    (8, 'Henri Dubois', 'Nantes', '2022-09-18', 'silver'),
    (9, 'Isabelle Richard', 'Strasbourg', '2021-12-01', 'gold'),
    (10, 'Jules Thomas', 'Paris', '2023-01-25', 'bronze'),
    (11, 'Karine Robert', 'Toulouse', '2022-05-14', 'silver'),
    (12, 'Luc Blanc', 'Nice', '2023-06-08', 'bronze'),
    (13, 'Marie Garnier', 'Paris', '2022-11-30', 'gold'),
    (14, 'Nicolas Faure', 'Rennes', '2023-03-17', 'bronze'),
    (15, 'Olivia Mercier', 'Lyon', '2022-08-22', 'silver'),
]

PRODUCTS = [
    (1, 'Laptop Pro', 'Electronics', 1299.99),
    (2, 'Wireless Mouse', 'Electronics', 29.99),
    (3, 'USB Hub', 'Electronics', 49.99),
    (4, 'T-Shirt Basic', 'Clothing', 19.99),
    (5, 'Jean Slim', 'Clothing', 59.99),
    (6, 'Jacket Winter', 'Clothing', 149.99),
    (7, 'Coffee Beans 1kg', 'Food', 12.99),
    (8, 'Olive Oil 1L', 'Food', 8.99),
    (9, 'Chocolate Box', 'Food', 15.99),
    (10, 'Monitor 27"', 'Electronics', 399.99),
    (11, 'Keyboard Mech', 'Electronics', 89.99),
    (12, 'Sneakers', 'Clothing', 79.99),
]

ORDERS = [
    (1,  1,  1,  1, '2022-02-10', 'completed'),
    (2,  1,  2,  2, '2022-02-10', 'completed'),
    (3,  1,  10, 1, '2022-05-15', 'completed'),
    (4,  1,  11, 1, '2022-05-15', 'completed'),
    (5,  1,  6,  2, '2023-01-20', 'completed'),
    (6,  2,  4,  3, '2022-04-05', 'completed'),
    (7,  2,  5,  1, '2022-04-05', 'completed'),
    (8,  2,  12, 2, '2022-08-12', 'completed'),
    (9,  2,  7,  5, '2023-02-28', 'completed'),
    (10, 2,  1,  1, '2023-06-10', 'completed'),
    (11, 3,  1,  2, '2022-01-08', 'completed'),
    (12, 3,  10, 1, '2022-06-20', 'completed'),
    (13, 3,  11, 1, '2022-06-20', 'completed'),
    (14, 3,  3,  2, '2023-03-15', 'completed'),
    (15, 4,  4,  2, '2023-03-01', 'completed'),
    (16, 4,  8,  3, '2023-03-01', 'completed'),
    (17, 4,  9,  2, '2023-05-10', 'pending'),
    (18, 5,  6,  1, '2022-08-05', 'completed'),
    (19, 5,  12, 1, '2022-08-05', 'completed'),
    (20, 5,  5,  2, '2023-01-15', 'completed'),
    (21, 5,  7,  3, '2023-04-20', 'completed'),
    (22, 6,  1,  1, '2021-09-01', 'completed'),
    (23, 6,  2,  3, '2021-09-01', 'completed'),
    (24, 6,  10, 2, '2022-03-10', 'completed'),
    (25, 6,  3,  1, '2022-11-20', 'completed'),
    (26, 7,  4,  5, '2023-05-01', 'completed'),
    (27, 7,  8,  2, '2023-05-01', 'cancelled'),
    (28, 8,  5,  3, '2022-10-05', 'completed'),
    (29, 8,  9,  4, '2022-10-05', 'completed'),
    (30, 8,  11, 1, '2023-03-22', 'pending'),
    (31, 9,  1,  1, '2022-01-20', 'completed'),
    (32, 9,  6,  3, '2022-04-15', 'completed'),
    (33, 9,  10, 1, '2023-01-05', 'completed'),
    (34, 9,  2,  2, '2023-05-18', 'completed'),
    (35, 10, 4,  4, '2023-02-14', 'completed'),
    (36, 10, 7,  3, '2023-02-14', 'completed'),
    (37, 10, 9,  2, '2023-07-01', 'pending'),
    (38, 11, 12, 2, '2022-06-10', 'completed'),
    (39, 11, 5,  1, '2023-04-08', 'completed'),
    (40, 12, 4,  3, '2023-07-15', 'completed'),
    (41, 12, 8,  2, '2023-07-15', 'cancelled'),
    (42, 13, 1,  1, '2022-12-05', 'completed'),
    (43, 13, 11, 2, '2022-12-05', 'completed'),
    (44, 13, 3,  3, '2023-05-25', 'completed'),
    (45, 15, 6,  2, '2022-09-10', 'completed'),
    (46, 15, 12, 1, '2022-09-10', 'completed'),
    (47, 15, 2,  4, '2023-02-20', 'completed'),
    (48, 3,  9,  3, '2023-08-01', 'completed'),
    (49, 6,  11, 1, '2023-07-15', 'completed'),
    (50, 9,  7,  5, '2023-06-28', 'completed'),
]

EMPLOYEES = [
    (1, 'Sophie Laurent',   'Management',  None, 8500.00),
    (2, 'Thomas Girard',    'Sales',       1,    5200.00),
    (3, 'Amélie Rousseau',  'Engineering', 1,    6800.00),
    (4, 'Pierre Lefebvre',  'Marketing',   1,    5800.00),
    (5, 'Camille Morel',    'Sales',       2,    3800.00),
    (6, 'Lucas Fournier',   'Sales',       2,    3600.00),
    (7, 'Mathilde Legrand', 'Engineering', 3,    4900.00),
    (8, 'Antoine Bonnet',   'Engineering', 3,    5100.00),
]

MONTHLY_SALES = [
    (2021, 1,  15230.50, 45),  (2021, 2,  18450.00, 52),
    (2021, 3,  22100.75, 68),  (2021, 4,  19800.25, 58),
    (2021, 5,  21500.00, 63),  (2021, 6,  25300.50, 78),
    (2021, 7,  28700.00, 89),  (2021, 8,  26500.25, 82),
    (2021, 9,  23400.00, 71),  (2021, 10, 31200.75, 95),
    (2021, 11, 42500.00, 130), (2021, 12, 55000.25, 168),
    (2022, 1,  18900.00, 55),  (2022, 2,  22300.50, 67),
    (2022, 3,  26700.75, 82),  (2022, 4,  24500.00, 74),
    (2022, 5,  27800.25, 85),  (2022, 6,  31200.00, 96),
    (2022, 7,  35400.50, 109), (2022, 8,  32100.75, 99),
    (2022, 9,  28900.00, 88),  (2022, 10, 38700.25, 118),
    (2022, 11, 52300.00, 160), (2022, 12, 67500.50, 206),
    (2023, 1,  22100.00, 67),  (2023, 2,  26500.75, 81),
    (2023, 3,  31800.00, 97),  (2023, 4,  29200.50, 89),
    (2023, 5,  33500.25, 102), (2023, 6,  38100.00, 116),
    (2023, 7,  42700.75, 130), (2023, 8,  39500.00, 121),
    (2023, 9,  35200.50, 107), (2023, 10, 46800.25, 143),
    (2023, 11, 63200.00, 193), (2023, 12, 82500.75, 252),
]


def initialize():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            signup_date TEXT NOT NULL,
            tier TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            manager_id INTEGER,
            salary REAL NOT NULL,
            FOREIGN KEY (manager_id) REFERENCES employees(id)
        );
        CREATE TABLE IF NOT EXISTS monthly_sales (
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            revenue REAL NOT NULL,
            units_sold INTEGER NOT NULL,
            PRIMARY KEY (year, month)
        );
    """)

    # Only insert if tables are empty
    if c.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        c.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", CUSTOMERS)
    if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        c.executemany("INSERT INTO products VALUES (?,?,?,?)", PRODUCTS)
    if c.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
        c.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", ORDERS)
    if c.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
        c.executemany("INSERT INTO employees VALUES (?,?,?,?,?)", EMPLOYEES)
    if c.execute("SELECT COUNT(*) FROM monthly_sales").fetchone()[0] == 0:
        c.executemany("INSERT INTO monthly_sales VALUES (?,?,?,?)", MONTHLY_SALES)

    conn.commit()
    conn.close()


def get_dataframes():
    customers = pd.DataFrame(CUSTOMERS, columns=['id', 'name', 'city', 'signup_date', 'tier'])
    products = pd.DataFrame(PRODUCTS, columns=['id', 'name', 'category', 'unit_price'])
    orders = pd.DataFrame(ORDERS, columns=['id', 'customer_id', 'product_id', 'quantity', 'order_date', 'status'])
    employees = pd.DataFrame(EMPLOYEES, columns=['id', 'name', 'department', 'manager_id', 'salary'])
    monthly_sales = pd.DataFrame(MONTHLY_SALES, columns=['year', 'month', 'revenue', 'units_sold'])

    customers['signup_date'] = pd.to_datetime(customers['signup_date'])
    orders['order_date'] = pd.to_datetime(orders['order_date'])

    return {
        'customers': customers,
        'products': products,
        'orders': orders,
        'employees': employees,
        'monthly_sales': monthly_sales,
    }
