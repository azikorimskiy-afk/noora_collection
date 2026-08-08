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
                stock INTEGER NOT NULL DEFAULT 0
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
                status TEXT NOT NULL DEFAULT 'new',
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

        # ====================================================
        # CARTS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # CART ITEMS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id SERIAL PRIMARY KEY,
                cart_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,

                UNIQUE (cart_id, product_id),

                FOREIGN KEY (cart_id)
                REFERENCES carts(id)
                ON DELETE CASCADE,

                FOREIGN KEY (product_id)
                REFERENCES products(product_id)
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
    description=None,
    image=None,
    stock=0,
):

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO products (
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
    name=None,
    phone=None,
    address=None,
):

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO customers (
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

        cursor = conn.execute("""
            INSERT INTO orders (
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
                INSERT INTO order_items (
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


def update_order_status(order_id, status):

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
# CARTS
# ============================================================

def get_or_create_cart(telegram_id):

    conn = get_connection()

    try:

        cart = conn.execute("""
            SELECT *
            FROM carts
            WHERE telegram_id = %s
        """, (telegram_id,)).fetchone()

        if cart:

            return cart

        cart = conn.execute("""
            INSERT INTO carts (telegram_id)
            VALUES (%s)
            RETURNING *
        """, (telegram_id,)).fetchone()

        conn.commit()

        return cart

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


def get_cart(telegram_id):

    conn = get_connection()

    try:

        cart = conn.execute("""
            SELECT
                carts.id AS cart_id,
                cart_items.product_id,
                cart_items.quantity
            FROM carts
            LEFT JOIN cart_items
                ON carts.id = cart_items.cart_id
            WHERE carts.telegram_id = %s
            ORDER BY cart_items.id
        """, (telegram_id,)).fetchall()

        result = {}

        for item in cart:

            if item["product_id"] is not None:

                result[item["product_id"]] = item["quantity"]

        return result

    finally:

        conn.close()


def add_to_cart(
    telegram_id,
    product_id,
    quantity=1,
):

    conn = get_connection()

    try:

        cart = conn.execute("""
            SELECT id
            FROM carts
            WHERE telegram_id = %s
        """, (telegram_id,)).fetchone()

        if not cart:

            cart = conn.execute("""
                INSERT INTO carts (telegram_id)
                VALUES (%s)
                RETURNING id
            """, (telegram_id,)).fetchone()

        cart_id = cart["id"]

        product = conn.execute("""
            SELECT stock
            FROM products
            WHERE product_id = %s
        """, (product_id,)).fetchone()

        if not product:

            raise ValueError(
                "Mahsulot topilmadi."
            )

        current = conn.execute("""
            SELECT quantity
            FROM cart_items
            WHERE cart_id = %s
            AND product_id = %s
        """, (
            cart_id,
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

        if new_quantity > product["stock"]:

            raise ValueError(
                "Omborda yetarli mahsulot yo‘q."
            )

        conn.execute("""
            INSERT INTO cart_items (
                cart_id,
                product_id,
                quantity
            )
            VALUES (%s, %s, %s)

            ON CONFLICT (cart_id, product_id)
            DO UPDATE SET
                quantity = EXCLUDED.quantity
        """, (
            cart_id,
            product_id,
            new_quantity,
        ))

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


def set_cart_quantity(
    telegram_id,
    product_id,
    quantity,
):

    conn = get_connection()

    try:

        cart = conn.execute("""
            SELECT id
            FROM carts
            WHERE telegram_id = %s
        """, (telegram_id,)).fetchone()

        if not cart:

            if quantity <= 0:
                return

            cart = conn.execute("""
                INSERT INTO carts (telegram_id)
                VALUES (%s)
                RETURNING id
            """, (telegram_id,)).fetchone()

        cart_id = cart["id"]

        if quantity <= 0:

            conn.execute("""
                DELETE FROM cart_items
                WHERE cart_id = %s
                AND product_id = %s
            """, (
                cart_id,
                product_id,
            ))

        else:

            product = conn.execute("""
                SELECT stock
                FROM products
                WHERE product_id = %s
            """, (product_id,)).fetchone()

            if not product:

                raise ValueError(
                    "Mahsulot topilmadi."
                )

            if quantity > product["stock"]:

                raise ValueError(
                    "Omborda yetarli mahsulot yo‘q."
                )

            conn.execute("""
                INSERT INTO cart_items (
                    cart_id,
                    product_id,
                    quantity
                )
                VALUES (%s, %s, %s)

                ON CONFLICT (cart_id, product_id)
                DO UPDATE SET
                    quantity = EXCLUDED.quantity
            """, (
                cart_id,
                product_id,
                quantity,
            ))

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


def remove_from_cart(
    telegram_id,
    product_id,
):

    set_cart_quantity(
        telegram_id,
        product_id,
        0,
    )


def clear_cart(telegram_id):

    conn = get_connection()

    try:

        cart = conn.execute("""
            SELECT id
            FROM carts
            WHERE telegram_id = %s
        """, (telegram_id,)).fetchone()

        if cart:

            conn.execute("""
                DELETE FROM cart_items
                WHERE cart_id = %s
            """, (cart["id"],))

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

        total_revenue = conn.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM orders
            WHERE status = 'delivered'
        """).fetchone()["coalesce"]

        return {
            "products": products_count,
            "customers": customers_count,
            "orders": orders_count,
            "delivered": delivered_count,
            "revenue": total_revenue,
        }

    finally:

        conn.close()
