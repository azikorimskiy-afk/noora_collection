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
