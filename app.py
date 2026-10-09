import os
import random
import threading
import telebot
from telebot import types

# =========================================================
# I-Beam™ Bot — НАСТРОЙКИ
# =========================================================
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

CHANNEL_URL = "https://t.me/beamcorporation"

# Положи файл ibeam.png в ту же папку, что и bot.py.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_PATH = os.path.join(BASE_DIR, "ibeam.png")

STAR_AMOUNTS = (25, 50, 75, 100)

bot = telebot.TeleBot(TOKEN)
user_messages = {}


# =========================================================
# УЧЁТ И УДАЛЕНИЕ СООБЩЕНИЙ
# =========================================================
def remember(chat_id, message):
    user_messages.setdefault(chat_id, set()).add(message.message_id)


def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass
    if chat_id in user_messages:
        user_messages[chat_id].discard(message_id)


def clear_bot_messages(chat_id):
    for message_id in list(user_messages.get(chat_id, set())):
        safe_delete(chat_id, message_id)
    user_messages.pop(chat_id, None)


# =========================================================
# КЛАВИАТУРЫ
# =========================================================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("🚪 Выйти", callback_data="exit"),
        types.InlineKeyboardButton("📢 Наш ТГК", url=CHANNEL_URL),
    )
    markup.row(
        types.InlineKeyboardButton("💸 Поддержать", callback_data="support")
    )
    markup.row(
        types.InlineKeyboardButton("😈 НЕ НАЖИМАТЬ", callback_data="random")
    )
    return markup


def stars_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("⭐ 25 Stars", callback_data="stars_25"),
        types.InlineKeyboardButton("⭐ 50 Stars", callback_data="stars_50"),
    )
    markup.row(
        types.InlineKeyboardButton("⭐ 75 Stars", callback_data="stars_75"),
        types.InlineKeyboardButton("⭐ 100 Stars", callback_data="stars_100"),
    )
    markup.row(
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back")
    )
    return markup


def edit_message_menu(chat_id, message_id, text, markup):
    try:
        bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=text,
            reply_markup=markup,
        )
        return
    except Exception:
        pass

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=markup,
        )
        return
    except Exception:
        pass

    sent = bot.send_message(chat_id, text, reply_markup=markup)
    remember(chat_id, sent)


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================
def send_main_menu(chat_id):
    text = (
        "👋 Привет! Добро пожаловать в I-Beam™!\n\n"
        "Здесь ты можешь поддержать наш проект и найти наш "
        "Telegram-канал.\n\n"
        "Выбирай, что тебя интересует, с помощью кнопок ниже. 🖤"
    )

    if os.path.isfile(PHOTO_PATH):
        with open(PHOTO_PATH, "rb") as photo:
            sent = bot.send_photo(
                chat_id,
                photo,
                caption=text,
                reply_markup=main_menu(),
            )
    else:
        sent = bot.send_message(
            chat_id,
            text + "\n\nℹ️ Для отображения логотипа положи файл "
            "ibeam.png рядом с bot.py.",
            reply_markup=main_menu(),
        )

    remember(chat_id, sent)


@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    clear_bot_messages(chat_id)
    send_main_menu(chat_id)


# =========================================================
# ОБРАБОТКА КНОПОК
# =========================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data or ""

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if data == "exit":
        clear_bot_messages(chat_id)
        safe_delete(chat_id, message_id)
        return

    if data == "support":
        edit_message_menu(
            chat_id,
            message_id,
            "🖤 Поддержи развитие I-Beam™!\n\n"
            "Выбери количество Telegram Stars для добровольного доната:",
            stars_menu(),
        )
        return

    if data == "back":
        for old_message_id in list(user_messages.get(chat_id, set())):
            if old_message_id != message_id:
                safe_delete(chat_id, old_message_id)
        user_messages[chat_id] = {message_id}

        text = (
            "👋 Привет! Добро пожаловать в I-Beam™!\n\n"
            "Здесь ты можешь поддержать наш проект и найти наш "
            "Telegram-канал.\n\n"
            "Выбирай, что тебя интересует, с помощью кнопок ниже. 🖤"
        )
        try:
            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=text,
                reply_markup=main_menu(),
            )
        except Exception:
            edit_message_menu(chat_id, message_id, text, main_menu())
        return

    if data.startswith("stars_"):
        try:
            amount = int(data.split("_", 1)[1])
        except (ValueError, IndexError):
            return

        if amount not in STAR_AMOUNTS:
            return

        prices = [
            types.LabeledPrice(
                label=f"Добровольный донат I-Beam™ — {amount} Stars",
                amount=amount,
            )
        ]

        try:
            invoice = bot.send_invoice(
                chat_id=chat_id,
                title="Поддержка I-Beam™",
                description=(
                    f"Добровольная поддержка проекта I-Beam™: "
                    f"{amount} Telegram Stars."
                ),
                invoice_payload=f"ibeam_donation_{amount}",
                provider_token="",
                currency="XTR",
                prices=prices,
            )
            remember(chat_id, invoice)
        except Exception as error:
            sent = bot.send_message(
                chat_id,
                "Не удалось создать счёт. Попробуй ещё раз позже.",
            )
            remember(chat_id, sent)
            print("Ошибка создания счёта:", repr(error))
        return

    if data == "random":
        safe_delete(chat_id, message_id)
        emoji = random.choice(["🥵", "😡", "🤬"])
        sent = bot.send_message(chat_id, emoji)
        remember(chat_id, sent)

        timer = threading.Timer(
            2.0,
            safe_delete,
            args=(chat_id, sent.message_id),
        )
        timer.daemon = True
        timer.start()
        return


# =========================================================
# ПЛАТЕЖИ TELEGRAM STARS
# =========================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_handler(query):
    try:
        valid_payloads = {
            f"ibeam_donation_{amount}" for amount in STAR_AMOUNTS
        }
        if query.invoice_payload not in valid_payloads or query.currency != "XTR":
            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Не удалось проверить счёт. Попробуй ещё раз.",
            )
            return

        expected_amount = int(query.invoice_payload.rsplit("_", 1)[1])
        if query.total_amount != expected_amount:
            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Сумма счёта не совпадает. Попробуй ещё раз.",
            )
            return

        bot.answer_pre_checkout_query(query.id, ok=True)
    except Exception as error:
        print("Ошибка проверки платежа:", repr(error))
        try:
            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Не удалось проверить платёж. Попробуй позже.",
            )
        except Exception:
            pass


@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    payment = message.successful_payment

    if payment.currency == "XTR":
        amount = payment.total_amount
        sent = bot.send_message(
            message.chat.id,
            "🖤 Спасибо за поддержку I-Beam™!\n\n"
            f"Получено: ⭐ {amount} Stars\n"
            "Твоя поддержка очень важна для нас!",
        )
        remember(message.chat.id, sent)


# =========================================================
# ЗАПУСК (для Render)
# =========================================================
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "I-Beam Bot is alive"


def run_bot():
    if not TOKEN.strip():
        print("ОШИБКА: токен не найден в переменных окружения.")
        return
    print("I-Beam™ Bot запускается...")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)