import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states.admin import AddProductState

from app.database.db import (
    add_product,
    get_products,
    get_product,
    delete_product,
    get_order,
    get_order_items,
    get_orders,
    update_order_status,
    get_customers,
    get_statistics,
)


admin_router = Router()


# ============================================================
# ADMIN TEKSHIRISH
# ============================================================

def is_admin(user_id: int) -> bool:

    admin_id = os.getenv("ADMIN_ID")

    if not admin_id:
        return False

    try:
        return user_id == int(admin_id)
    except (ValueError, TypeError):
        return False


# ============================================================
# ADMIN PANEL KEYBOARD
# ============================================================

def admin_keyboard():

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

    return builder.as_markup()


# ============================================================
# ADMIN PANEL
# ============================================================

@admin_router.message(Command("admin"))
async def admin_panel(message: Message):

    if not is_admin(message.from_user.id):

        await message.answer(
            "⛔ Sizda admin panelga kirish huquqi yo‘q."
        )

        return

    await message.answer(
        "⚙️ <b>ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=admin_keyboard(),
    )


# ============================================================
# ADMIN ORQAGA
# ============================================================

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    await callback.message.edit_text(
        "⚙️ <b>ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=admin_keyboard(),
    )

    await callback.answer()


# ============================================================
# MAHSULOTLAR
# ============================================================

@admin_router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    products = get_products()

    builder = InlineKeyboardBuilder()

    for product in products:

        builder.button(
            text=product["name"],
            callback_data=(
                f"admin_product:{product['product_id']}"
            ),
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

    if products:

        text = (
            "📦 <b>MAHSULOTLAR</b>\n\n"
            "Mahsulotni tanlang:"
        )

    else:

        text = (
            "📦 <b>MAHSULOTLAR</b>\n\n"
            "Hozircha mahsulotlar yo‘q."
        )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# ============================================================
# MAHSULOT DETALI
# ============================================================

@admin_router.callback_query(
    F.data.startswith("admin_product:")
)
async def admin_product(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    product_id = callback.data.split(":", 1)[1]

    product = get_product(product_id)

    if not product:

        await callback.answer(
            "❌ Mahsulot topilmadi!",
            show_alert=True,
        )

        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🗑 O‘chirish",
        callback_data=(
            f"delete_product:{product_id}"
        ),
    )

    builder.button(
        text="⬅️ Mahsulotlar",
        callback_data="admin_products",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        f"📦 <b>{product['name']}</b>\n\n"
        f"📝 {product['description'] or '-'}\n\n"
        f"💰 Narx: <b>{product['price']:,} so‘m</b>\n"
        f"📦 Qoldiq: <b>{product['stock']} dona</b>",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# ============================================================
# MAHSULOT QO‘SHISH
# ============================================================

@admin_router.callback_query(
    F.data == "admin_add_product"
)
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

    await state.clear()

    await state.set_state(
        AddProductState.waiting_product_id
    )

    await callback.message.answer(
        "🆔 <b>1/6</b>\n\n"
        "Mahsulot ID sini kiriting.\n\n"
        "Masalan:\n"
        "<code>tasbeh2</code>"
    )

    await callback.answer()


# ============================================================
# 1 — PRODUCT ID
# ============================================================

@admin_router.message(
    AddProductState.waiting_product_id
)
async def product_id_received(
    message: Message,
    state: FSMContext,
):

    if not message.text:

        await message.answer(
            "❗ ID matn ko‘rinishida bo‘lishi kerak."
        )

        return

    product_id = message.text.strip().lower()

    if not product_id:

        await message.answer(
            "❗ ID bo‘sh bo‘lmasligi kerak."
        )

        return

    if get_product(product_id):

        await message.answer(
            "❌ Bu ID allaqachon mavjud.\n\n"
            "Boshqa ID kiriting."
        )

        return

    await state.update_data(
        product_id=product_id
    )

    await state.set_state(
        AddProductState.waiting_name
    )

    await message.answer(
        "📦 <b>2/6</b>\n\n"
        "Mahsulot nomini kiriting."
    )


# ============================================================
# 2 — NAME
# ============================================================

@admin_router.message(
    AddProductState.waiting_name
)
async def product_name_received(
    message: Message,
    state: FSMContext,
):

    if not message.text:

        await message.answer(
            "❗ Mahsulot nomini kiriting."
        )

        return

    name = message.text.strip()

    if len(name) < 2:

        await message.answer(
            "❗ Mahsulot nomi juda qisqa."
        )

        return

    await state.update_data(
        name=name
    )

    await state.set_state(
        AddProductState.waiting_price
    )

    await message.answer(
        "💰 <b>3/6</b>\n\n"
        "Mahsulot narxini kiriting.\n\n"
        "Masalan:\n"
        "<code>75000</code>"
    )


# ============================================================
# 3 — PRICE
# ============================================================

@admin_router.message(
    AddProductState.waiting_price
)
async def product_price_received(
    message: Message,
    state: FSMContext,
):

    if not message.text:

        await message.answer(
            "❗ Narxni kiriting."
        )

        return

    try:

        price = int(
            message.text.replace(" ", "")
        )

    except ValueError:

        await message.answer(
            "❗ Narxni faqat raqam bilan kiriting."
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
        "📝 <b>4/6</b>\n\n"
        "Mahsulot tavsifini yozing."
    )


# ============================================================
# 4 — DESCRIPTION
# ============================================================

@admin_router.message(
    AddProductState.waiting_description
)
async def product_description_received(
    message: Message,
    state: FSMContext,
):

    if not message.text:

        await message.answer(
            "❗ Tavsifni yozing."
        )

        return

    description = message.text.strip()

    await state.update_data(
        description=description
    )

    await state.set_state(
        AddProductState.waiting_image
    )

    await message.answer(
        "🖼 <b>5/6</b>\n\n"
        "Mahsulot rasmini yuboring."
    )


# ============================================================
# 5 — IMAGE
# ============================================================

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
        "📦 <b>6/6</b>\n\n"
        "Qoldiqdagi mahsulot sonini kiriting.\n\n"
        "Masalan:\n"
        "<code>50</code>"
    )


@admin_router.message(
    AddProductState.waiting_image
)
async def product_image_error(message: Message):

    await message.answer(
        "❗ Iltimos, mahsulot rasmini yuboring."
    )


# ============================================================
# 6 — STOCK
# ============================================================

@admin_router.message(
    AddProductState.waiting_stock
)
async def product_stock_received(
    message: Message,
    state: FSMContext,
):

    if not message.text:

        await message.answer(
            "❗ Qoldiq sonini kiriting."
        )

        return

    try:

        stock = int(
            message.text.strip()
        )

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
            image=data.get("image"),
            stock=stock,
        )

    except Exception as e:

        print(
            "❌ PRODUCT ADD ERROR:",
            repr(e),
        )

        await message.answer(
            "❌ Mahsulot qo‘shishda xatolik yuz berdi."
        )

        await state.clear()

        return

    await state.clear()

    await message.answer(
        "✅ <b>MAHSULOT QO‘SHILDI!</b>\n\n"
        f"📦 {data['name']}\n"
        f"💰 {data['price']:,} so‘m\n"
        f"📦 Qoldiq: {stock} dona"
    )


# ============================================================
# MAHSULOTNI O‘CHIRISH
# ============================================================

@admin_router.callback_query(
    F.data.startswith("delete_product:")
)
async def delete_product_handler(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    product_id = callback.data.split(":", 1)[1]

    product = get_product(product_id)

    if not product:

        await callback.answer(
            "❌ Mahsulot topilmadi!",
            show_alert=True,
        )

        return

    try:

        delete_product(product_id)

    except Exception as e:

        print(
            "❌ DELETE PRODUCT ERROR:",
            repr(e),
        )

        await callback.answer(
            "❌ O‘chirishda xatolik!",
            show_alert=True,
        )

        return

    await callback.message.edit_text(
        "🗑 <b>Mahsulot o‘chirildi.</b>",
        reply_markup=InlineKeyboardBuilder()
        .button(
            text="⬅️ Mahsulotlar",
            callback_data="admin_products",
        )
        .as_markup(),
    )

    await callback.answer(
        "🗑 Mahsulot o‘chirildi!"
    )


# ============================================================
# BUYURTMALAR
# ============================================================

@admin_router.callback_query(
    F.data == "admin_orders"
)
async def admin_orders(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    orders = get_orders()

    builder = InlineKeyboardBuilder()

    if not orders:

        builder.button(
            text="⬅️ Admin panel",
            callback_data="admin_back",
        )

        await callback.message.edit_text(
            "📋 <b>BUYURTMALAR</b>\n\n"
            "Hozircha buyurtmalar yo‘q.",
            reply_markup=builder.as_markup(),
        )

        await callback.answer()

        return

    for order in orders[:20]:

        status = order["status"]

        emoji = {
            "new": "🆕",
            "accepted": "🟢",
            "delivery": "🚚",
            "delivered": "✅",
            "cancelled": "🔴",
        }.get(status, "📦")

        builder.button(
            text=(
                f"{emoji} #{order['id']} — "
                f"{order['total']:,} so‘m"
            ),
            callback_data=(
                f"admin_order:{order['id']}"
            ),
        )

    builder.button(
        text="⬅️ Admin panel",
        callback_data="admin_back",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "📋 <b>BUYURTMALAR</b>\n\n"
        "Buyurtmani tanlang:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# ============================================================
# BUYURTMA DETALI
# ============================================================

@admin_router.callback_query(
    F.data.startswith("admin_order:")
)
async def admin_order_detail(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    order_id = int(
        callback.data.split(":", 1)[1]
    )

    order = get_order(order_id)

    if not order:

        await callback.answer(
            "❌ Buyurtma topilmadi!",
            show_alert=True,
        )

        return

    items = get_order_items(order_id)

    text = (
        f"📦 <b>BUYURTMA #{order['id']}</b>\n\n"
    )

    for item in items:

        text += (
            f"• {item['product_name']} × "
            f"{item['quantity']}\n"
            f"  💰 {item['subtotal']:,} so‘m\n\n"
        )

    text += (
        f"💵 <b>Jami:</b> "
        f"{order['total']:,} so‘m\n\n"
        f"👤 <b>Ism:</b> {order['name']}\n"
        f"📞 <b>Telefon:</b> {order['phone']}\n"
        f"📍 <b>Manzil:</b> {order['address']}\n"
        f"🆔 <b>Telegram ID:</b> "
        f"{order['telegram_id']}\n\n"
        f"📊 <b>Status:</b> "
        f"{order['status']}"
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🟢 Qabul qilish",
        callback_data=(
            f"order_status:accepted:{order_id}"
        ),
    )

    builder.button(
        text="🚚 Yetkazilmoqda",
        callback_data=(
            f"order_status:delivery:{order_id}"
        ),
    )

    builder.button(
        text="✅ Yetkazildi",
        callback_data=(
            f"order_status:delivered:{order_id}"
        ),
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data=(
            f"order_status:cancelled:{order_id}"
        ),
    )

    builder.button(
        text="⬅️ Buyurtmalar",
        callback_data="admin_orders",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# ============================================================
# STATUS O‘ZGARTIRISH
# ============================================================

@admin_router.callback_query(
    F.data.startswith("order_status:")
)
async def order_status_handler(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    _, status, order_id = callback.data.split(":")

    order_id = int(order_id)

    try:

        update_order_status(
            order_id,
            status,
        )

    except Exception as e:

        print(
            "❌ STATUS ERROR:",
            repr(e),
        )

        await callback.answer(
            "❌ Statusni o‘zgartirishda xatolik!",
            show_alert=True,
        )

        return

    status_names = {
        "accepted": "🟢 QABUL QILINDI",
        "delivery": "🚚 YETKAZILMOQDA",
        "delivered": "✅ YETKAZILDI",
        "cancelled": "🔴 BEKOR QILINDI",
    }

    await callback.answer(
        f"Status: {status_names.get(status, status)}"
    )

    await admin_order_detail(callback)


# ============================================================
# MIJOZLAR
# ============================================================

@admin_router.callback_query(
    F.data == "admin_customers"
)
async def admin_customers(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    customers = get_customers()

    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Admin panel",
        callback_data="admin_back",
    )

    builder.adjust(1)

    if not customers:

        await callback.message.edit_text(
            "👥 <b>MIJOZLAR</b>\n\n"
            "Hozircha mijozlar yo‘q.",
            reply_markup=builder.as_markup(),
        )

        await callback.answer()

        return

    text = "👥 <b>MIJOZLAR</b>\n\n"

    for customer in customers[:20]:

        text += (
            f"👤 <b>{customer['name'] or '-'}</b>\n"
            f"📞 {customer['phone'] or '-'}\n"
            f"📍 {customer['address'] or '-'}\n"
            f"🆔 {customer['telegram_id']}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# ============================================================
# STATISTIKA
# ============================================================

async def show_statistics(
    callback: CallbackQuery,
):

    stats = get_statistics()

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔄 Yangilash",
        callback_data="admin_stats",
    )

    builder.button(
        text="⬅️ Admin panel",
        callback_data="admin_back",
    )

    builder.adjust(1)

    text = (
        "📊 <b>STATISTIKA</b>\n\n"
        f"📦 Mahsulotlar: "
        f"<b>{stats['products']}</b>\n"
        f"👥 Mijozlar: "
        f"<b>{stats['customers']}</b>\n"
        f"📋 Buyurtmalar: "
        f"<b>{stats['orders']}</b>\n"
        f"✅ Yetkazilgan: "
        f"<b>{stats['delivered']}</b>\n"
        f"💰 Tushum: "
        f"<b>{stats['revenue']:,} so‘m</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )


@admin_router.callback_query(
    F.data == "admin_stats"
)
async def admin_stats(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    try:

        await show_statistics(callback)

    except Exception as e:

        print(
            "❌ STATISTICS ERROR:",
            repr(e),
        )

        await callback.answer(
            "❌ Statistikani yuklashda xatolik!",
            show_alert=True,
        )

        return

    await callback.answer(
        "🔄 Statistika yangilandi!"
    )