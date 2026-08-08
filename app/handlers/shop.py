from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

shop_router = Router()


PRODUCTS = {
    "tasbeh": {
        "name": "📿 Tasbeh",
        "price": 50000,
        "description": "Chiroyli va sifatli tasbeh."
    },
    "joynamoz": {
        "name": "🕌 Joynamoz",
        "price": 150000,
        "description": "Yumshoq va sifatli joynamoz."
    },
    "himor": {
        "name": "🧕 Himor",
        "price": 120000,
        "description": "Qulay va chiroyli himor."
    },
    "abaya": {
        "name": "👗 Abaya",
        "price": 350000,
        "description": "Zamonaviy va nafis abaya."
    },
    "doppi": {
        "name": "🧢 Do‘ppi",
        "price": 80000,
        "description": "Milliy uslubdagi chiroyli do‘ppi."
    }
}


@shop_router.message(CommandStart())
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛍 Katalog",
        callback_data="catalog"
    )

    builder.button(
        text="🛒 Savatcha",
        callback_data="cart"
    )

    builder.adjust(1)

    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "🛍 NOORA do‘koniga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=builder.as_markup()
    )


@shop_router.callback_query(F.data == "catalog")
async def catalog_handler(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    for key, product in PRODUCTS.items():
        builder.button(
            text=product["name"],
            callback_data=f"product:{key}"
        )

    builder.button(
        text="🛒 Savatcha",
        callback_data="cart"
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "🛍 <b>KATALOG</b>\n\n"
        "Kerakli mahsulotni tanlang:",
        reply_markup=builder.as_markup()
    )

    await callback.answer()


@shop_router.callback_query(F.data.startswith("product:"))
async def product_handler(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]
    product = PRODUCTS[product_id]

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛒 Savatga qo‘shish",
        callback_data=f"add:{product_id}"
    )

    builder.button(
        text="⬅️ Katalog",
        callback_data="catalog"
    )

    builder.adjust(1)

    await callback.message.edit_text(
        f"<b>{product['name']}</b>\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Narxi: <b>{product['price']:,} so‘m</b>",
        reply_markup=builder.as_markup()
    )

    await callback.answer()
