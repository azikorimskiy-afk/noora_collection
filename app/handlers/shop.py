
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.db import (
    get_products,
    get_product,
)

shop_router = Router()


# ============================================================
# ODDIY SAVATCHA
# ============================================================

carts = {}


def get_cart(user_id: int):
    if user_id not in carts:
        carts[user_id] = {}

    return carts[user_id]


# ============================================================
# PRODUCTS DICT
# ============================================================

def products_dict():

    products = get_products()

    result = {}

    for product in products:

        result[product["product_id"]] = {
            "name": product["name"],
            "price": product["price"],
            "description": product["description"],
            "image": product["image"],
            "stock": product["stock"],
        }

    return result


# ============================================================
# KATALOG
# ============================================================

async def show_catalog(callback: CallbackQuery):

    products = get_products()

    builder = InlineKeyboardBuilder()

    if not products:

        text = (
            "🛍 <b>KATALOG</b>\n\n"
            "Hozircha mahsulotlar mavjud emas."
        )

        if callback.message.text is not None:

            await callback.message.edit_text(text)

        else:

            await callback.message.delete()

            await callback.message.answer(text)

        return

    for product in products:

        builder.button(
            text=product["name"],
            callback_data=f"product:{product['product_id']}",
        )

    builder.button(
        text="🛒 Savatcha",
        callback_data="cart",
    )

    builder.adjust(1)

    text = (
        "🛍 <b>KATALOG</b>\n\n"
        "Mahsulotni tanlang:"
    )

    if callback.message.text is not None:

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
        )

    else:

        await callback.message.delete()

        await callback.message.answer(
            text,
            reply_markup=builder.as_markup(),
        )


# ============================================================
# SAVATCHA MATNI
# ============================================================

def cart_text(user_id: int):

    cart = get_cart(user_id)

    if not cart:

        return (
            "🛒 <b>SAVATCHA</b>\n\n"
            "Savatchangiz hozircha bo‘sh."
        )

    products = products_dict()

    text = "🛒 <b>SAVATCHA</b>\n\n"

    total = 0

    for product_id, quantity in cart.items():

        product = products.get(product_id)

        if not product:
            continue

        subtotal = product["price"] * quantity

        total += subtotal

        text += (
            f"📦 <b>{product['name']}</b>\n"
            f"{quantity} dona × "
            f"{product['price']:,} so‘m\n"
            f"Jami: <b>{subtotal:,} so‘m</b>\n\n"
        )

    text += (
        f"💰 <b>Umumiy: {total:,} so‘m</b>"
    )

    return text


# ============================================================
# SAVATCHA KEYBOARD
# ============================================================

def cart_keyboard(user_id: int):

    cart = get_cart(user_id)

    products = products_dict()

    builder = InlineKeyboardBuilder()

    for product_id, quantity in cart.items():

        product = products.get(product_id)

        if not product:
            continue

        builder.button(
            text=f"📦 {product['name']} — {quantity} dona",
            callback_data=f"quantity:{product_id}",
        )

    if cart:

        builder.button(
            text="🗑 Savatni tozalash",
            callback_data="clear_cart",
        )

        builder.button(
            text="✅ Buyurtma berish",
            callback_data="checkout",
        )

    builder.button(
        text="⬅️ Katalog",
        callback_data="catalog",
    )

    builder.adjust(1)

    return builder.as_markup()


# ============================================================
# SAVATCHANI KO‘RSATISH
# ============================================================

async def show_cart(callback: CallbackQuery):

    text = cart_text(
        callback.from_user.id
    )

    keyboard = cart_keyboard(
        callback.from_user.id
    )

    if callback.message.text is not None:

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
        )

    else:

        await callback.message.delete()

        await callback.message.answer(
            text,
            reply_markup=keyboard,
        )


# ============================================================
# START
# ============================================================

@shop_router.message(CommandStart())
async def start_handler(message: Message):

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛍 Katalog",
        callback_data="catalog",
    )

    builder.button(
        text="🛒 Savatcha",
        callback_data="cart",
    )

    builder.adjust(1)

    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "🛍 <b>NOORA</b> do‘koniga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=builder.as_markup(),
    )


# ============================================================
# KATALOG
# ============================================================

@shop_router.callback_query(F.data == "catalog")
async def catalog_handler(callback: CallbackQuery):

    await show_catalog(callback)

    await callback.answer()


# ============================================================
# MAHSULOT
# ============================================================

@shop_router.callback_query(
    F.data.startswith("product:")
)
async def product_handler(callback: CallbackQuery):

    product_id = callback.data.split(":", 1)[1]

    product = get_product(product_id)

    if not product:

        await callback.answer(
            "❌ Mahsulot topilmadi!",
            show_alert=True,
        )

        return

    builder = InlineKeyboardBuilder()

    if product["stock"] > 0:

        builder.button(
            text="🛒 Savatga qo‘shish",
            callback_data=f"add:{product_id}",
        )

    else:

        builder.button(
            text="❌ Sotuvda yo‘q",
            callback_data="nothing",
        )

    builder.button(
        text="⬅️ Katalog",
        callback_data="catalog",
    )

    builder.adjust(1)

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"📝 {product['description'] or 'Tavsif mavjud emas'}\n\n"
        f"💰 Narxi: "
        f"<b>{product['price']:,} so‘m</b>\n"
        f"📦 Qoldiq: "
        f"<b>{product['stock']} dona</b>"
    )

    if product["image"]:

        await callback.message.delete()

        await callback.message.answer_photo(
            photo=product["image"],
            caption=text,
            reply_markup=builder.as_markup(),
        )

    else:

        if callback.message.text is not None:

            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
            )

        else:

            await callback.message.delete()

            await callback.message.answer(
                text,
                reply_markup=builder.as_markup(),
            )

    await callback.answer()


# ============================================================
# SAVATGA QO‘SHISH
# ============================================================

@shop_router.callback_query(
    F.data.startswith("add:")
)
async def add_to_cart_handler(
    callback: CallbackQuery,
):

    product_id = callback.data.split(":", 1)[1]

    product = get_product(product_id)

    if not product:

        await callback.answer(
            "❌ Mahsulot topilmadi!",
            show_alert=True,
        )

        return

    stock = product["stock"]

    if stock <= 0:

        await callback.answer(
            "❌ Mahsulot qolmagan!",
            show_alert=True,
        )

        return

    cart = get_cart(
        callback.from_user.id
    )

    current_quantity = cart.get(
        product_id,
        0,
    )

    if current_quantity >= stock:

        await callback.answer(
            "❌ Omborda bundan ko‘p mahsulot yo‘q!",
            show_alert=True,
        )

        return

    cart[product_id] = current_quantity + 1

    await callback.answer(
        "🛒 Savatchaga qo‘shildi!"
    )

    await show_cart(callback)


# ============================================================
# SAVATCHA
# ============================================================

@shop_router.callback_query(
    F.data == "cart"
)
async def cart_handler(
    callback: CallbackQuery,
):

    await show_cart(callback)

    await callback.answer()


# ============================================================
# MIQDOR
# ============================================================

@shop_router.callback_query(
    F.data.startswith("quantity:")
)
async def quantity_handler(
    callback: CallbackQuery,
):

    product_id = callback.data.split(":", 1)[1]

    cart = get_cart(
        callback.from_user.id
    )

    quantity = cart.get(
        product_id,
        0,
    )

    product = get_product(product_id)

    if not product:

        await callback.answer(
            "❌ Mahsulot topilmadi!"
        )

        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➖",
        callback_data=f"minus:{product_id}",
    )

    builder.button(
        text=f"{quantity} dona",
        callback_data="nothing",
    )

    builder.button(
        text="➕",
        callback_data=f"plus:{product_id}",
    )

    builder.button(
        text="🗑 O‘chirish",
        callback_data=f"remove:{product_id}",
    )

    builder.button(
        text="⬅️ Savatcha",
        callback_data="cart",
    )

    builder.adjust(3, 1, 1)

    await callback.message.edit_text(
        f"📦 <b>{product['name']}</b>\n\n"
        f"📊 Hozirgi miqdor: "
        f"<b>{quantity} dona</b>\n\n"
        "Miqdorni tanlang:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# ============================================================
# PLUS
# ============================================================

@shop_router.callback_query(
    F.data.startswith("plus:")
)
async def plus_handler(
    callback: CallbackQuery,
):

    product_id = callback.data.split(":", 1)[1]

    cart = get_cart(
        callback.from_user.id
    )

    product = get_product(product_id)

    if not product:

        await callback.answer(
            "❌ Mahsulot topilmadi!"
        )

        return

    current = cart.get(
        product_id,
        0,
    )

    if current >= product["stock"]:

        await callback.answer(
            "❌ Ombordagi qoldiq tugadi!",
            show_alert=True,
        )

        return

    cart[product_id] = current + 1

    await show_cart(callback)

    await callback.answer(
        "➕ Qo‘shildi"
    )


# ============================================================
# MINUS
# ============================================================

@shop_router.callback_query(
    F.data.startswith("minus:")
)
async def minus_handler(
    callback: CallbackQuery,
):

    product_id = callback.data.split(":", 1)[1]

    cart = get_cart(
        callback.from_user.id
    )

    quantity = cart.get(
        product_id,
        0,
    )

    if quantity <= 1:

        cart.pop(
            product_id,
            None,
        )

    else:

        cart[product_id] = quantity - 1

    await show_cart(callback)

    await callback.answer(
        "➖ Kamaytirildi"
    )


# ============================================================
# O‘CHIRISH
# ============================================================

@shop_router.callback_query(
    F.data.startswith("remove:")
)
async def remove_handler(
    callback: CallbackQuery,
):

    product_id = callback.data.split(":", 1)[1]

    cart = get_cart(
        callback.from_user.id
    )

    cart.pop(
        product_id,
        None,
    )

    await show_cart(callback)

    await callback.answer(
        "🗑 Mahsulot o‘chirildi"
    )


# ============================================================
# SAVATNI TOZALASH
# ============================================================

@shop_router.callback_query(
    F.data == "clear_cart"
)
async def clear_cart_handler(
    callback: CallbackQuery,
):

    carts[callback.from_user.id] = {}

    await show_cart(callback)

    await callback.answer(
        "🗑 Savat tozalandi!"
    )


# ============================================================
# HECH NIMA
# ============================================================

@shop_router.callback_query(
    F.data == "nothing"
)
async def nothing_handler(
    callback: CallbackQuery,
):

    await callback.answer()
