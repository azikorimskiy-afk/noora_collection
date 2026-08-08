import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.handlers.shop import PRODUCTS

admin_router = Router()


def is_admin(user_id: int) -> bool:
    admin_id = os.getenv("ADMIN_ID")

    if not admin_id:
        return False

    try:
        return user_id == int(admin_id)
    except ValueError:
        return False


@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ Sizda admin panelga kirish huquqi yo‘q."
        )
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📦 Mahsulotlar",
        callback_data="admin_products",
    )

    builder.button(
        text="📋 Buyurtmalar",
        callback_data="admin_orders",
    )

    builder.button(
        text="👥 Mijozlar",
        callback_data="admin_customers",
    )

    builder.button(
        text="📊 Statistika",
        callback_data="admin_stats",
    )

    builder.adjust(1)

    await message.answer(
        "⚙️ <b>ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=builder.as_markup(),
    )


@admin_router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )
        return

    builder = InlineKeyboardBuilder()

    for product_id, product in PRODUCTS.items():
        builder.button(
            text=product["name"],
            callback_data=f"admin_product:{product_id}",
        )

    builder.button(
        text="➕ Mahsulot qo‘shish",
        callback_data="admin_add_product",
    )

    builder.button(
        text="⬅️ Admin panel",
        callback_data="admin_back",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "📦 <b>MAHSULOTLAR</b>\n\n"
        "Mahsulotni tanlang:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_product:"))
async def admin_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )
        return

    product_id = callback.data.split(":")[1]
    product = PRODUCTS.get(product_id)

    if not product:
        await callback.answer(
            "Mahsulot topilmadi!",
            show_alert=True,
        )
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✏️ Tahrirlash",
        callback_data=f"edit_product:{product_id}",
    )

    builder.button(
        text="🗑 O‘chirish",
        callback_data=f"delete_product:{product_id}",
    )

    builder.button(
        text="⬅️ Mahsulotlar",
        callback_data="admin_products",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        f"<b>{product['name']}</b>\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Narx: {product['price']:,} so‘m",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📦 Mahsulotlar",
        callback_data="admin_products",
    )

    builder.button(
        text="📋 Buyurtmalar",
        callback_data="admin_orders",
    )

    builder.button(
        text="👥 Mijozlar",
        callback_data="admin_customers",
    )

    builder.button(
        text="📊 Statistika",
        callback_data="admin_stats",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "⚙️ <b>ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()

from aiogram.fsm.context import FSMContext

from app.states.admin import AddProductState
from app.database.db import add_product


@admin_router.callback_query(F.data == "admin_add_product")
async def admin_add_product(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )
        return

    await state.set_state(
        AddProductState.waiting_product_id
    )

    await callback.message.answer(
        "🆔 Mahsulot uchun ID kiriting.\n\n"
        "Masalan:\n"
        "<code>tasbeh2</code>"
    )

    await callback.answer()


@admin_router.message(AddProductState.waiting_product_id)
async def product_id_received(
    message: Message,
    state: FSMContext,
):
    product_id = message.text.strip().lower()

    if not product_id:
        await message.answer(
            "❗ ID bo‘sh bo‘lmasligi kerak."
        )
        return

    await state.update_data(
        product_id=product_id
    )

    await state.set_state(
        AddProductState.waiting_name
    )

    await message.answer(
        "📦 Mahsulot nomini kiriting:\n\n"
        "Masalan: 📿 Tasbeh Premium"
    )


@admin_router.message(AddProductState.waiting_name)
async def product_name_received(
    message: Message,
    state: FSMContext,
):
    name = message.text.strip()

    await state.update_data(
        name=name
    )

    await state.set_state(
        AddProductState.waiting_price
    )

    await message.answer(
        "💰 Mahsulot narxini kiriting.\n\n"
        "Masalan: <code>75000</code>"
    )


@admin_router.message(AddProductState.waiting_price)
async def product_price_received(
    message: Message,
    state: FSMContext,
):
    try:
        price = int(
            message.text.replace(" ", "")
        )
    except ValueError:
        await message.answer(
            "❗ Narxni faqat raqam bilan kiriting.\n\n"
            "Masalan: 75000"
        )
        return

    if price <= 0:
        await message.answer(
            "❗ Narx 0 dan katta bo‘lishi kerak."
        )
        return

    await state.update_data(
        price=price
    )

    await state.set_state(
        AddProductState.waiting_description
    )

    await message.answer(
        "📝 Mahsulot tavsifini kiriting:"
    )


@admin_router.message(
    AddProductState.waiting_description
)
async def product_description_received(
    message: Message,
    state: FSMContext,
):
    description = message.text.strip()

    await state.update_data(
        description=description
    )

    await state.set_state(
        AddProductState.waiting_image
    )

    await message.answer(
        "🖼 Mahsulot rasmini yuboring."
    )


@admin_router.message(
    AddProductState.waiting_image,
    F.photo,
)
async def product_image_received(
    message: Message,
    state: FSMContext,
):
    photo = message.photo[-1]

    await state.update_data(
        image=photo.file_id
    )

    await state.set_state(
        AddProductState.waiting_stock
    )

    await message.answer(
        "📦 Qoldiqdagi mahsulot sonini kiriting.\n\n"
        "Masalan: <code>50</code>"
    )


@admin_router.message(
    AddProductState.waiting_image
)
async def product_image_error(
    message: Message,
):
    await message.answer(
        "❗ Iltimos, mahsulot rasmini yuboring."
    )


@admin_router.message(
    AddProductState.waiting_stock
)
async def product_stock_received(
    message: Message,
    state: FSMContext,
):
    try:
        stock = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❗ Qoldiqni faqat raqam bilan kiriting."
        )
        return

    if stock < 0:
        await message.answer(
            "❗ Qoldiq manfiy bo‘lishi mumkin emas."
        )
        return

    data = await state.get_data()

    try:
        add_product(
            product_id=data["product_id"],
            name=data["name"],
            price=data["price"],
            description=data["description"],
            image=data["image"],
            stock=stock,
        )

    except Exception as e:
        print("PRODUCT ADD ERROR:", repr(e))

        await message.answer(
            "❌ Mahsulot qo‘shishda xatolik yuz berdi.\n\n"
            "Ehtimol bu ID allaqachon mavjud."
        )

        await state.clear()
        return

    await state.clear()

    await message.answer(
        "✅ <b>Mahsulot muvaffaqiyatli qo‘shildi!</b>\n\n"
        f"📦 {data['name']}\n"
        f"💰 {data['price']:,} so‘m\n"
        f"📦 Qoldiq: {stock} dona"
    )
