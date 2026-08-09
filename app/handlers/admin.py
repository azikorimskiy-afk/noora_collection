import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states.admin import (
    AddProductState,
    EditProductState,
    AddVariantState,
    EditVariantState,
)

from app.database.db import (
    add_product,
    get_products,
    get_product,
    update_product,
    delete_product,
    get_product_variants,
    get_variant,
    add_variant,
    update_variant,
    delete_variant,
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
        text="ð¦ Mahsulotlar",
        callback_data="admin_products",
    )

    builder.button(
        text="ð Buyurtmalar",
        callback_data="admin_orders",
    )

    builder.button(
        text="ð¥ Mijozlar",
        callback_data="admin_customers",
    )

    builder.button(
        text="ð Statistika",
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
            "â Sizda admin panelga kirish huquqi yoâq."
        )

        return

    await message.answer(
        "âï¸ <b>ADMIN PANEL</b>\n\n"
        "Kerakli boâlimni tanlang:",
        reply_markup=admin_keyboard(),
    )

# ============================================================
# ADMIN ORQAGA
# ============================================================

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "â Ruxsat yoâq!",
            show_alert=True,
        )

        return

    await callback.message.edit_text(
        "âï¸ <b>ADMIN PANEL</b>\n\n"
        "Kerakli boâlimni tanlang:",
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
            "â Ruxsat yoâq!",
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
        text="â Mahsulot qoâshish",
        callback_data="admin_add_product",
    )

    builder.button(
        text="â¬ï¸ Admin panel",
        callback_data="admin_back",
    )

    builder.adjust(1)

    if products:

        text = (
            "ð¦ <b>MAHSULOTLAR</b>\n\n"
            "Mahsulotni tanlang:"
        )

    else:

        text = (
            "ð¦ <b>MAHSULOTLAR</b>\n\n"
            "Hozircha mahsulotlar yoâq."
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
        await callback.answer("â Ruxsat yoâq!", show_alert=True)
        return

    product_id = callback.data.split(":", 1)[1]
    product = get_product(product_id)

    if not product:
        await callback.answer("â Mahsulot topilmadi!", show_alert=True)
        return

    variants = get_product_variants(product_id)
    builder = InlineKeyboardBuilder()

    builder.button(text="âï¸ Tahrirlash", callback_data=f"edit_product:{product_id}")
    builder.button(text="ð¨ Ranglar", callback_data=f"product_variants:{product_id}")
    builder.button(text="ð Oâchirish", callback_data=f"delete_product:{product_id}")
    builder.button(text="â¬ï¸ Mahsulotlar", callback_data="admin_products")
    builder.adjust(1)

    await callback.message.edit_text(
        f"ð¦ <b>{product['name']}</b>\n\n"
        f"ð {product['description'] or '-'}\n\n"
        f"ð° Narx: <b>{product['price']:,} soâm</b>\n"
        f"ð¦ Qoldiq: <b>{product['stock']} dona</b>\n"
        f"ð¨ Ranglar: <b>{len(variants)} ta</b>",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()

# ============================================================
# MAHSULOT QOâSHISH
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
            "â Ruxsat yoâq!",
            show_alert=True,
        )

        return

    await state.clear()

    await state.set_state(
        AddProductState.waiting_product_id
    )

    await callback.message.answer(
        "ð <b>1/6</b>\n\n"
        "Mahsulot ID sini kiriting.\n\n"
        "Masalan:\n"
        "<code>tasbeh2</code>"
    )

    await callback.answer()

# ============================================================
# 1 â PRODUCT ID
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
            "â ID matn koârinishida boâlishi kerak."
        )

        return

    product_id = message.text.strip().lower()

    if not product_id:

        await message.answer(
            "â ID boâsh boâlmasligi kerak."
        )

        return

    if get_product(product_id):

        await message.answer(
            "â Bu ID allaqachon mavjud.\n\n"
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
        "ð¦ <b>2/6</b>\n\n"
        "Mahsulot nomini kiriting."
    )

# ============================================================
# 2 â NAME
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
            "â Mahsulot nomini kiriting."
        )

        return

    name = message.text.strip()

    if len(name) < 2:

        await message.answer(
            "â Mahsulot nomi juda qisqa."
        )

        return

    await state.update_data(
        name=name
    )

    await state.set_state(
        AddProductState.waiting_price
    )

    await message.answer(
        "ð° <b>3/6</b>\n\n"
        "Mahsulot narxini kiriting.\n\n"
        "Masalan:\n"
        "<code>75000</code>"
    )

# ============================================================
# 3 â PRICE
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
            "â Narxni kiriting."
        )

        return

    try:

        price = int(
            message.text.replace(" ", "")
        )

    except ValueError:

        await message.answer(
            "â Narxni faqat raqam bilan kiriting."
        )

        return

    if price <= 0:

        await message.answer(
            "â Narx 0 dan katta boâlishi kerak."
        )

        return

    await state.update_data(
        price=price
    )

    await state.set_state(
        AddProductState.waiting_description
    )

    await message.answer(
        "ð <b>4/6</b>\n\n"
        "Mahsulot tavsifini yozing."
    )

# ============================================================
# 4 â DESCRIPTION
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
            "â Tavsifni yozing."
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
        "ð¼ <b>5/6</b>\n\n"
        "Mahsulot rasmini yuboring."
    )

# ============================================================
# 5 â IMAGE
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
        "ð¦ <b>6/6</b>\n\n"
        "Qoldiqdagi mahsulot sonini kiriting.\n\n"
        "Masalan:\n"
        "<code>50</code>"
    )

@admin_router.message(
    AddProductState.waiting_image
)
async def product_image_error(message: Message):

    await message.answer(
        "â Iltimos, mahsulot rasmini yuboring."
    )

# ============================================================
# 6 â STOCK
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
            "â Qoldiq sonini kiriting."
        )

        return

    try:

        stock = int(
            message.text.strip()
        )

    except ValueError:

        await message.answer(
            "â Qoldiqni faqat raqam bilan kiriting."
        )

        return

    if stock < 0:

        await message.answer(
            "â Qoldiq manfiy boâlishi mumkin emas."
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
            "â PRODUCT ADD ERROR:",
            repr(e),
        )

        await message.answer(
            "â Mahsulot qoâshishda xatolik yuz berdi."
        )

        await state.clear()

        return

    await state.clear()

    await message.answer(
        "â <b>MAHSULOT QOâSHILDI!</b>\n\n"
        f"ð¦ {data['name']}\n"
        f"ð° {data['price']:,} soâm\n"
        f"ð¦ Qoldiq: {stock} dona"
    )

# ============================================================
# MAHSULOTNI TAHRIRLASH
# ============================================================

@admin_router.callback_query(F.data.startswith("edit_product:"))
async def edit_product_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True)
        return

    product_id = callback.data.split(":", 1)[1]
    product = get_product(product_id)
    if not product:
        await callback.answer("â Mahsulot topilmadi!", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="ð Nom", callback_data=f"edit_name:{product_id}")
    builder.button(text="ð° Narx", callback_data=f"edit_price:{product_id}")
    builder.button(text="ð Tavsif", callback_data=f"edit_description:{product_id}")
    builder.button(text="ð¼ Rasm", callback_data=f"edit_image:{product_id}")
    builder.button(text="ð¦ Qoldiq", callback_data=f"edit_stock:{product_id}")
    builder.button(text="ð¨ Ranglar", callback_data=f"product_variants:{product_id}")
    builder.button(text="â¬ï¸ Orqaga", callback_data=f"admin_product:{product_id}")
    builder.adjust(1)

    await callback.message.edit_text(
        f"âï¸ <b>{product['name']}</b>\n\nNimani oâzgartirmoqchisiz?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()

async def _finish_product_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    product = get_product(data["product_id"])
    if not product:
        await state.clear()
        await message.answer("â Mahsulot topilmadi.")
        return None
    return product

@admin_router.callback_query(F.data.startswith("edit_name:"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    pid = callback.data.split(":", 1)[1]
    await state.clear(); await state.update_data(product_id=pid)
    await state.set_state(EditProductState.waiting_name)
    await callback.message.answer("ð Yangi mahsulot nomini kiriting:")
    await callback.answer()

@admin_router.message(EditProductState.waiting_name)
async def edit_name_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("â Mahsulot nomini toâgâri kiriting."); return
    product = await _finish_product_edit(message, state)
    if not product: return
    update_product(product["product_id"], message.text.strip(), product["description"], product["image"], product["price"], product["stock"])
    await state.clear(); await message.answer("â Mahsulot nomi oâzgartirildi.")

@admin_router.callback_query(F.data.startswith("edit_price:"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    pid = callback.data.split(":", 1)[1]
    await state.clear(); await state.update_data(product_id=pid)
    await state.set_state(EditProductState.waiting_price)
    await callback.message.answer("ð° Yangi narxni kiriting (masalan: 75000):")
    await callback.answer()

@admin_router.message(EditProductState.waiting_price)
async def edit_price_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try: price = int(message.text.replace(" ", ""))
    except (ValueError, AttributeError):
        await message.answer("â Narxni faqat raqam bilan kiriting."); return
    if price <= 0:
        await message.answer("â Narx 0 dan katta boâlishi kerak."); return
    product = await _finish_product_edit(message, state)
    if not product: return
    update_product(product["product_id"], product["name"], product["description"], product["image"], price, product["stock"])
    await state.clear(); await message.answer(f"â Narx oâzgartirildi: <b>{price:,} soâm</b>")

@admin_router.callback_query(F.data.startswith("edit_description:"))
async def edit_description_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    pid = callback.data.split(":", 1)[1]
    await state.clear(); await state.update_data(product_id=pid)
    await state.set_state(EditProductState.waiting_description)
    await callback.message.answer("ð Yangi tavsifni kiriting:")
    await callback.answer()

@admin_router.message(EditProductState.waiting_description)
async def edit_description_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    if not message.text:
        await message.answer("â Tavsifni matn koârinishida yuboring."); return
    product = await _finish_product_edit(message, state)
    if not product: return
    update_product(product["product_id"], product["name"], message.text.strip(), product["image"], product["price"], product["stock"])
    await state.clear(); await message.answer("â Tavsif oâzgartirildi.")

@admin_router.callback_query(F.data.startswith("edit_image:"))
async def edit_image_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    pid = callback.data.split(":", 1)[1]
    await state.clear(); await state.update_data(product_id=pid)
    await state.set_state(EditProductState.waiting_image)
    await callback.message.answer("ð¼ Yangi mahsulot rasmini yuboring:")
    await callback.answer()

@admin_router.message(EditProductState.waiting_image, F.photo)
async def edit_image_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    product = await _finish_product_edit(message, state)
    if not product: return
    update_product(product["product_id"], product["name"], product["description"], message.photo[-1].file_id, product["price"], product["stock"])
    await state.clear(); await message.answer("â Mahsulot rasmi oâzgartirildi.")

@admin_router.message(EditProductState.waiting_image)
async def edit_image_error(message: Message):
    await message.answer("â Iltimos, rasm yuboring.")

@admin_router.callback_query(F.data.startswith("edit_stock:"))
async def edit_stock_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    pid = callback.data.split(":", 1)[1]
    await state.clear(); await state.update_data(product_id=pid)
    await state.set_state(EditProductState.waiting_stock)
    await callback.message.answer("ð¦ Yangi qoldiqni kiriting:")
    await callback.answer()

@admin_router.message(EditProductState.waiting_stock)
async def edit_stock_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try: stock = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("â Qoldiqni faqat raqam bilan kiriting."); return
    if stock < 0:
        await message.answer("â Qoldiq manfiy boâlishi mumkin emas."); return
    product = await _finish_product_edit(message, state)
    if not product: return
    update_product(product["product_id"], product["name"], product["description"], product["image"], product["price"], stock)
    await state.clear(); await message.answer(f"â Qoldiq oâzgartirildi: <b>{stock} dona</b>")

# ============================================================
# RANGLAR / VARIANTLAR
# ============================================================

@admin_router.callback_query(F.data.startswith("product_variants:"))
async def product_variants(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    pid = callback.data.split(":", 1)[1]
    product = get_product(pid)
    if not product:
        await callback.answer("â Mahsulot topilmadi!", show_alert=True); return
    variants = get_product_variants(pid)
    builder = InlineKeyboardBuilder()
    for v in variants:
        builder.button(text=f"ð¨ {v['color_name']} â {v['price']:,} soâm ({v['stock']})", callback_data=f"admin_variant:{v['id']}")
    builder.button(text="â Rang qoâshish", callback_data=f"admin_add_variant:{pid}")
    builder.button(text="â¬ï¸ Orqaga", callback_data=f"admin_product:{pid}")
    builder.adjust(1)
    await callback.message.edit_text(
        f"ð¨ <b>{product['name']} â RANGLAR</b>\n\n"
        + ("Rangni tanlang:" if variants else "Hozircha rang qoâshilmagan."),
        reply_markup=builder.as_markup(),
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_add_variant:"))
async def add_variant_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    pid = callback.data.split(":", 1)[1]
    await state.clear(); await state.update_data(product_id=pid)
    await state.set_state(AddVariantState.waiting_color_name)
    await callback.message.answer("ð¨ Rang nomini kiriting (masalan: Qora):")
    await callback.answer()

@admin_router.message(AddVariantState.waiting_color_name)
async def variant_name_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    if not message.text:
        await message.answer("â Rang nomini kiriting."); return
    await state.update_data(color_name=message.text.strip())
    await state.set_state(AddVariantState.waiting_color_code)
    await message.answer("ð¢ Rang kodini kiriting (masalan: #000000). Kerak boâlmasa - yuboring:")

@admin_router.message(AddVariantState.waiting_color_code)
async def variant_code_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    code = message.text.strip() if message.text else "-"
    await state.update_data(color_code=None if code == "-" else code)
    await state.set_state(AddVariantState.waiting_image)
    await message.answer("ð¼ Shu rangning rasmini yuboring:")

@admin_router.message(AddVariantState.waiting_image, F.photo)
async def variant_image_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(image=message.photo[-1].file_id)
    await state.set_state(AddVariantState.waiting_price)
    await message.answer("ð° Shu rangning narxini kiriting:")

@admin_router.message(AddVariantState.waiting_image)
async def variant_image_error(message: Message):
    await message.answer("â Iltimos, rasm yuboring.")

@admin_router.message(AddVariantState.waiting_price)
async def variant_price_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try: price = int(message.text.replace(" ", ""))
    except (ValueError, AttributeError):
        await message.answer("â Narxni faqat raqam bilan kiriting."); return
    if price <= 0:
        await message.answer("â Narx 0 dan katta boâlishi kerak."); return
    await state.update_data(price=price)
    await state.set_state(AddVariantState.waiting_stock)
    await message.answer("ð¦ Shu rangdan nechta dona bor?")

@admin_router.message(AddVariantState.waiting_stock)
async def variant_stock_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try: stock = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("â Qoldiqni faqat raqam bilan kiriting."); return
    if stock < 0:
        await message.answer("â Qoldiq manfiy boâlishi mumkin emas."); return
    data = await state.get_data()
    try:
        add_variant(data["product_id"], data["color_name"], data.get("color_code"), data["image"], data["price"], stock)
    except Exception as e:
        print("â VARIANT ADD ERROR:", repr(e))
        await state.clear(); await message.answer("â Rang qoâshishda xatolik yuz berdi."); return
    await state.clear()
    await message.answer(f"â <b>RANG QOâSHILDI!</b>\n\nð¨ {data['color_name']}\nð° {data['price']:,} soâm\nð¦ {stock} dona")

@admin_router.callback_query(F.data.startswith("admin_variant:"))
async def variant_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1])
    v = get_variant(vid)
    if not v:
        await callback.answer("â Rang topilmadi!", show_alert=True); return
    builder = InlineKeyboardBuilder()
    builder.button(text="âï¸ Tahrirlash", callback_data=f"edit_variant:{vid}")
    builder.button(text="ð Oâchirish", callback_data=f"delete_variant:{vid}")
    builder.button(text="â¬ï¸ Ranglar", callback_data=f"product_variants:{v['product_id']}")
    builder.adjust(1)
    await callback.message.edit_text(
        f"ð¨ <b>{v['color_name']}</b>\n\n"
        f"ð¢ Kod: <code>{v['color_code'] or '-'}</code>\n"
        f"ð° Narx: <b>{v['price']:,} soâm</b>\n"
        f"ð¦ Qoldiq: <b>{v['stock']} dona</b>",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("delete_variant:"))
async def delete_variant_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1])
    v = get_variant(vid)
    if not v:
        await callback.answer("â Rang topilmadi!", show_alert=True); return
    try:
        delete_variant(vid)
    except Exception as e:
        print("â VARIANT DELETE ERROR:", repr(e))
        await callback.answer("â Rangni oâchirishda xatolik!", show_alert=True); return
    await callback.message.edit_text("ð <b>Rang oâchirildi.</b>", reply_markup=InlineKeyboardBuilder().button(text="â¬ï¸ Ranglar", callback_data=f"product_variants:{v['product_id']}").as_markup())
    await callback.answer("ð Rang oâchirildi!")

@admin_router.callback_query(F.data.startswith("edit_variant:"))
async def edit_variant_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1]); v = get_variant(vid)
    if not v:
        await callback.answer("â Rang topilmadi!", show_alert=True); return
    builder = InlineKeyboardBuilder()
    builder.button(text="ð¨ Rang nomi", callback_data=f"edit_v_name:{vid}")
    builder.button(text="ð¢ Rang kodi", callback_data=f"edit_v_code:{vid}")
    builder.button(text="ð¼ Rasm", callback_data=f"edit_v_image:{vid}")
    builder.button(text="ð° Narx", callback_data=f"edit_v_price:{vid}")
    builder.button(text="ð¦ Qoldiq", callback_data=f"edit_v_stock:{vid}")
    builder.button(text="â¬ï¸ Orqaga", callback_data=f"admin_variant:{vid}")
    builder.adjust(1)
    await callback.message.edit_text(f"âï¸ <b>{v['color_name']}</b>\n\nNimani oâzgartirmoqchisiz?", reply_markup=builder.as_markup())
    await callback.answer()

@admin_router.callback_query(F.data.startswith("edit_v_name:"))
async def edit_v_name_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1]); v = get_variant(vid)
    if not v: await callback.answer("â Rang topilmadi!", show_alert=True); return
    await state.clear(); await state.update_data(variant_id=vid); await state.set_state(EditVariantState.waiting_color_name)
    await callback.message.answer("ð¨ Yangi rang nomini kiriting:"); await callback.answer()

@admin_router.message(EditVariantState.waiting_color_name)
async def edit_v_name_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    if not message.text: await message.answer("â Rang nomini kiriting."); return
    data = await state.get_data(); v = get_variant(data["variant_id"])
    if not v: await state.clear(); await message.answer("â Rang topilmadi."); return
    update_variant(data["variant_id"], message.text.strip(), v["color_code"], v["image"], v["price"], v["stock"])
    await state.clear(); await message.answer("â Rang nomi oâzgartirildi.")

@admin_router.callback_query(F.data.startswith("edit_v_code:"))
async def edit_v_code_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1]); await state.clear(); await state.update_data(variant_id=vid); await state.set_state(EditVariantState.waiting_color_code)
    await callback.message.answer("ð¢ Yangi rang kodini kiriting. Oâchirish uchun - yuboring:"); await callback.answer()

@admin_router.message(EditVariantState.waiting_color_code)
async def edit_v_code_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data(); v = get_variant(data["variant_id"])
    if not v: await state.clear(); await message.answer("â Rang topilmadi."); return
    code = message.text.strip() if message.text else "-"
    update_variant(data["variant_id"], v["color_name"], None if code == "-" else code, v["image"], v["price"], v["stock"])
    await state.clear(); await message.answer("â Rang kodi oâzgartirildi.")

@admin_router.callback_query(F.data.startswith("edit_v_image:"))
async def edit_v_image_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1]); await state.clear(); await state.update_data(variant_id=vid); await state.set_state(EditVariantState.waiting_image)
    await callback.message.answer("ð¼ Yangi rang rasmini yuboring:"); await callback.answer()

@admin_router.message(EditVariantState.waiting_image, F.photo)
async def edit_v_image_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data(); v = get_variant(data["variant_id"])
    if not v: await state.clear(); await message.answer("â Rang topilmadi."); return
    update_variant(data["variant_id"], v["color_name"], v["color_code"], message.photo[-1].file_id, v["price"], v["stock"])
    await state.clear(); await message.answer("â Rang rasmi oâzgartirildi.")

@admin_router.message(EditVariantState.waiting_image)
async def edit_v_image_error(message: Message):
    await message.answer("â Iltimos, rasm yuboring.")

@admin_router.callback_query(F.data.startswith("edit_v_price:"))
async def edit_v_price_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1]); await state.clear(); await state.update_data(variant_id=vid); await state.set_state(EditVariantState.waiting_price)
    await callback.message.answer("ð° Yangi narxni kiriting:"); await callback.answer()

@admin_router.message(EditVariantState.waiting_price)
async def edit_v_price_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try: price = int(message.text.replace(" ", ""))
    except (ValueError, AttributeError): await message.answer("â Narxni faqat raqam bilan kiriting."); return
    if price <= 0: await message.answer("â Narx 0 dan katta boâlishi kerak."); return
    data = await state.get_data(); v = get_variant(data["variant_id"])
    if not v: await state.clear(); await message.answer("â Rang topilmadi."); return
    update_variant(data["variant_id"], v["color_name"], v["color_code"], v["image"], price, v["stock"])
    await state.clear(); await message.answer(f"â Rang narxi oâzgartirildi: <b>{price:,} soâm</b>")

@admin_router.callback_query(F.data.startswith("edit_v_stock:"))
async def edit_v_stock_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): await callback.answer("â Ruxsat yoâq!", show_alert=True); return
    vid = int(callback.data.split(":", 1)[1]); await state.clear(); await state.update_data(variant_id=vid); await state.set_state(EditVariantState.waiting_stock)
    await callback.message.answer("ð¦ Yangi qoldiqni kiriting:"); await callback.answer()

@admin_router.message(EditVariantState.waiting_stock)
async def edit_v_stock_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try: stock = int(message.text.strip())
    except (ValueError, AttributeError): await message.answer("â Qoldiqni faqat raqam bilan kiriting."); return
    if stock < 0: await message.answer("â Qoldiq manfiy boâlishi mumkin emas."); return
    data = await state.get_data(); v = get_variant(data["variant_id"])
    if not v: await state.clear(); await message.answer("â Rang topilmadi."); return
    update_variant(data["variant_id"], v["color_name"], v["color_code"], v["image"], v["price"], stock)
    await state.clear(); await message.answer(f"â Rang qoldigâi oâzgartirildi: <b>{stock} dona</b>")

# ============================================================
# MAHSULOTNI OâCHIRISH
# ============================================================

@admin_router.callback_query(
    F.data.startswith("delete_product:")
)
async def delete_product_handler(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "â Ruxsat yoâq!",
            show_alert=True,
        )

        return

    product_id = callback.data.split(":", 1)[1]

    product = get_product(product_id)

    if not product:

        await callback.answer(
            "â Mahsulot topilmadi!",
            show_alert=True,
        )

        return

    try:

        delete_product(product_id)

    except Exception as e:

        print(
            "â DELETE PRODUCT ERROR:",
            repr(e),
        )

        await callback.answer(
            "â Oâchirishda xatolik!",
            show_alert=True,
        )

        return

    await callback.message.edit_text(
        "ð <b>Mahsulot oâchirildi.</b>",
        reply_markup=InlineKeyboardBuilder()
        .button(
            text="â¬ï¸ Mahsulotlar",
            callback_data="admin_products",
        )
        .as_markup(),
    )

    await callback.answer(
        "ð Mahsulot oâchirildi!"
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
            "â Ruxsat yoâq!",
            show_alert=True,
        )

        return

    orders = get_orders()

    builder = InlineKeyboardBuilder()

    if not orders:

        builder.button(
            text="â¬ï¸ Admin panel",
            callback_data="admin_back",
        )

        await callback.message.edit_text(
            "ð <b>BUYURTMALAR</b>\n\n"
            "Hozircha buyurtmalar yoâq.",
            reply_markup=builder.as_markup(),
        )

        await callback.answer()

        return

    for order in orders[:20]:

        status = order["status"]

        emoji = {
            "new": "ð",
            "accepted": "ð¢",
            "delivery": "ð",
            "delivered": "â",
            "cancelled": "ð´",
        }.get(status, "ð¦")

        builder.button(
            text=(
                f"{emoji} #{order['id']} â "
                f"{order['total']:,} soâm"
            ),
            callback_data=(
                f"admin_order:{order['id']}"
            ),
        )

    builder.button(
        text="â¬ï¸ Admin panel",
        callback_data="admin_back",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "ð <b>BUYURTMALAR</b>\n\n"
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
            "â Ruxsat yoâq!",
            show_alert=True,
        )

        return

    order_id = int(
        callback.data.split(":", 1)[1]
    )

    order = get_order(order_id)

    if not order:

        await callback.answer(
            "â Buyurtma topilmadi!",
            show_alert=True,
        )

        return

    items = get_order_items(order_id)

    text = (
        f"ð¦ <b>BUYURTMA #{order['id']}</b>\n\n"
    )

    for item in items:

        text += (
            f"â¢ {item['product_name']} Ã "
            f"{item['quantity']}\n"
            f"  ð° {item['subtotal']:,} soâm\n\n"
        )

    text += (
        f"ðµ <b>Jami:</b> "
        f"{order['total']:,} soâm\n\n"
        f"ð¤ <b>Ism:</b> {order['name']}\n"
        f"ð <b>Telefon:</b> {order['phone']}\n"
        f"ð <b>Manzil:</b> {order['address']}\n"
        f"ð <b>Telegram ID:</b> "
        f"{order['telegram_id']}\n\n"
        f"ð <b>Status:</b> "
        f"{order['status']}"
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="ð¢ Qabul qilish",
        callback_data=(
            f"order_status:accepted:{order_id}"
        ),
    )

    builder.button(
        text="ð Yetkazilmoqda",
        callback_data=(
            f"order_status:delivery:{order_id}"
        ),
    )

    builder.button(
        text="â Yetkazildi",
        callback_data=(
            f"order_status:delivered:{order_id}"
        ),
    )

    builder.button(
        text="â Bekor qilish",
        callback_data=(
            f"order_status:cancelled:{order_id}"
        ),
    )

    builder.button(
        text="â¬ï¸ Buyurtmalar",
        callback_data="admin_orders",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()

# ============================================================
# STATUS OâZGARTIRISH
# ============================================================

@admin_router.callback_query(
    F.data.startswith("order_status:")
)
async def order_status_handler(
    callback: CallbackQuery,
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "â Ruxsat yoâq!",
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
            "â STATUS ERROR:",
            repr(e),
        )

        await callback.answer(
            "â Statusni oâzgartirishda xatolik!",
            show_alert=True,
        )

        return

    status_names = {
        "accepted": "ð¢ QABUL QILINDI",
        "delivery": "ð YETKAZILMOQDA",
        "delivered": "â YETKAZILDI",
        "cancelled": "ð´ BEKOR QILINDI",
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
            "â Ruxsat yoâq!",
            show_alert=True,
        )

        return

    customers = get_customers()

    builder = InlineKeyboardBuilder()

    builder.button(
        text="â¬ï¸ Admin panel",
        callback_data="admin_back",
    )

    builder.adjust(1)

    if not customers:

        await callback.message.edit_text(
            "ð¥ <b>MIJOZLAR</b>\n\n"
            "Hozircha mijozlar yoâq.",
            reply_markup=builder.as_markup(),
        )

        await callback.answer()

        return

    text = "ð¥ <b>MIJOZLAR</b>\n\n"

    for customer in customers[:20]:

        text += (
            f"ð¤ <b>{customer['name'] or '-'}</b>\n"
            f"ð {customer['phone'] or '-'}\n"
            f"ð {customer['address'] or '-'}\n"
            f"ð {customer['telegram_id']}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()

# ==================================================
# STATISTIKA
# ==================================================

@admin_router.callback_query(
    F.data == "admin_stats"
)
async def admin_stats(
    callback: CallbackQuery,
):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "â Ruxsat yoâq!",
            show_alert=True,
        )
        return

    try:
        stats = get_statistics()

        text = (
            "ð <b>STATISTIKA</b>\n\n"
            f"ð¦ Mahsulotlar: <b>{stats['products']}</b>\n"
            f"ð¥ Mijozlar: <b>{stats['customers']}</b>\n"
            f"ð Buyurtmalar: <b>{stats['orders']}</b>\n"
            f"â Yetkazilgan: <b>{stats['delivered']}</b>\n"
            f"ð° Tushum: <b>{stats['revenue']:,} soâm</b>"
        )

        builder = InlineKeyboardBuilder()

        builder.button(
            text="ð Yangilash",
            callback_data="admin_stats",
        )

        builder.button(
            text="â¬ï¸ Admin panel",
            callback_data="admin_back",
        )

        builder.adjust(1)

        try:
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
            )

        except Exception as e:

            # Telegram:
            # message is not modified
            # xatosini e'tiborsiz qoldiramiz
            if "message is not modified" not in str(e):
                raise

        await callback.answer(
            "ð Statistika yangilandi!"
        )

    except Exception as e:

        print(
            "â ADMIN STATISTICS ERROR:",
            repr(e),
        )

        await callback.answer(
            "â Statistikani yuklashda xatolik!",
            show_alert=True,
        )