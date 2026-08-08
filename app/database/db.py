import sqlite3
from pathlib import Path


DB_PATH = Path("shop.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

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

    conn.commit()
    conn.close()


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
        "SELECT * FROM products WHERE product_id = ?",
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

    conn.execute("""
        INSERT INTO products
        (product_id, name, price, description, image, stock)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        product_id,
        name,
        price,
        description,
        image,
        stock,
    ))

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

    conn.execute("""
        UPDATE products
        SET name = ?,
            price = ?,
            description = ?,
            image = ?,
            stock = ?
        WHERE product_id = ?
    """, (
        name,
        price,
        description,
        image,
        stock,
        product_id,
    ))

    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()

    conn.execute(
        "DELETE FROM products WHERE product_id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()
