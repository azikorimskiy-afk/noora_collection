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
from app.database.db import (
    get_product,
    save_customer,
    create_order,
    get_order,
    get_order_items,
    update_order_status,
    get_connection,
)

order_router = Router()


# ==================================================
# ADMIN TEKSHIRISH
# ==================================================

def is_admin(user_id: int) -> bool:

    admin_id = os.getenv("ADMIN_ID")

    if not admin_id:
        return False

    try:
        return user_id == int(admin_id)
    except ValueError:
        return False


# ==================================================
# BUYURTMA BOSHLASH
# ==================================================

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

    await state.clear()

    await state.set_state(
        OrderState.waiting_name
    )

    await callback.message.answer(
        "👤 <b>BUYURTMA RASMIYLASHTIRISH</b>\n\n"
        "Ismingizni kiriting:"
    )

    await callback.answer()


# ==================================================
# ISM
# ==================================================

@order_router.message(
    OrderState.waiting_name
)
async def get_name(
    message: Message,
    state: FSMContext,
):

    if not message.text:

        await message.answer(
            "❗ Iltimos, ismingizni kiriting."
        )

        return

    name = message.text.strip()

    if len(name) < 2:

        await message.answer(
            "❗ Iltimos, ismingizni to‘g‘ri kiriting."
        )

        return

    await state.update_data(
        name=name
    )

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

    await state.set_state(
        OrderState.waiting_phone
    )

    await message.answer(
        "📞 <b>2/3</b>\n\n"
        "Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard,
    )


# ==================================================
# TELEFON
# ==================================================

@order_router.message(
    OrderState.waiting_phone,
    F.contact,
)
async def get_phone(
    message: Message,
    state: FSMContext,
):

    phone = message.contact.phone_number

    await state.update_data(
        phone=phone
    )

    await state.set_state(
        OrderState.waiting_address
    )

    await message.answer(
        "📍 <b>3/3</b>\n\n"
        "Yetkazib berish manzilingizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )


# ==================================================
# TELEFON XATOSI
# ==================================================

@order_router.message(
    OrderState.waiting_phone
)
async def phone_error(
    message: Message,
):

    await message.answer(
        "❗ Iltimos, pastdagi\n"
        "📞 <b>Telefon raqamni yuborish</b>\n"
        "tugmasidan foydalaning."
    )


# ==================================================
# MANZIL
# ==================================================

@order_router.message(
    OrderState.waiting_address
)
async def get_address(
    message: Message,
    state: FSMContext,
):

    if not message.text:

        await message.answer(
            "❗ Manzilni yozing."
        )

        return

    address = message.text.strip()

    if len(address) < 5:

        await message.answer(
            "❗ Iltimos, to‘liq manzil kiriting."
        )

        return

    await state.update_data(
        address=address
    )

    data = await state.get_data()

    cart = get_cart(
        message.from_user.id
    )

    if not cart:

        await message.answer(
            "🛒 Savatchangiz bo‘sh."
        )

        await state.clear()

        return

    # ==================================================
    # MAHSULOTLARNI TEKSHIRISH
    # ==================================================

    total = 0

    items = []

    for product_id, quantity in cart.items():

        product = get_product(
            product_id
        )

        if not product:

            await message.answer(
                f"❌ Mahsulot topilmadi: "
                f"<code>{product_id}</code>"
            )

            return

        if quantity <= 0:

            continue

        if product["stock"] < quantity:

            await message.answer(
                "❌ <b>Omborda yetarli mahsulot yo‘q!</b>\n\n"
                f"📦 {product['name']}\n"
                f"🛒 Siz tanlagan: {quantity} dona\n"
                f"📦 Omborda: {product['stock']} dona"
            )

            return

        subtotal = (
            product["price"] * quantity
        )

        total += subtotal

        items.append(
            {
                "product_id": product_id,
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    if not items:

        await message.answer(
            "🛒 Savatchangiz bo‘sh."
        )

        await state.clear()

        return

    # ==================================================
    # TASDIQLASH MATNI
    # ==================================================

    order_text = (
        "📦 <b>BUYURTMA</b>\n\n"
    )

    for item in items:

        order_text += (
            f"📦 {item['name']} × "
            f"{item['quantity']}\n"
            f"💰 {item['subtotal']:,} so‘m\n\n"
        )

    order_text += (
        f"💵 <b>JAMI: {total:,} so‘m</b>\n\n"
        f"👤 <b>Ism:</b> {data['name']}\n"
        f"📞 <b>Telefon:</b> {data['phone']}\n"
        f"📍 <b>Manzil:</b> {data['address']}"
    )

    # Ma'lumotlarni keyingi callback uchun saqlaymiz
    await state.update_data(
        items=items,
        total=total,
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


# ==================================================
# BUYURTMANI TASDIQLASH
# ==================================================

@order_router.callback_query(
    F.data == "confirm_order"
)
async def confirm_order(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
):

    data = await state.get_data()

    cart = get_cart(
        callback.from_user.id
    )

    if not cart:

        await callback.answer(
            "🛒 Savatchangiz bo‘sh!",
            show_alert=True,
        )

        return

    admin_id = os.getenv(
        "ADMIN_ID"
    )

    if not admin_id:

        await callback.answer(
            "❌ ADMIN_ID sozlanmagan!",
            show_alert=True,
        )

        return

    items = data.get(
        "items",
        []
    )

    total = data.get(
        "total",
        0
    )

    if not items:

        await callback.answer(
            "❌ Buyurtma ma'lumotlari topilmadi!",
            show_alert=True,
        )

        await state.clear()

        return

    # ==================================================
    # STOCKNI QAYTA TEKSHIRISH
    # ==================================================

    for item in items:

        product = get_product(
            item["product_id"]
        )

        if not product:

            await callback.answer(
                "❌ Mahsulot topilmadi!",
                show_alert=True,
            )

            return

        if product["stock"] < item["quantity"]:

            await callback.answer(
                f"❌ {product['name']} "
                f"uchun qoldiq yetarli emas!",
                show_alert=True,
            )

            return

    # ==================================================
    # CUSTOMER SAQLASH
    # ==================================================

    try:

        save_customer(
            telegram_id=callback.from_user.id,
            name=data["name"],
            phone=data["phone"],
            address=data["address"],
        )

    except Exception as e:

        print(
            "❌ CUSTOMER SAVE ERROR:",
            repr(e)
        )

        await callback.answer(
            "❌ Mijoz ma'lumotlarini saqlashda xatolik!",
            show_alert=True,
        )

        return

    # ==================================================
    # ORDER YARATISH
    # ==================================================

    try:

        order_id = create_order(
            telegram_id=callback.from_user.id,
            name=data["name"],
            phone=data["phone"],
            address=data["address"],
            total=total,
            items=items,
        )

    except Exception as e:

        print(
            "❌ ORDER CREATE ERROR:",
            repr(e)
        )

        await callback.answer(
            "❌ Buyurtmani saqlashda xatolik!",
            show_alert=True,
        )

        return

    # ==================================================
    # ADMIN BUYURTMA MATNI
    # ==================================================

    order_text = (
        "🔔 <b>YANGI BUYURTMA!</b>\n\n"
        f"🆔 <b>Buyurtma №{order_id}</b>\n\n"
    )

    for item in items:

        order_text += (
            f"📦 {item['name']} × "
            f"{item['quantity']}\n"
            f"💰 {item['subtotal']:,} so‘m\n\n"
        )

    order_text += (
        f"💵 <b>JAMI: {total:,} so‘m</b>\n\n"
        f"👤 <b>Ism:</b> {data['name']}\n"
        f"📞 <b>Telefon:</b> {data['phone']}\n"
        f"📍 <b>Manzil:</b> {data['address']}\n\n"
        f"🆔 <b>Telegram ID:</b> "
        f"{callback.from_user.id}\n\n"
        f"🟡 <b>STATUS: YANGI</b>"
    )

    # ==================================================
    # ADMIN TUGMALARI
    # ==================================================

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Qabul qilish",
        callback_data=f"admin_accept:{order_id}",
    )

    builder.button(
        text="🚚 Yetkazilmoqda",
        callback_data=f"admin_delivery:{order_id}",
    )

    builder.button(
        text="✅ Yetkazildi",
        callback_data=f"admin_delivered:{order_id}",
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data=f"admin_cancel:{order_id}",
    )

    builder.adjust(1)

    # ==================================================
    # ADMINGA YUBORISH
    # ==================================================

    try:

        await bot.send_message(
            chat_id=int(admin_id),
            text=order_text,
            reply_markup=builder.as_markup(),
        )

    except Exception as e:

        print(
            "❌ ADMIN MESSAGE ERROR:",
            repr(e)
        )

        # Admin xabariga yuborib bo'lmasa,
        # buyurtma bazada qoladi.

        await callback.answer(
            "⚠️ Buyurtma saqlandi, "
            "lekin adminga xabar yuborilmadi!",
            show_alert=True,
        )

        cart.clear()
        await state.clear()

        return

    # ==================================================
    # MIJOZGA JAVOB
    # ==================================================

    await callback.message.edit_text(
        "✅ <b>BUYURTMANGIZ QABUL QILINDI!</b>\n\n"
        f"🆔 Buyurtma №{order_id}\n"
        f"💰 Jami: {total:,} so‘m\n\n"
        "Tez orada operatorimiz siz bilan "
        "bog‘lanadi. 📞"
    )

    cart.clear()

    await state.clear()

    await callback.answer(
        "✅ Buyurtma yuborildi!"
    )


# ==================================================
# BUYURTMANI BEKOR QILISH
# ==================================================

@order_router.callback_query(
    F.data == "cancel_order"
)
async def cancel_order(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.clear()

    await callback.message.edit_text(
        "❌ <b>BUYURTMA BEKOR QILINDI.</b>\n\n"
        "🛍 Istasangiz katalogdan yana "
        "mahsulot tanlashingiz mumkin."
    )

    await callback.answer(
        "❌ Buyurtma bekor qilindi."
    )


# ==================================================
# ADMIN — QABUL QILISH
# ==================================================

@order_router.callback_query(
    F.data.startswith("admin_accept:")
)
async def admin_accept(
    callback: CallbackQuery,
    bot: Bot,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    order_id = int(
        callback.data.split(":")[1]
    )

    order = get_order(
        order_id
    )

    if not order:

        await callback.answer(
            "❌ Buyurtma topilmadi!",
            show_alert=True,
        )

        return

    update_order_status(
        order_id,
        "accepted",
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n"
        "🟢 <b>STATUS: QABUL QILINDI</b>"
    )

    try:

        await bot.send_message(
            chat_id=order["telegram_id"],
            text=(
                "🟢 <b>BUYURTMANGIZ QABUL QILINDI!</b>\n\n"
                f"🆔 Buyurtma №{order_id}\n\n"
                "Operatorimiz buyurtmangizni "
                "qabul qildi."
            ),
        )

    except Exception as e:

        print(
            "❌ CUSTOMER NOTIFY ERROR:",
            repr(e)
        )

    await callback.answer(
        "✅ Buyurtma qabul qilindi!"
    )


# ==================================================
# ADMIN — YETKAZILMOQDA
# ==================================================

@order_router.callback_query(
    F.data.startswith("admin_delivery:")
)
async def admin_delivery(
    callback: CallbackQuery,
    bot: Bot,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    order_id = int(
        callback.data.split(":")[1]
    )

    order = get_order(
        order_id
    )

    if not order:

        await callback.answer(
            "❌ Buyurtma topilmadi!",
            show_alert=True,
        )

        return

    update_order_status(
        order_id,
        "delivery",
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n"
        "🚚 <b>STATUS: YETKAZILMOQDA</b>"
    )

    try:

        await bot.send_message(
            chat_id=order["telegram_id"],
            text=(
                "🚚 <b>BUYURTMANGIZ YO‘LDA!</b>\n\n"
                f"🆔 Buyurtma №{order_id}\n\n"
                "Buyurtmangiz yetkazib berish "
                "uchun yo‘lga chiqarildi."
            ),
        )

    except Exception as e:

        print(
            "❌ CUSTOMER NOTIFY ERROR:",
            repr(e)
        )

    await callback.answer(
        "🚚 Yetkazilmoqda!"
    )


# ==================================================
# ADMIN — YETKAZILDI
# ==================================================

@order_router.callback_query(
    F.data.startswith("admin_delivered:")
)
async def admin_delivered(
    callback: CallbackQuery,
    bot: Bot,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    order_id = int(
        callback.data.split(":")[1]
    )

    order = get_order(
        order_id
    )

    if not order:

        await callback.answer(
            "❌ Buyurtma topilmadi!",
            show_alert=True,
        )

        return

    update_order_status(
        order_id,
        "delivered",
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n"
        "✅ <b>STATUS: YETKAZILDI</b>"
    )

    try:

        await bot.send_message(
            chat_id=order["telegram_id"],
            text=(
                "✅ <b>BUYURTMANGIZ YETKAZILDI!</b>\n\n"
                f"🆔 Buyurtma №{order_id}\n\n"
                "Xaridingiz uchun rahmat! ❤️"
            ),
        )

    except Exception as e:

        print(
            "❌ CUSTOMER NOTIFY ERROR:",
            repr(e)
        )

    await callback.answer(
        "✅ Buyurtma yetkazildi!"
    )


# ==================================================
# ADMIN — BEKOR QILISH
# ==================================================

@order_router.callback_query(
    F.data.startswith("admin_cancel:")
)
async def admin_cancel(
    callback: CallbackQuery,
    bot: Bot,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Ruxsat yo‘q!",
            show_alert=True,
        )

        return

    order_id = int(
        callback.data.split(":")[1]
    )

    order = get_order(
        order_id
    )

    if not order:

        await callback.answer(
            "❌ Buyurtma topilmadi!",
            show_alert=True,
        )

        return

    # Agar oldin bekor qilingan bo‘lsa,
    # stockni yana qaytarmaymiz.

    if order["status"] != "cancelled":

        items = get_order_items(
            order_id
        )

        conn = get_connection()

        try:

            for item in items:

                conn.execute(
                    """
                    UPDATE products
                    SET stock = stock + ?
                    WHERE product_id = ?
                    """,
                    (
                        item["quantity"],
                        item["product_id"],
                    )
                )

            conn.commit()

        except Exception as e:

            conn.rollback()

            print(
                "❌ STOCK RESTORE ERROR:",
                repr(e)
            )

            conn.close()

            await callback.answer(
                "❌ Stockni qaytarishda xatolik!",
                show_alert=True,
            )

            return

        conn.close()

        update_order_status(
            order_id,
            "cancelled",
        )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n"
        "🔴 <b>STATUS: BEKOR QILINDI</b>"
    )

    try:

        await bot.send_message(
            chat_id=order["telegram_id"],
            text=(
                "❌ <b>BUYURTMANGIZ BEKOR QILINDI.</b>\n\n"
                f"🆔 Buyurtma №{order_id}\n\n"
                "Qo‘shimcha ma’lumot uchun "
                "operator bilan bog‘lanishingiz mumkin."
            ),
        )

    except Exception as e:

        print(
            "❌ CUSTOMER NOTIFY ERROR:",
            repr(e)
        )

    await callback.answer(
        "❌ Buyurtma bekor qilindi!"
    )
