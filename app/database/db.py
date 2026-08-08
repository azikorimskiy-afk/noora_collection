
import os
import psycopg
from psycopg.rows import dict_row


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL topilmadi! "
            "Railway Variables ichida DATABASE_URL mavjudligini tekshiring."
        )

    return psycopg.connect(
        database_url,
        row_factory=dict_row,
    )


# ============================================================
# DATABASE INIT
# ============================================================

def init_db():
    conn = get_connection()

    try:

        # ====================================================
        # PRODUCTS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                product_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price BIGINT NOT NULL,
                description TEXT,
                image TEXT,
                stock INTEGER DEFAULT 0
            )
        """)

        # ====================================================
        # CUSTOMERS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                name TEXT,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # ORDERS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                total BIGINT NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # ORDER ITEMS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL,
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

        conn.commit()

        print("✅ PostgreSQL database tayyor!")

    except Exception as e:
        conn.rollback()

        print(
            "❌ DATABASE INIT ERROR:",
            repr(e)
        )

        raise

    finally:
        conn.close()


# ============================================================
# PRODUCTS
# ============================================================

def get_products():
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM products
            ORDER BY id
        """).fetchall()

    finally:
        conn.close()


def get_product(product_id):
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM products
            WHERE product_id = %s
        """, (product_id,)).fetchone()

    finally:
        conn.close()


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
        conn.execute("""
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
        conn.execute("""
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
        conn.execute("""
            DELETE FROM products
            WHERE product_id = %s
        """, (product_id,))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ============================================================
# CUSTOMERS
# ============================================================

def save_customer(
    telegram_id,
    name,
    phone,
    address,
):
    conn = get_connection()

    try:
        conn.execute("""
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


def get_customer(telegram_id):
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM customers
            WHERE telegram_id = %s
        """, (telegram_id,)).fetchone()

    finally:
        conn.close()


def get_customers():
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM customers
            ORDER BY id DESC
        """).fetchall()

    finally:
        conn.close()


# ============================================================
# CREATE ORDER
# ============================================================

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

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        cursor = conn.execute("""
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

        # ----------------------------------------------------
        # ORDER ITEMS + STOCK
        # ----------------------------------------------------

        for item in items:

            result = conn.execute("""
                UPDATE products
                SET stock = stock - %s
                WHERE product_id = %s
                AND stock >= %s
                RETURNING stock
            """, (
                item["quantity"],
                item["product_id"],
                item["quantity"],
            )).fetchone()

            if not result:
                raise ValueError(
                    f"Mahsulot qoldig'i yetarli emas: "
                    f"{item['product_id']}"
                )

            conn.execute("""
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


# ============================================================
# GET ORDER
# ============================================================

def get_order(order_id):
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM orders
            WHERE id = %s
        """, (order_id,)).fetchone()

    finally:
        conn.close()


# ============================================================
# GET ORDER ITEMS
# ============================================================

def get_order_items(order_id):
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = %s
            ORDER BY id
        """, (order_id,)).fetchall()

    finally:
        conn.close()


# ============================================================
# GET ALL ORDERS
# ============================================================

def get_orders():
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM orders
            ORDER BY id DESC
        """).fetchall()

    finally:
        conn.close()


# ============================================================
# GET USER ORDERS
# ============================================================

def get_user_orders(telegram_id):
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM orders
            WHERE telegram_id = %s
            ORDER BY id DESC
        """, (telegram_id,)).fetchall()

    finally:
        conn.close()


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

def update_order_status(
    order_id,
    status,
):
    conn = get_connection()

    try:
        conn.execute("""
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


# ============================================================
# STATISTICS
# ============================================================

def get_statistics():
    """
    Admin panel uchun statistika.
    """

    try:
        products = get_products()
        customers = get_customers()
        orders = get_orders()

        products_count = len(products)
        customers_count = len(customers)
        orders_count = len(orders)

        delivered_count = 0
        total_revenue = 0

        for order in orders:

            status = order.get("status")

            if status == "delivered":

                delivered_count += 1

                total = order.get("total", 0)

                if total:
                    total_revenue += int(total)

        return {
            "products": products_count,
            "customers": customers_count,
            "orders": orders_count,
            "delivered": delivered_count,
            "revenue": total_revenue,
        }

    except Exception as e:

        print(
            "❌ GET STATISTICS ERROR:",
            repr(e),
        )

        return {
            "products": 0,
            "customers": 0,
            "orders": 0,
            "delivered": 0,
            "revenue": 0,
        }
    finally:
        conn.close()
