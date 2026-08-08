
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

                price BIGINT NOT NULL DEFAULT 0,

                description TEXT,

                image TEXT,

                stock INTEGER NOT NULL DEFAULT 0,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

                total BIGINT NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'new',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        # ====================================================
        # CART ITEMS
        #
        # PostgreSQL'dagi doimiy savatcha.
        # Bot restart bo'lsa ham saqlanadi.
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id SERIAL PRIMARY KEY,

                telegram_id BIGINT NOT NULL,

                product_id TEXT NOT NULL,

                quantity INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (telegram_id, product_id),

                FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE CASCADE
            )
        """)

        # ====================================================
        # INDEXLAR
        # ====================================================

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_telegram_id
            ON orders(telegram_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_status
            ON orders(status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_items_order_id
            ON order_items(order_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cart_items_telegram_id
            ON cart_items(telegram_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_product_id
            ON products(product_id)
        """)

        conn.commit()

        print("======================================")
        print("✅ PostgreSQL DATABASE TAYYOR!")
        print("======================================")
        print("✅ products")
        print("✅ customers")
        print("✅ orders")
        print("✅ order_items")
        print("✅ cart_items")
        print("✅ indexes")
        print("======================================")

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

        products = conn.execute("""
            SELECT *
            FROM products
            ORDER BY id ASC
        """).fetchall()

        return products

    finally:

        conn.close()


# ============================================================

def get_product(product_id):

    conn = get_connection()

    try:

        product = conn.execute("""
            SELECT *
            FROM products
            WHERE product_id = %s
        """, (
            product_id,
        )).fetchone()

        return product

    finally:

        conn.close()


# ============================================================

def add_product(
    product_id,
    name,
    price,
    description=None,
    image=None,
    stock=0,
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


# ============================================================

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


# ============================================================

def delete_product(product_id):

    conn = get_connection()

    try:

        conn.execute("""
            DELETE FROM products
            WHERE product_id = %s
        """, (
            product_id,
        ))

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

                address = EXCLUDED.address,

                updated_at = CURRENT_TIMESTAMP
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


# ============================================================

def get_customer(telegram_id):

    conn = get_connection()

    try:

        customer = conn.execute("""
            SELECT *
            FROM customers
            WHERE telegram_id = %s
        """, (
            telegram_id,
        )).fetchone()

        return customer

    finally:

        conn.close()


# ============================================================

def get_customers():

    conn = get_connection()

    try:

        customers = conn.execute("""
            SELECT *
            FROM customers
            ORDER BY id DESC
        """).fetchall()

        return customers

    finally:

        conn.close()


# ============================================================
# ORDERS
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

        # ====================================================
        # ORDER YARATISH
        # ====================================================

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

        # ====================================================
        # ORDER ITEMS
        # ====================================================

        for item in items:

            product_id = item["product_id"]

            quantity = int(
                item["quantity"]
            )

            # -----------------------------------------------
            # STOCKNI ATOMIK KAMAYTIRISH
            # -----------------------------------------------

            result = conn.execute("""
                UPDATE products

                SET stock = stock - %s

                WHERE product_id = %s

                AND stock >= %s

                RETURNING stock
            """, (
                quantity,
                product_id,
                quantity,
            )).fetchone()

            if not result:

                raise ValueError(
                    f"Mahsulot qoldig'i yetarli emas: "
                    f"{product_id}"
                )

            # -----------------------------------------------
            # ORDER ITEM
            # -----------------------------------------------

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
                product_id,
                item["name"],
                item["price"],
                quantity,
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

def get_order(order_id):

    conn = get_connection()

    try:

        order = conn.execute("""
            SELECT *
            FROM orders
            WHERE id = %s
        """, (
            order_id,
        )).fetchone()

        return order

    finally:

        conn.close()


# ============================================================

def get_order_items(order_id):

    conn = get_connection()

    try:

        items = conn.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = %s
            ORDER BY id ASC
        """, (
            order_id,
        )).fetchall()

        return items

    finally:

        conn.close()


# ============================================================

def get_orders():

    conn = get_connection()

    try:

        orders = conn.execute("""
            SELECT *
            FROM orders
            ORDER BY id DESC
        """).fetchall()

        return orders

    finally:

        conn.close()


# ============================================================

def get_user_orders(telegram_id):

    conn = get_connection()

    try:

        orders = conn.execute("""
            SELECT *
            FROM orders
            WHERE telegram_id = %s
            ORDER BY id DESC
        """, (
            telegram_id,
        )).fetchall()

        return orders

    finally:

        conn.close()


# ============================================================

def update_order_status(
    order_id,
    status,
):

    conn = get_connection()

    try:

        conn.execute("""
            UPDATE orders

            SET
                status = %s,
                updated_at = CURRENT_TIMESTAMP

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
# ORDER CANCEL + STOCK RESTORE
# ============================================================

def cancel_order(order_id):

    conn = get_connection()

    try:

        order = conn.execute("""
            SELECT status
            FROM orders
            WHERE id = %s
        """, (
            order_id,
        )).fetchone()

        if not order:

            raise ValueError(
                "Buyurtma topilmadi."
            )

        # -----------------------------------------------
        # Allaqachon bekor qilingan bo'lsa
        # stockni qaytarmaymiz.
        # -----------------------------------------------

        if order["status"] == "cancelled":

            conn.rollback()

            return False

        # -----------------------------------------------
        # ORDER ITEMS
        # -----------------------------------------------

        items = conn.execute("""
            SELECT
                product_id,
                quantity
            FROM order_items
            WHERE order_id = %s
        """, (
            order_id,
        )).fetchall()

        # -----------------------------------------------
        # STOCKNI QAYTARISH
        # -----------------------------------------------

        for item in items:

            conn.execute("""
                UPDATE products

                SET stock = stock + %s

                WHERE product_id = %s
            """, (
                item["quantity"],
                item["product_id"],
            ))

        # -----------------------------------------------
        # STATUS
        # -----------------------------------------------

        conn.execute("""
            UPDATE orders

            SET
                status = 'cancelled',
                updated_at = CURRENT_TIMESTAMP

            WHERE id = %s
        """, (
            order_id,
        ))

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# CART — GET
# ============================================================

def get_cart(telegram_id):

    conn = get_connection()

    try:

        cart = conn.execute("""
            SELECT
                product_id,
                quantity
            FROM cart_items

            WHERE telegram_id = %s

            ORDER BY id ASC
        """, (
            telegram_id,
        )).fetchall()

        return {
            item["product_id"]: item["quantity"]
            for item in cart
        }

    finally:

        conn.close()


# ============================================================
# CART — ADD
# ============================================================

def add_to_cart(
    telegram_id,
    product_id,
    quantity=1,
):

    conn = get_connection()

    try:

        # -----------------------------------------------
        # PRODUCT
        # -----------------------------------------------

        product = conn.execute("""
            SELECT stock
            FROM products
            WHERE product_id = %s
        """, (
            product_id,
        )).fetchone()

        if not product:

            raise ValueError(
                "Mahsulot topilmadi."
            )

        stock = product["stock"]

        # -----------------------------------------------
        # CURRENT CART
        # -----------------------------------------------

        current = conn.execute("""
            SELECT quantity
            FROM cart_items

            WHERE telegram_id = %s
            AND product_id = %s
        """, (
            telegram_id,
            product_id,
        )).fetchone()

        current_quantity = (
            current["quantity"]
            if current
            else 0
        )

        new_quantity = (
            current_quantity + quantity
        )

        # -----------------------------------------------
        # STOCK CHECK
        # -----------------------------------------------

        if new_quantity > stock:

            raise ValueError(
                "❌ Omborda yetarli mahsulot yo‘q."
            )

        # -----------------------------------------------
        # INSERT / UPDATE
        # -----------------------------------------------

        conn.execute("""
            INSERT INTO cart_items
            (
                telegram_id,
                product_id,
                quantity
            )

            VALUES (%s, %s, %s)

            ON CONFLICT
            (
                telegram_id,
                product_id
            )

            DO UPDATE SET

                quantity = EXCLUDED.quantity,

                updated_at = CURRENT_TIMESTAMP
        """, (
            telegram_id,
            product_id,
            new_quantity,
        ))

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# CART — SET QUANTITY
# ============================================================

def set_cart_quantity(
    telegram_id,
    product_id,
    quantity,
):

    conn = get_connection()

    try:

        # -----------------------------------------------
        # 0 yoki undan kam = DELETE
        # -----------------------------------------------

        if quantity <= 0:

            conn.execute("""
                DELETE FROM cart_items

                WHERE telegram_id = %s
                AND product_id = %s
            """, (
                telegram_id,
                product_id,
            ))

        else:

            # -------------------------------------------
            # PRODUCT
            # -------------------------------------------

            product = conn.execute("""
                SELECT stock
                FROM products
                WHERE product_id = %s
            """, (
                product_id,
            )).fetchone()

            if not product:

                raise ValueError(
                    "Mahsulot topilmadi."
                )

            # -------------------------------------------
            # STOCK
            # -------------------------------------------

            if quantity > product["stock"]:

                raise ValueError(
                    "❌ Omborda yetarli mahsulot yo‘q."
                )

            # -------------------------------------------
            # INSERT / UPDATE
            # -------------------------------------------

            conn.execute("""
                INSERT INTO cart_items
                (
                    telegram_id,
                    product_id,
                    quantity
                )

                VALUES (%s, %s, %s)

                ON CONFLICT
                (
                    telegram_id,
                    product_id
                )

                DO UPDATE SET

                    quantity = EXCLUDED.quantity,

                    updated_at = CURRENT_TIMESTAMP
            """, (
                telegram_id,
                product_id,
                quantity,
            ))

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# CART — REMOVE ONE PRODUCT
# ============================================================

def remove_from_cart(
    telegram_id,
    product_id,
):

    conn = get_connection()

    try:

        conn.execute("""
            DELETE FROM cart_items

            WHERE telegram_id = %s
            AND product_id = %s
        """, (
            telegram_id,
            product_id,
        ))

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# CART — CLEAR
# ============================================================

def clear_cart(telegram_id):

    conn = get_connection()

    try:

        conn.execute("""
            DELETE FROM cart_items

            WHERE telegram_id = %s
        """, (
            telegram_id,
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

    conn = get_connection()

    try:

        products_count = conn.execute("""
            SELECT COUNT(*)
            FROM products
        """).fetchone()["count"]

        customers_count = conn.execute("""
            SELECT COUNT(*)
            FROM customers
        """).fetchone()["count"]

        orders_count = conn.execute("""
            SELECT COUNT(*)
            FROM orders
        """).fetchone()["count"]

        delivered_count = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status = 'delivered'
        """).fetchone()["count"]

        cancelled_count = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status = 'cancelled'
        """).fetchone()["count"]

        new_orders_count = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status = 'new'
        """).fetchone()["count"]

        accepted_count = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status = 'accepted'
        """).fetchone()["count"]

        delivery_count = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status = 'delivery'
        """).fetchone()["count"]

        total_revenue = conn.execute("""
            SELECT COALESCE(
                SUM(total),
                0
            )

            FROM orders

            WHERE status = 'delivered'
        """).fetchone()["coalesce"]

        return {
            "products": products_count,
            "customers": customers_count,
            "orders": orders_count,
            "new": new_orders_count,
            "accepted": accepted_count,
            "delivery": delivery_count,
            "delivered": delivered_count,
            "cancelled": cancelled_count,
            "revenue": total_revenue,
        }

    finally:

        conn.close()
