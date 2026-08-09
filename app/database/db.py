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
            "Hosting Variables ichida DATABASE_URL mavjudligini tekshiring."
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
                description TEXT,
                image TEXT,
                price BIGINT DEFAULT 0,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # PRODUCT VARIANTS
        # Har bir rang uchun alohida rasm, narx va qoldiq
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_variants (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL,
                color_name TEXT NOT NULL,
                color_code TEXT,
                image TEXT,
                price BIGINT NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE CASCADE
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

                variant_id INTEGER,
                color_name TEXT,

                price BIGINT NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal BIGINT NOT NULL,

                FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

                FOREIGN KEY (variant_id)
                REFERENCES product_variants(id)
                ON DELETE SET NULL
            )
        """)

        conn.commit()

        print("✅ PostgreSQL database tayyor!")

    except Exception as e:
        conn.rollback()
        print("❌ DATABASE INIT ERROR:", repr(e))
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
    description="",
    image=None,
    price=0,
    stock=0,
):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO products
            (
                product_id,
                name,
                description,
                image,
                price,
                stock
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            product_id,
            name,
            description,
            image,
            price,
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
    description="",
    image=None,
    price=0,
    stock=0,
):
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE products
            SET
                name = %s,
                description = %s,
                image = %s,
                price = %s,
                stock = %s
            WHERE product_id = %s
        """, (
            name,
            description,
            image,
            price,
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
# PRODUCT VARIANTS / COLORS
# ============================================================

def get_product_variants(product_id):
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM product_variants
            WHERE product_id = %s
            ORDER BY id
        """, (product_id,)).fetchall()

    finally:
        conn.close()

def get_variant(variant_id):
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT *
            FROM product_variants
            WHERE id = %s
        """, (variant_id,)).fetchone()

    finally:
        conn.close()

def add_variant(
    product_id,
    color_name,
    color_code,
    image,
    price,
    stock,
):
    conn = get_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO product_variants
            (
                product_id,
                color_name,
                color_code,
                image,
                price,
                stock
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            product_id,
            color_name,
            color_code,
            image,
            price,
            stock,
        ))

        variant_id = cursor.fetchone()["id"]

        conn.commit()

        return variant_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def update_variant(
    variant_id,
    color_name,
    color_code,
    image,
    price,
    stock,
):
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE product_variants
            SET
                color_name = %s,
                color_code = %s,
                image = %s,
                price = %s,
                stock = %s
            WHERE id = %s
        """, (
            color_name,
            color_code,
            image,
            price,
            stock,
            variant_id,
        ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def delete_variant(variant_id):
    conn = get_connection()

    try:
        conn.execute("""
            DELETE FROM product_variants
            WHERE id = %s
        """, (variant_id,))

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

            variant_id = item.get("variant_id")

            # ================================================
            # AGAR VARIANT / RANG BOR BO'LSA
            # ================================================

            if variant_id:

                result = conn.execute("""
                    UPDATE product_variants
                    SET stock = stock - %s
                    WHERE id = %s
                    AND stock >= %s
                    RETURNING stock
                """, (
                    item["quantity"],
                    variant_id,
                    item["quantity"],
                )).fetchone()

                if not result:
                    raise ValueError(
                        f"Variant qoldig'i yetarli emas: "
                        f"{variant_id}"
                    )

            # ================================================
            # AGAR RANGI YO'Q MAHSULOT BO'LSA
            # ================================================

            else:

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

            # ------------------------------------------------
            # ORDER ITEM
            # ------------------------------------------------

            conn.execute("""
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    product_name,
                    variant_id,
                    color_name,
                    price,
                    quantity,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                item["product_id"],
                item["name"],
                variant_id,
                item.get("color_name"),
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
    conn = get_connection()

    try:

        products_count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM products
        """).fetchone()["count"]

        customers_count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM customers
        """).fetchone()["count"]

        orders_count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM orders
        """).fetchone()["count"]

        delivered_count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM orders
            WHERE status = 'delivered'
        """).fetchone()["count"]

        total_revenue = conn.execute("""
            SELECT COALESCE(SUM(total), 0) AS revenue
            FROM orders
            WHERE status = 'delivered'
        """).fetchone()["revenue"]

        return {
            "products": products_count,
            "customers": customers_count,
            "orders": orders_count,
            "delivered": delivered_count,
            "revenue": total_revenue,
        }

    except Exception as e:
        print("❌ GET STATISTICS ERROR:", repr(e))
        raise

    finally:
        conn.close() 