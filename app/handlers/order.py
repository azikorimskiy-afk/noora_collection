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
    get_variant,
    save_customer,
    create_order,
    get_order,
    get_order_items,
    update_order_status,
    cancel_order_and_restore_stock,
)


order_router = Router()


# ============================================================
# ADMIN
# ============================================================

def is_admin(
    user_id: int,
) -> bool:

    admin_id = os.getenv(
        "ADMIN_ID"
    )

    if not admin_id:
        return False

    try:

        return (
            user_id
            == int(admin_id)
        )

    except ValueError:

        return False


# ============================================================
# CHECKOUT
# ============================================================

@order_router.callback_query(
    F.data == "checkout"
)
async def checkout_handler(
    callback: CallbackQuery,
    state: FSMContext,
):

    cart = get_cart(
        callback.from_user.id
    )

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


# ============================================================
# NAME
# ============================================================

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
            "❗ Iltimos, ismingizni "
            "to‘g‘ri kiriting."
        )

        return

    await state.update_data(
        name=name
    )

    phone_keyboard = (
        ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=(
                            "📞 Telefon raqamni yuborish"
                        ),
                        request_contact=True,
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    )

    await state.set_state(
        OrderState.waiting_phone
    )

    await message.answer(
        "📞 <b>2/3</b>\n\n"
        "Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard,
    )


# ============================================================
# PHONE
# ============================================================

@order_router.message(
    OrderState.waiting_phone,
    F.contact,
)
async def get_phone(
    message: Message,
    state: FSMContext,
):

    phone = (
        message.contact.phone_number
    )

    await state.update_data(
        phone=phone
    )

    await state.set_state(
        OrderState.waiting_address
    )

    await message.answer(
        "📍 <b>3/3</b>\n\n"
        "Yetkazib berish "
        "manzilingizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )


# ============================================================
# PHONE ERROR
# ============================================================

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


# ============================================================
# ADDRESS
# ============================================================

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
            "❗ Iltimos, to‘liq manzil "
            "kiriting."
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

    # ========================================================
    # CART -> ORDER ITEMS
    # ========================================================

    total = 0

    items = []

    for cart_key, cart_item in cart.items():

        product_id = cart_item.get(
            "product_id"
        )

        variant_id = cart_item.get(
            "variant_id"
        )

        quantity = int(
            cart_item.get(
                "quantity",
                0
            )
        )

        if quantity <= 0:
            continue

        # ====================================================
        # VARIANT
        # ====================================================

        if variant_id:

            variant = get_variant(
                variant_id
            )

            if not variant:

                await message.answer(
                    "❌ Tanlangan rang "
                    "topilmadi.\n\n"
                    "Iltimos, savatchani "
                    "yangilab qaytadan "
                    "tanlang."
                )

                return

            stock = int(
                variant["stock"]
            )

            if stock < quantity:

                await message.answer(
                    "❌ <b>Omborda yetarli "
                    "mahsulot yo‘q!</b>\n\n"
                    f"📦 {cart_item['name']}\n"
                    f"🎨 Rang: "
                    f"{variant['color_name']}\n"
                    f"🛒 Siz tanlagan: "
                    f"{quantity} dona\n"
                    f"📦 Omborda: "
                    f"{stock} dona"
                )

                return

            name = cart_item[
                "name"
            ]

            color_name = (
                variant["color_name"]
            )

            price = int(
                variant["price"]
            )

        # ====================================================
        # PRODUCT
        # ====================================================

        else:

            product = get_product(
                product_id
            )

            if not product:

                await message.answer(
                    "❌ Mahsulot topilmadi!\n\n"
                    f"ID: "
                    f"<code>{product_id}</code>"
                )

                return

            stock = int(
                product["stock"]
            )

            if stock < quantity:

                await message.answer(
                    "❌ <b>Omborda yetarli "
                    "mahsulot yo‘q!</b>\n\n"
                    f"📦 {product['name']}\n"
                    f"🛒 Siz tanlagan: "
                    f"{quantity} dona\n"
                    f"📦 Omborda: "
                    f"{stock} dona"
                )

                return

            name = product[
                "name"
            ]

            color_name = None

            price = int(
                product["price"]
            )

        # ====================================================
        # SUBTOTAL
        # ====================================================

        subtotal = (
            price * quantity
        )

        total += subtotal

        items.append({

            "product_id":
                product_id,

            "variant_id":
                variant_id,

            "name":
                name,

            "color_name":
                color_name,

            "price":
                price,

            "quantity":
                quantity,

            "subtotal":
                subtotal,
        })

    # ========================================================
    # EMPTY
    # ========================================================

    if not items:

        await message.answer(
            "🛒 Savatchangiz bo‘sh."
        )

        await state.clear()

        return

    # ========================================================
    # CONFIRM TEXT
    # ========================================================

    order_text = (
        "📦 <b>BUYURTMA</b>\n\n"
    )

    for item in items:

        order_text += (
            f"📦 <b>{item['name']}</b>\n"
        )

        if item.get(
            "color_name"
        ):

            order_text += (
                f"🎨 Rang: "
                f"<b>{item['color_name']}</b>\n"
            )

        order_text += (
            f"{item['quantity']} dona × "
            f"{item['price']:,} so‘m\n"
            f"Jami: "
            f"<b>{item['subtotal']:,} so‘m</b>\n\n"
        )

    order_text += (
        f"💵 <b>JAMI: "
        f"{total:,} so‘m</b>\n\n"
        f"👤 <b>Ism:</b> "
        f"{data['name']}\n"
        f"📞 <b>Telefon:</b> "
        f"{data['phone']}\n"
        f"📍 <b>Manzil:</b> "
        f"{data['address']}"
    )

    await state.update_data(
        items=items,
        total=total,
    )

    # ========================================================
    # BUTTONS
    # ========================================================

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


# ============================================================
# CONFIRM ORDER
# ============================================================

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
            "❌ Buyurtma ma'lumotlari "
            "topilmadi!",
            show_alert=True,
        )

        await state.clear()

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

    # ========================================================
    # CUSTOMER
    # ========================================================

    try:

        save_customer(
            telegram_id=(
                callback.from_user.id
            ),
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
            "❌ Mijoz ma'lumotlarini "
            "saqlashda xatolik!",
            show_alert=True,
        )

        return

    # ========================================================
    # CREATE ORDER
    #
    # DB bu yerda stockni ATOMAR
    # ravishda kamaytiradi.
    # ========================================================

    try:

        order_id = create_order(
            telegram_id=(
                callback.from_user.id
            ),
            name=data["name"],
            phone=data["phone"],
            address=data["address"],
            total=total,
            items=items,
        )

    except ValueError as e:

        print(
            "❌ STOCK ERROR:",
            repr(e)
        )

        await callback.answer(
            "❌ Mahsulot qoldig‘i "
            "yetarli emas!",
            show_alert=True,
        )

        return

    except Exception as e:

        print(
            "❌ ORDER CREATE ERROR:",
            repr(e)
        )

        await callback.answer(
            "❌ Buyurtmani saqlashda "
            "xatolik!",
            show_alert=True,
        )

        return

    # ========================================================
    # ADMIN TEXT
    # ========================================================

    order_text = (
        "🔔 <b>YANGI BUYURTMA!</b>\n\n"
        f"🆔 <b>Buyurtma №{order_id}</b>\n\n"
    )

    for item in items:

        order_text += (
            f"📦 {item['name']} × "
            f"{item['quantity']}\n"
        )

        if item.get(
            "color_name"
        ):

            order_text += (
                f"🎨 Rang: "
                f"{item['color_name']}\n"
            )

        order_text += (
            f"💰 "
            f"{item['subtotal']:,} so‘m\n\n"
        )

    order_text += (
        f"💵 <b>JAMI: "
        f"{total:,} so‘m</b>\n\n"
        f"👤 <b>Ism:</b> "
        f"{data['name']}\n"
        f"📞 <b>Telefon:</b> "
        f"{data['phone']}\n"
        f"📍 <b>Manzil:</b> "
        f"{data['address']}\n\n"
        f"🆔 <b>Telegram ID:</b> "
        f"{callback.from_user.id}\n\n"
        "🟡 <b>STATUS: YANGI</b>"
    )

    # ========================================================
    # ADMIN BUTTONS
    # ========================================================

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Qabul qilish",
        callback_data=(
            f"admin_accept:{order_id}"
        ),
    )

    builder.button(
        text="🚚 Yetkazilmoqda",
        callback_data=(
            f"admin_delivery:{order_id}"
        ),
    )

    builder.button(
        text="✅ Yetkazildi",
        callback_data=(
            f"admin_delivered:{order_id}"
        ),
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data=(
            f"admin_cancel:{order_id}"
        ),
    )

    builder.adjust(1)

    # ========================================================
    # ADMIN MESSAGE
    # ========================================================

    try:

        await bot.send_message(
            chat_id=int(admin_id),
            text=order_text,
            reply_markup=(
                builder.as_markup()
            ),
        )

    except Exception as e:

        print(
            "❌ ADMIN MESSAGE ERROR:",
            repr(e)
        )

        # BUYURTMA ALLAQACHON DBGA SAQLANGAN.
        # STOCK HAM KAMAYGAN.
        # Admin xabar yuborilmagani uchun
        # buyurtmani o‘chirib tashlamaymiz.

        cart.clear()

        await state.clear()

        await callback.message.edit_text(
            "⚠️ <b>BUYURTMA SAQLANDI!</b>\n\n"
            f"🆔 Buyurtma №{order_id}\n"
            f"💰 Jami: {total:,} so‘m\n\n"
            "Operatorga xabar yuborishda "
            "vaqtinchalik xatolik yuz berdi."
        )

        await callback.answer(
            "⚠️ Buyurtma saqlandi.",
            show_alert=True,
        )

        return

    # ========================================================
    # CUSTOMER SUCCESS
    # ========================================================

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


# ============================================================
# CANCEL BEFORE CONFIRM
# ============================================================

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


# ============================================================
# ADMIN ACCEPT
# ============================================================

@order_router.callback_query(
    F.data.startswith(
        "admin_accept:"
    )
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
        callback.data.split(
            ":"
        )[1]
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
        "🟢 <b>STATUS: "
        "QABUL QILINDI</b>"
    )

    try:

        await bot.send_message(
            chat_id=order[
                "telegram_id"
            ],
            text=(
                "🟢 <b>BUYURTMANGIZ "
                "QABUL QILINDI!</b>\n\n"
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


# ============================================================
# ADMIN DELIVERY
# ============================================================

@order_router.callback_query(
    F.data.startswith(
        "admin_delivery:"
    )
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
        callback.data.split(
            ":"
        )[1]
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
        "🚚 <b>STATUS: "
        "YETKAZILMOQDA</b>"
    )

    try:

        await bot.send_message(
            chat_id=order[
                "telegram_id"
            ],
            text=(
                "🚚 <b>BUYURTMANGIZ "
                "YO‘LDA!</b>\n\n"
                f"🆔 Buyurtma №{order_id}\n\n"
                "Buyurtmangiz yetkazib "
                "berish uchun yo‘lga "
                "chiqarildi."
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


# ============================================================
# ADMIN DELIVERED
# ============================================================

@order_router.callback_query(
    F.data.startswith(
        "admin_delivered:"
    )
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
        callback.data.split(
            ":"
        )[1]
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
        "✅ <b>STATUS: "
        "YETKAZILDI</b>"
    )

    try:

        await bot.send_message(
            chat_id=order[
                "telegram_id"
            ],
            text=(
                "✅ <b>BUYURTMANGIZ "
                "YETKAZILDI!</b>\n\n"
                f"🆔 Buyurtma №{order_id}\n\n"
                "Xaridingiz uchun "
                "rahmat! ❤️"
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


# ============================================================
# ADMIN CANCEL
#
# STOCK QAYTADI:
#
# variant -> product_variants
# oddiy   -> products
#
# Ikkinchi marta cancel qilinsa
# stock yana qaytmaydi.
# ============================================================

@order_router.callback_query(
    F.data.startswith(
        "admin_cancel:"
    )
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
        callback.data.split(
            ":"
        )[1]
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

    # ========================================================
    # CANCEL + STOCK RESTORE
    # ========================================================

    try:

        restored = (
            cancel_order_and_restore_stock(
                order_id
            )
        )

    except Exception as e:

        print(
            "❌ CANCEL ORDER ERROR:",
            repr(e)
        )

        await callback.answer(
            "❌ Buyurtmani bekor qilishda "
            "xatolik!",
            show_alert=True,
        )

        return

    if not restored:

        await callback.answer(
            "⚠️ Bu buyurtma allaqachon "
            "bekor qilingan!",
            show_alert=True,
        )

        return

    # ========================================================
    # ADMIN MESSAGE
    # ========================================================

    await callback.message.edit_text(
        callback.message.text
        + "\n\n"
        "🔴 <b>STATUS: "
        "BEKOR QILINDI</b>"
    )

    # ========================================================
    # CUSTOMER
    # ========================================================

    try:

        await bot.send_message(
            chat_id=order[
                "telegram_id"
            ],
            text=(
                "❌ <b>BUYURTMANGIZ "
                "BEKOR QILINDI.</b>\n\n"
                f"🆔 Buyurtma №{order_id}\n\n"
                "Qo‘shimcha ma’lumot uchun "
                "operator bilan "
                "bog‘lanishingiz mumkin."
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