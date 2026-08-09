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
                description TEXT DEFAULT '',
                image TEXT,
                price BIGINT DEFAULT 0,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ====================================================
        # PRODUCT VARIANTS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_variants (
                id SERIAL PRIMARY KEY,

                product_id TEXT NOT NULL,

                color_name TEXT NOT NULL,
                color_code TEXT,

                image TEXT,

                price BIGINT NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_variant_product
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

                total BIGINT NOT NULL DEFAULT 0,

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

                variant_id INTEGER,
                color_name TEXT,

                price BIGINT NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 1,
                subtotal BIGINT NOT NULL DEFAULT 0,

                CONSTRAINT fk_order_item_order
                FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

                CONSTRAINT fk_order_item_variant
                FOREIGN KEY (variant_id)
                REFERENCES product_variants(id)
                ON DELETE SET NULL
            )
        """)

        # ====================================================
        # ESKI BAZANI MIGRATSIYA QILISH
        #
        # Agar order_items oldindan mavjud bo'lgan bo'lsa
        # va variant_id/color_name bo'lmasa, qo'shamiz.
        # ====================================================

        conn.execute("""
            ALTER TABLE order_items
            ADD COLUMN IF NOT EXISTS variant_id INTEGER
        """)

        conn.execute("""
            ALTER TABLE order_items
            ADD COLUMN IF NOT EXISTS color_name TEXT
        """)

        # ====================================================
        # FOREIGN KEY
        #
        # Eski bazada FK bo'lmasligi mumkin.
        # IF NOT EXISTS PostgreSQL FK uchun ishlamaydi,
        # shuning uchun katalogdan tekshiramiz.
        # ====================================================

        fk_exists = conn.execute("""
            SELECT 1
            FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_order_item_variant'
              AND table_name = 'order_items'
        """).fetchone()

        if not fk_exists:

            try:

                conn.execute("""
                    ALTER TABLE order_items
                    ADD CONSTRAINT fk_order_item_variant
                    FOREIGN KEY (variant_id)
                    REFERENCES product_variants(id)
                    ON DELETE SET NULL
                """)

            except Exception as e:

                print(
                    "⚠️ Variant FK qo‘shilmadi:",
                    repr(e)
                )

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
# VARIANTS / COLORS
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

        product = conn.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = %s
        """, (product_id,)).fetchone()

        if not product:

            raise ValueError(
                f"Mahsulot topilmadi: {product_id}"
            )

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

        # ====================================================
        # ORDER
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
        # ITEMS
        # ====================================================

        for item in items:

            product_id = item["product_id"]
            quantity = int(item["quantity"])

            if quantity <= 0:
                continue

            variant_id = item.get("variant_id")

            # =================================================
            # VARIANT
            # =================================================

            if variant_id:

                variant = conn.execute("""
                    SELECT *
                    FROM product_variants
                    WHERE id = %s
                    FOR UPDATE
                """, (
                    variant_id,
                )).fetchone()

                if not variant:

                    raise ValueError(
                        f"Variant topilmadi: {variant_id}"
                    )

                if variant["product_id"] != product_id:

                    raise ValueError(
                        "Variant mahsulotga tegishli emas."
                    )

                if variant["stock"] < quantity:

                    raise ValueError(
                        f"'{variant['color_name']}' "
                        f"rangi uchun qoldiq yetarli emas. "
                        f"Qoldiq: {variant['stock']}"
                    )

                # STOCK KAMAYTIRISH

                conn.execute("""
                    UPDATE product_variants
                    SET stock = stock - %s
                    WHERE id = %s
                """, (
                    quantity,
                    variant_id,
                ))

            # =================================================
            # ODDIY MAHSULOT
            # =================================================

            else:

                product = conn.execute("""
                    SELECT *
                    FROM products
                    WHERE product_id = %s
                    FOR UPDATE
                """, (
                    product_id,
                )).fetchone()

                if not product:

                    raise ValueError(
                        f"Mahsulot topilmadi: {product_id}"
                    )

                if product["stock"] < quantity:

                    raise ValueError(
                        f"'{product['name']}' "
                        f"uchun qoldiq yetarli emas. "
                        f"Qoldiq: {product['stock']}"
                    )

                # STOCK KAMAYTIRISH

                conn.execute("""
                    UPDATE products
                    SET stock = stock - %s
                    WHERE product_id = %s
                """, (
                    quantity,
                    product_id,
                ))

            # =================================================
            # ORDER ITEM
            # =================================================

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
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                order_id,
                product_id,
                item["name"],
                variant_id,
                item.get("color_name"),
                item["price"],
                quantity,
                item["subtotal"],
            ))

        # ====================================================
        # HAMMASI MUVAFFAQIYATLI
        # ====================================================

        conn.commit()

        return order_id

    except Exception:

        # Buyurtma yoki stockdan biror joyda xato bo'lsa,
        # HAMMASI rollback bo'ladi.

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
# USER ORDERS
# ============================================================

def get_user_orders(telegram_id):

    conn = get_connection()

    try:

        return conn.execute("""
            SELECT *
            FROM orders
            WHERE telegram_id = %s
            ORDER BY id DESC
        """, (
            telegram_id,
        )).fetchall()

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
# CANCEL ORDER + RESTORE STOCK
# ============================================================

def cancel_order_and_restore_stock(order_id):

    conn = get_connection()

    try:

        # ====================================================
        # ORDERNI LOCK QILAMIZ
        # ====================================================

        order = conn.execute("""
            SELECT *
            FROM orders
            WHERE id = %s
            FOR UPDATE
        """, (
            order_id,
        )).fetchone()

        if not order:

            raise ValueError(
                f"Buyurtma topilmadi: {order_id}"
            )

        # ====================================================
        # OLDIN BEKOR QILINGAN BO'LSA
        # STOCKNI QAYTARMAYMIZ
        # ====================================================

        if order["status"] == "cancelled":

            conn.commit()

            return False

        # ====================================================
        # ORDER ITEMS
        # ====================================================

        items = conn.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = %s
            ORDER BY id
        """, (
            order_id,
        )).fetchall()

        # ====================================================
        # STOCKNI QAYTARISH
        # ====================================================

        for item in items:

            quantity = int(
                item["quantity"]
            )

            variant_id = item.get(
                "variant_id"
            )

            # ================================================
            # RANG / VARIANT
            # ================================================

            if variant_id:

                conn.execute("""
                    UPDATE product_variants
                    SET stock = stock + %s
                    WHERE id = %s
                """, (
                    quantity,
                    variant_id,
                ))

            # ================================================
            # ODDIY MAHSULOT
            # ================================================

            else:

                conn.execute("""
                    UPDATE products
                    SET stock = stock + %s
                    WHERE product_id = %s
                """, (
                    quantity,
                    item["product_id"],
                ))

        # ====================================================
        # STATUS
        # ====================================================

        conn.execute("""
            UPDATE orders
            SET status = 'cancelled'
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

        print(
            "❌ GET STATISTICS ERROR:",
            repr(e)
        )

        raise

    finally:

        conn.close()