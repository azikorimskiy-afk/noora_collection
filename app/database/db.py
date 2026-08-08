
import sqlite3
from pathlib import Path


DB_PATH = Path("shop.db")


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_connection():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# ==================================================
# DATABASE INIT
# ==================================================

def init_db():

    conn = get_connection()

    # ------------------------------
    # PRODUCTS
    # ------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            image TEXT,
            stock INTEGER DEFAULT 0
        )
    """)

    # ------------------------------
    # CUSTOMERS
    # ------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            name TEXT,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------------------------------
    # ORDERS
    # ------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            total INTEGER NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------------------------------
    # ORDER ITEMS
    # ------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,

            FOREIGN KEY (order_id)
            REFERENCES orders(id)
        )
    """)

    conn.commit()

    conn.close()


# ==================================================
# PRODUCTS
# ==================================================

def get_products():

    conn = get_connection()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id"
    ).fetchall()

    conn.close()

    return products


def get_product(product_id):

    conn = get_connection()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE product_id = ?
        """,
        (product_id,)
    ).fetchone()

    conn.close()

    return product


def add_product(
    product_id,
    name,
    price,
    description,
    image,
    stock,
):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO products
        (
            product_id,
            name,
            price,
            description,
            image,
            stock
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            name,
            price,
            description,
            image,
            stock,
        )
    )

    conn.commit()

    conn.close()


def update_product(
    product_id,
    name,
    price,
    description,
    image,
    stock,
):

    conn = get_connection()

    conn.execute(
        """
        UPDATE products
        SET
            name = ?,
            price = ?,
            description = ?,
            image = ?,
            stock = ?
        WHERE product_id = ?
        """,
        (
            name,
            price,
            description,
            image,
            stock,
            product_id,
        )
    )

    conn.commit()

    conn.close()


def delete_product(product_id):

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM products
        WHERE product_id = ?
        """,
        (product_id,)
    )

    conn.commit()

    conn.close()


# ==================================================
# CUSTOMER
# ==================================================

def save_customer(
    telegram_id,
    name,
    phone,
    address,
):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO customers
        (
            telegram_id,
            name,
            phone,
            address
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            name = excluded.name,
            phone = excluded.phone,
            address = excluded.address
        """,
        (
            telegram_id,
            name,
            phone,
            address,
        )
    )

    conn.commit()

    conn.close()


# ==================================================
# CREATE ORDER
# ==================================================

def create_order(
    telegram_id,
    name,
    phone,
    address,
    total,
    items,
):

    conn = get_connection()

    cursor = conn.cursor()

    # ------------------------------
    # ORDER
    # ------------------------------

    cursor.execute(
        """
        INSERT INTO orders
        (
            telegram_id,
            name,
            phone,
            address,
            total,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            name,
            phone,
            address,
            total,
            "new",
        )
    )

    order_id = cursor.lastrowid

    # ------------------------------
    # ORDER ITEMS
    # ------------------------------

    for item in items:

        cursor.execute(
            """
            INSERT INTO order_items
            (
                order_id,
                product_id,
                product_name,
                price,
                quantity,
                subtotal
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item["product_id"],
                item["name"],
                item["price"],
                item["quantity"],
                item["subtotal"],
            )
        )

        # ------------------------------
        # STOCK AYIRISH
        # ------------------------------

        cursor.execute(
            """
            UPDATE products
            SET stock = stock - ?
            WHERE product_id = ?
            AND stock >= ?
            """,
            (
                item["quantity"],
                item["product_id"],
                item["quantity"],
            )
        )

    conn.commit()

    conn.close()

    return order_id


# ==================================================
# GET ORDER
# ==================================================

def get_order(order_id):

    conn = get_connection()

    order = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    ).fetchone()

    conn.close()

    return order


# ==================================================
# GET ORDER ITEMS
# ==================================================

def get_order_items(order_id):

    conn = get_connection()

    items = conn.execute(
        """
        SELECT *
        FROM order_items
        WHERE order_id = ?
        ORDER BY id
        """,
        (order_id,)
    ).fetchall()

    conn.close()

    return items


# ==================================================
# GET ALL ORDERS
# ==================================================

def get_orders():

    conn = get_connection()

    orders = conn.execute(
        """
        SELECT *
        FROM orders
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return orders


# ==================================================
# UPDATE ORDER STATUS
# ==================================================

def update_order_status(
    order_id,
    status,
):

    conn = get_connection()

    conn.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            order_id,
        )
    )

    conn.commit()

    conn.close()


# ==================================================
# CUSTOMERS
# ==================================================

def get_customers():

    conn = get_connection()

    customers = conn.execute(
        """
        SELECT *
        FROM customers
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return customers


# ==================================================
# STATISTICS
# ==================================================

def get_statistics():

    conn = get_connection()

    products_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM products
        """
    ).fetchone()[0]

    customers_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM customers
        """
    ).fetchone()[0]

    orders_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM orders
        """
    ).fetchone()[0]

    delivered_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'delivered'
        """
    ).fetchone()[0]

    total_revenue = conn.execute(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM orders
        WHERE status = 'delivered'
        """
    ).fetchone()[0]

    conn.close()

    return {
        "products": products_count,
        "customers": customers_count,
        "orders": orders_count,
        "delivered": delivered_count,
        "revenue": total_revenue,
    }
