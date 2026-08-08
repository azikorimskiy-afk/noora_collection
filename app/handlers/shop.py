from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.db import (
    get_products,
    get_product,
    get_cart,
    add_to_cart,
    set_cart_quantity,
    clear_cart,
)


shop_router = Router()


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
# CART TEXT
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
            f"   {quantity} dona × "
            f"{product['price']:,} so‘m = "
            f"<b>{subtotal:,} so‘m</b>\n\n"
        )

    text += (
        f"💰 <b>Jami: {total:,} so‘m</b>"
    )

    return text


# ============================================================
# CART KEYBOARD
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
# SHOW CART
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
# CATALOG
# ============================================================

@shop_router.callback_query(F.data == "catalog")
async def catalog_handler(
    callback: CallbackQuery,
):

    products = get_products()

    builder = InlineKeyboardBuilder()

    if not products:

        if callback.message.text is not None:

            await callback.message.edit_text(
                "🛍 <b>KATALOG</b>\n\n"
                "Hozircha mahsulotlar mavjud emas."
            )

        else:

            await callback.message.delete()

            await callback.message.answer(
                "🛍 <b>KATALOG</b>\n\n"
                "Hozircha mahsulotlar mavjud emas."
            )

        await callback.answer()

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

    await callback.answer()


# ============================================================
# PRODUCT
# ============================================================

@shop_router.callback_query(
    F.data.startswith("product:")
)
async def product_handler(
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

    description = product["description"] or ""

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"📝 {description}\n\n"
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
# ADD TO CART
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

    try:

        add_to_cart(
            telegram_id=callback.from_user.id,
            product_id=product_id,
            quantity=1,
        )

    except ValueError as e:

        await callback.answer(
            f"❌ {str(e)}",
            show_alert=True,
        )

        return

    await callback.answer(
        "🛒 Mahsulot savatchaga qo‘shildi!"
    )

    await show_cart(callback)


# ============================================================
# CART
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
# QUANTITY
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

    product = get_product(
        product_id
    )

    if not product:

        await callback.answer(
            "❌ Mahsulot topilmadi!",
            show_alert=True,
        )

        return

    if quantity <= 0:

        await show_cart(callback)

        await callback.answer()

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
        text="⬅️ Savatcha",
        callback_data="cart",
    )

    builder.adjust(3, 1)

    await callback.message.edit_text(
        f"📦 <b>{product['name']}</b>\n\n"
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

    current = cart.get(
        product_id,
        0,
    )

    try:

        set_cart_quantity(
            telegram_id=callback.from_user.id,
            product_id=product_id,
            quantity=current + 1,
        )

    except ValueError as e:

        await callback.answer(
            f"❌ {str(e)}",
            show_alert=True,
        )

        return

    await show_cart(callback)

    await callback.answer()


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

    new_quantity = quantity - 1

    try:

        set_cart_quantity(
            telegram_id=callback.from_user.id,
            product_id=product_id,
            quantity=new_quantity,
        )

    except ValueError as e:

        await callback.answer(
            f"❌ {str(e)}",
            show_alert=True,
        )

        return

    await show_cart(callback)

    await callback.answer()


# ============================================================
# CLEAR CART
# ============================================================

@shop_router.callback_query(
    F.data == "clear_cart"
)
async def clear_cart_handler(
    callback: CallbackQuery,
):

    clear_cart(
        callback.from_user.id
    )

    await show_cart(callback)

    await callback.answer(
        "🗑 Savat tozalandi!"
    )


# ============================================================
# CHECKOUT — HOZIRCHA
# ============================================================

@shop_router.callback_query(
    F.data == "checkout"
)
async def checkout_handler(
    callback: CallbackQuery,
):

    await callback.answer(
        "✅ Buyurtma berish funksiyasini keyingi bosqichda ulaymiz.",
        show_alert=True,
    )


# ============================================================
# NOTHING
# ============================================================

@shop_router.callback_query(
    F.data == "nothing"
)
async def nothing_handler(
    callback: CallbackQuery,
):

    await callback.answer()
