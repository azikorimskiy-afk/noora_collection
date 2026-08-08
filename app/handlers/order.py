import os

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states.order import OrderState
from app.handlers.shop import get_cart
from app.database.db import get_product

order_router = Router()


@order_router.callback_query(F.data == "checkout")
async def checkout_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    cart = get_cart(callback.from_user.id)

    if not cart:
        await callback.answer(
            "🛒 Savatchangiz bo‘sh!",
            show_alert=True,
        )
        return

    await state.set_state(OrderState.waiting_name)

    await callback.message.answer(
        "👤 <b>Buyurtma rasmiylashtirish</b>\n\n"
        "Ismingizni kiriting:"
    )

    await callback.answer()


@order_router.message(OrderState.waiting_name)
async def get_name(
    message: Message,
    state: FSMContext,
):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            "❗ Iltimos, ismingizni to‘g‘ri kiriting."
        )
        return

    await state.update_data(name=name)

    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📞 Telefon raqamni yuborish",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await state.set_state(OrderState.waiting_phone)

    await message.answer(
        "📞 Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard,
    )


@order_router.message(
    OrderState.waiting_phone,
    F.contact,
)
async def get_phone(
    message: Message,
    state: FSMContext,
):
    phone = message.contact.phone_number

    await state.update_data(phone=phone)

    await state.set_state(OrderState.waiting_address)

    await message.answer(
        "📍 Yetkazib berish manzilingizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )


@order_router.message(OrderState.waiting_phone)
async def phone_error(message: Message):
    await message.answer(
        "❗ Iltimos, pastdagi "
        "📞 Telefon raqamni yuborish "
        "tugmasidan foydalaning."
    )


@order_router.message(OrderState.waiting_address)
async def get_address(
    message: Message,
    state: FSMContext,
):
    address = message.text.strip()

    if len(address) < 5:
        await message.answer(
            "❗ Iltimos, to‘liq manzil kiriting."
        )
        return

    await state.update_data(address=address)

    data = await state.get_data()
    cart = get_cart(message.from_user.id)

    if not cart:
        await message.answer("🛒 Savatchangiz bo‘sh.")
        await state.clear()
        return

    total = 0

    order_text = "📦 <b>BUYURTMA</b>\n\n"

    for product_id, quantity in cart.items():
        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity
        total += subtotal

        order_text += (
            f"{product['name']} × {quantity}\n"
            f"💰 {subtotal:,} so‘m\n\n"
        )

    order_text += (
        f"💵 <b>Jami: {total:,} so‘m</b>\n\n"
        f"👤 Ism: {data['name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📍 Manzil: {data['address']}"
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Buyurtmani tasdiqlash",
        callback_data="confirm_order",
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data="cancel_order",
    )

    builder.adjust(1)

    await message.answer(
        order_text,
        reply_markup=builder.as_markup(),
    )


@order_router.callback_query(F.data == "confirm_order")
async def confirm_order(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()

    cart = get_cart(callback.from_user.id)

    if not cart:
        await callback.answer(
            "🛒 Savatchangiz bo‘sh!",
            show_alert=True,
        )
        return

    admin_id = os.getenv("ADMIN_ID")

    print("========== ADMIN TEST ==========")
    print("ADMIN_ID:", admin_id)
    print("USER ID:", callback.from_user.id)
    print("================================")

    if not admin_id:
        await callback.answer(
            "❌ ADMIN_ID sozlanmagan!",
            show_alert=True,
        )
        return

    total = 0

    order_text = "🔔 <b>YANGI BUYURTMA!</b>\n\n"

    for product_id, quantity in cart.items():
        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity
        total += subtotal

        order_text += (
            f"📦 {product['name']} × {quantity}\n"
            f"💰 {subtotal:,} so‘m\n\n"
        )

    order_text += (
        f"💵 <b>JAMI: {total:,} so‘m</b>\n\n"
        f"👤 <b>Ism:</b> {data['name']}\n"
        f"📞 <b>Telefon:</b> {data['phone']}\n"
        f"📍 <b>Manzil:</b> {data['address']}\n\n"
        f"🆔 <b>Telegram ID:</b> {callback.from_user.id}"
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Qabul qilish",
        callback_data="admin_accept",
    )

    builder.button(
        text="🚚 Yetkazilmoqda",
        callback_data="admin_delivery",
    )

    builder.button(
        text="✅ Yetkazildi",
        callback_data="admin_delivered",
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data="admin_cancel",
    )

    builder.adjust(1)

    try:
        print("📤 Adminga xabar yuborilmoqda...")

        await bot.send_message(
            chat_id=int(admin_id),
            text=order_text,
            reply_markup=builder.as_markup(),
        )

        print("✅ ADAMINGA XABAR YUBORILDI!")

    except Exception as e:
        print("❌ ADMIN XABAR XATOSI:", repr(e))

        await callback.answer(
            "❌ Adminga yuborishda xatolik!",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        "Tez orada operatorimiz siz bilan bog‘lanadi. 📞"
    )

    cart.clear()
    await state.clear()

    await callback.answer()


@order_router.callback_query(F.data == "cancel_order")
async def cancel_order(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        "❌ Buyurtma bekor qilindi."
    )

    await callback.answer()


@order_router.callback_query(F.data == "admin_accept")
async def admin_accept(callback: CallbackQuery):
    await callback.answer("✅ Buyurtma qabul qilindi!")

    await callback.message.edit_text(
        callback.message.text
        + "\n\n🟢 <b>STATUS: QABUL QILINDI</b>"
    )


@order_router.callback_query(F.data == "admin_delivery")
async def admin_delivery(callback: CallbackQuery):
    await callback.answer("🚚 Yetkazilmoqda!")

    await callback.message.edit_text(
        callback.message.text
        + "\n\n🚚 <b>STATUS: YETKAZILMOQDA</b>"
    )


@order_router.callback_query(F.data == "admin_delivered")
async def admin_delivered(callback: CallbackQuery):
    await callback.answer("✅ Yetkazildi!")

    await callback.message.edit_text(
        callback.message.text
        + "\n\n✅ <b>STATUS: YETKAZILDI</b>"
    )


@order_router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery):
    await callback.answer("❌ Buyurtma bekor qilindi!")

    await callback.message.edit_text(
        callback.message.text
        + "\n\n🔴 <b>STATUS: BEKOR QILINDI</b>"
    )
