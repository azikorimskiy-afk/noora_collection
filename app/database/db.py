
import os
import psycopg
from psycopg.rows import dict_row


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "❌ DATABASE_URL Railway Variables'da topilmadi!"
        )

    return psycopg.connect(
        database_url,
        row_factory=dict_row,
    )


# ==================================================
# DATABASE INIT
# ==================================================

def init_db():
    conn = get_connection()

    with conn.cursor() as cursor:

        # ------------------------------
        # PRODUCTS
        # ------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id BIGSERIAL PRIMARY KEY,
                product_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price BIGINT NOT NULL,
                description TEXT,
                image TEXT,
                stock INTEGER DEFAULT 0
            )
        """)

        # ------------------------------
        # CUSTOMERS
        # ------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                name TEXT,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ------------------------------
        # ORDERS
        # ------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                total BIGINT NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ------------------------------
        # ORDER ITEMS
        # ------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id BIGSERIAL PRIMARY KEY,
                order_id BIGINT NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                price BIGINT NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal BIGINT NOT NULL,

                FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE
            )
        """)

        # ------------------------------
        # CARTS
        # ------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL
            )
        """)

        # ------------------------------
        # CART ITEMS
        # ------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,

                UNIQUE (telegram_id, product_id)
            )
        """)

    conn.commit()
    conn.close()


# ==================================================
# PRODUCTS
# ==================================================

def get_products():
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM products
            ORDER BY id
        """)

        products = cursor.fetchall()

    conn.close()

    return products


def get_product(product_id):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM products
            WHERE product_id = %s
        """, (product_id,))

        product = cursor.fetchone()

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

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO products
                (
                    product_id,
                    name,
                    price,
                    description,
                    image,
                    stock
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                product_id,
                name,
                price,
                description,
                image,
                stock,
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
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

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE products
                SET
                    name = %s,
                    price = %s,
                    description = %s,
                    image = %s,
                    stock = %s
                WHERE product_id = %s
            """, (
                name,
                price,
                description,
                image,
                stock,
                product_id,
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def delete_product(product_id):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM products
                WHERE product_id = %s
            """, (product_id,))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
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

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO customers
                (
                    telegram_id,
                    name,
                    phone,
                    address
                )
                VALUES (%s, %s, %s, %s)

                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone,
                    address = EXCLUDED.address
            """, (
                telegram_id,
                name,
                phone,
                address,
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
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

    try:
        with conn.cursor() as cursor:

            # ------------------------------
            # CUSTOMER
            # ------------------------------

            cursor.execute("""
                INSERT INTO customers
                (
                    telegram_id,
                    name,
                    phone,
                    address
                )
                VALUES (%s, %s, %s, %s)

                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone,
                    address = EXCLUDED.address
            """, (
                telegram_id,
                name,
                phone,
                address,
            ))

            # ------------------------------
            # ORDER
            # ------------------------------

            cursor.execute("""
                INSERT INTO orders
                (
                    telegram_id,
                    name,
                    phone,
                    address,
                    total,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                telegram_id,
                name,
                phone,
                address,
                total,
                "new",
            ))

            order_id = cursor.fetchone()["id"]

            # ------------------------------
            # ORDER ITEMS + STOCK
            # ------------------------------

            for item in items:

                cursor.execute("""
                    UPDATE products
                    SET stock = stock - %s
                    WHERE product_id = %s
                    AND stock >= %s
                    RETURNING product_id
                """, (
                    item["quantity"],
                    item["product_id"],
                    item["quantity"],
                ))

                updated = cursor.fetchone()

                if not updated:
                    raise ValueError(
                        f"Mahsulot qoldig'i yetarli emas: "
                        f"{item['product_id']}"
                    )

                cursor.execute("""
                    INSERT INTO order_items
                    (
                        order_id,
                        product_id,
                        product_name,
                        price,
                        quantity,
                        subtotal
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    order_id,
                    item["product_id"],
                    item["name"],
                    item["price"],
                    item["quantity"],
                    item["subtotal"],
                ))

        conn.commit()

        return order_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==================================================
# GET ORDER
# ==================================================

def get_order(order_id):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM orders
            WHERE id = %s
        """, (order_id,))

        order = cursor.fetchone()

    conn.close()

    return order


# ==================================================
# GET ORDER ITEMS
# ==================================================

def get_order_items(order_id):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = %s
            ORDER BY id
        """, (order_id,))

        items = cursor.fetchall()

    conn.close()

    return items


# ==================================================
# GET ALL ORDERS
# ==================================================

def get_orders():
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM orders
            ORDER BY id DESC
        """)

        orders = cursor.fetchall()

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

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE orders
                SET status = %s
                WHERE id = %s
            """, (
                status,
                order_id,
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==================================================
# CUSTOMERS
# ==================================================

def get_customers():
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM customers
            ORDER BY id DESC
        """)

        customers = cursor.fetchall()

    conn.close()

    return customers


# ==================================================
# STATISTICS
# ==================================================

def get_statistics():
    conn = get_connection()

    with conn.cursor() as cursor:

        cursor.execute("""
            SELECT COUNT(*)
            FROM products
        """)
        products_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT COUNT(*)
            FROM customers
        """)
        customers_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT COUNT(*)
            FROM orders
        """)
        orders_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status = 'delivered'
        """)
        delivered_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM orders
            WHERE status = 'delivered'
        """)
        total_revenue = cursor.fetchone()["coalesce"]

    conn.close()

    return {
        "products": products_count,
        "customers": customers_count,
        "orders": orders_count,
        "delivered": delivered_count,
        "revenue": total_revenue,
    }


# ==================================================
# CART
# ==================================================

def get_cart(user_id):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT product_id, quantity
            FROM cart_items
            WHERE telegram_id = %s
            ORDER BY id
        """, (user_id,))

        rows = cursor.fetchall()

    conn.close()

    return {
        row["product_id"]: row["quantity"]
        for row in rows
    }


def set_cart_quantity(
    user_id,
    product_id,
    quantity,
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            if quantity <= 0:
                cursor.execute("""
                    DELETE FROM cart_items
                    WHERE telegram_id = %s
                    AND product_id = %s
                """, (
                    user_id,
                    product_id,
                ))

            else:
                cursor.execute("""
                    INSERT INTO cart_items
                    (
                        telegram_id,
                        product_id,
                        quantity
                    )
                    VALUES (%s, %s, %s)

                    ON CONFLICT (telegram_id, product_id)
                    DO UPDATE SET
                        quantity = EXCLUDED.quantity
                """, (
                    user_id,
                    product_id,
                    quantity,
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def clear_cart(user_id):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM cart_items
                WHERE telegram_id = %s
            """, (user_id,))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
