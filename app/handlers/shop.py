from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

shop_router = Router()


PRODUCTS = {
    "tasbeh": {
        "name": "📿 Tasbeh",
        "price": 50000,
        "description": "Chiroyli va sifatli tasbeh.",
    },
    "joynamoz": {
        "name": "🕌 Joynamoz",
        "price": 150000,
        "description": "Yumshoq va sifatli joynamoz.",
    },
    "himor": {
        "name": "🧕 Himor",
        "price": 120000,
        "description": "Qulay va chiroyli himor.",
    },
    "abaya": {
        "name": "👗 Abaya",
        "price": 350000,
        "description": "Zamonaviy va nafis abaya.",
    },
    "doppi": {
        "name": "🧢 Do‘ppi",
        "price": 80000,
        "description": "Milliy uslubdagi chiroyli do‘ppi.",
    },
}


# Vaqtinchalik savatchalar
# Keyin database bilan almashtiramiz.
carts = {}


def get_cart(user_id: int):
    if user_id not in carts:
        carts[user_id] = {}

    return carts[user_id]


def cart_text(user_id: int):
    cart = get_cart(user_id)

    if not cart:
        return "🛒 <b>SAVATCHA</b>\n\nSavatchangiz hozircha bo‘sh."

    text = "🛒 <b>SAVATCHA</b>\n\n"

    total = 0

    for product_id, quantity in cart.items():
        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity
        total += subtotal

        text += (
            f"{product['name']}\n"
            f"   {quantity} dona × "
            f"{product['price']:,} so‘m = "
            f"<b>{subtotal:,} so‘m</b>\n\n"
        )

    text += f"💰 <b>Jami: {total:,} so‘m</b>"

    return text


def cart_keyboard(user_id: int):
    cart = get_cart(user_id)

    builder = InlineKeyboardBuilder()

    for product_id, quantity in cart.items():
        product = PRODUCTS[product_id]

        builder.button(
            text=f"➖ {product['name']} {quantity} ➕",
            callback_data=f"quantity:{product_id}",
        )

    builder.button(
        text="🗑 Savatni tozalash",
        callback_data="clear_cart",
    )

    if cart:
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


@shop_router.callback_query(F.data == "catalog")
async def catalog_handler(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    for key, product in PRODUCTS.items():
        builder.button(
            text=product["name"],
            callback_data=f"product:{key}",
        )

    builder.button(
        text="🛒 Savatcha",
        callback_data="cart",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "🛍 <b>KATALOG</b>\n\n"
        "Mahsulotni tanlang:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@shop_router.callback_query(F.data.startswith("product:"))
async def product_handler(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]
    product = PRODUCTS[product_id]

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛒 Savatga qo‘shish",
        callback_data=f"add:{product_id}",
    )

    builder.button(
        text="⬅️ Katalog",
        callback_data="catalog",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        f"<b>{product['name']}</b>\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Narxi: <b>{product['price']:,} so‘m</b>",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@shop_router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]

    cart = get_cart(callback.from_user.id)

    if product_id not in cart:
        cart[product_id] = 1
    else:
        cart[product_id] += 1

    await callback.answer(
        "🛒 Mahsulot savatchaga qo‘shildi!",
        show_alert=False,
    )

    await callback.message.edit_text(
        cart_text(callback.from_user.id),
        reply_markup=cart_keyboard(callback.from_user.id),
    )


@shop_router.callback_query(F.data == "cart")
async def cart_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        cart_text(callback.from_user.id),
        reply_markup=cart_keyboard(callback.from_user.id),
    )

    await callback.answer()


@shop_router.callback_query(F.data.startswith("quantity:"))
async def quantity_handler(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➖",
        callback_data=f"minus:{product_id}",
    )

    builder.button(
        text=f"{get_cart(callback.from_user.id).get(product_id, 0)} dona",
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
        f"📦 <b>{PRODUCTS[product_id]['name']}</b>\n\n"
        "Miqdorni tanlang:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@shop_router.callback_query(F.data.startswith("plus:"))
async def plus_handler(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]

    cart = get_cart(callback.from_user.id)

    cart[product_id] = cart.get(product_id, 0) + 1

    await callback.message.edit_text(
        cart_text(callback.from_user.id),
        reply_markup=cart_keyboard(callback.from_user.id),
    )

    await callback.answer()


@shop_router.callback_query(F.data.startswith("minus:"))
async def minus_handler(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]

    cart = get_cart(callback.from_user.id)

    if product_id in cart:
        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    await callback.message.edit_text(
        cart_text(callback.from_user.id),
        reply_markup=cart_keyboard(callback.from_user.id),
    )

    await callback.answer()


@shop_router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    carts[callback.from_user.id] = {}

    await callback.message.edit_text(
        cart_text(callback.from_user.id),
        reply_markup=cart_keyboard(callback.from_user.id),
    )

    await callback.answer("🗑 Savatcha tozalandi!")


@shop_router.callback_query(F.data == "nothing")
async def nothing_handler(callback: CallbackQuery):
    await callback.answer()
