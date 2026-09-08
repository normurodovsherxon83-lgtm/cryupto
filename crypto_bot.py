import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = "8806163133:AAHn5N0dY79lpj4sBEi1WGce2jvWPb_DQcE"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_HISTORY_URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart"
QUICKCHART_URL = "https://quickchart.io/chart"
CONTACT_URL = "https://t.me/axgrti"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COINS = [
    ("bitcoin", "Bitcoin", "BTC"),
    ("ethereum", "Ethereum", "ETH"),
    ("the-open-network", "Toncoin", "TON"),
    ("tether", "Tether", "USDT"),
    ("binancecoin", "BNB", "BNB"),
    ("ripple", "XRP", "XRP"),
    ("solana", "Solana", "SOL"),
    ("dogecoin", "Dogecoin", "DOGE"),
    ("cardano", "Cardano", "ADA"),
    ("tron", "Tron", "TRX"),
]

COIN_BY_ID = {c[0]: c for c in COINS}


def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("Kripto narxlari", callback_data="menu:coins")],
        [InlineKeyboardButton("7 kunlik natija", callback_data="menu:chart")],
        [InlineKeyboardButton("Murojaat", url=CONTACT_URL)],
    ]
    return InlineKeyboardMarkup(buttons)


def coins_keyboard(prefix):
    buttons = []
    row = []
    for coin_id, name, symbol in COINS:
        label = f"{name} ({symbol})"
        data = f"{prefix}:{coin_id}"
        row.append(InlineKeyboardButton(label, callback_data=data))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Orqaga", callback_data="menu:main")])
    return InlineKeyboardMarkup(buttons)


def get_price(coin_id: str):
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    resp = requests.get(COINGECKO_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get(coin_id)


def get_history(coin_id: str):
    url = COINGECKO_HISTORY_URL.format(id=coin_id)
    params = {"vs_currency": "usd", "days": "7"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("prices", [])


def build_chart_url(coin_id: str, name: str, prices):
    labels = []
    values = []
    step = max(1, len(prices) // 20)
    for i in range(0, len(prices), step):
        point = prices[i]
        values.append(round(point[1], 4))
        labels.append(str(i))

    chart_config = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": name,
                "data": values,
                "borderColor": "blue",
                "fill": False,
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": name + " - 7 kunlik narx (USD)"
            }
        }
    }

    import json
    import urllib.parse
    encoded = urllib.parse.quote(json.dumps(chart_config))
    url = QUICKCHART_URL + "?c=" + encoded
    return url


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Assalomu alaykum!"
    text += "\n\n"
    text += "Kerakli bolimni tanlang:"
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu:coins":
        text = "Kripto narxlari"
        text += "\n\n"
        text += "Valyutani tanlang:"
        try:
            await query.edit_message_text(text, reply_markup=coins_keyboard("price"))
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
        return

    if query.data == "menu:chart":
        text = "7 kunlik natija"
        text += "\n\n"
        text += "Valyutani tanlang:"
        try:
            await query.edit_message_text(text, reply_markup=coins_keyboard("chart"))
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
        return

    if query.data == "menu:main":
        text = "Assalomu alaykum!"
        text += "\n\n"
        text += "Kerakli bolimni tanlang:"
        try:
            await query.edit_message_text(text, reply_markup=main_menu_keyboard())
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
        return


async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("price:"):
        return

    coin_id = query.data.split(":", 1)[1]
    coin_info = COIN_BY_ID.get(coin_id)
    if not coin_info:
        return

    _, name, symbol = coin_info

    try:
        price_data = get_price(coin_id)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        try:
            msg = "Kechirasiz, narxni olishda xatolik."
            await query.edit_message_text(msg, reply_markup=coins_keyboard("price"))
        except BadRequest:
            pass
        return

    if not price_data:
        try:
            msg = "Malumot topilmadi."
            await query.edit_message_text(msg, reply_markup=coins_keyboard("price"))
        except BadRequest:
            pass
        return

    usd = price_data.get("usd")
    change = price_data.get("usd_24h_change", 0)
    if change > 0:
        arrow = "UP"
    elif change < 0:
        arrow = "DOWN"
    else:
        arrow = "SAME"

    line1 = f"{name} ({symbol})"
    line2 = f"USD: ${usd:,.2f}"
    line4 = f"24h: {arrow} {change:+.2f}%"
    line5 = "Boshqa valyutani tanlang:"
    text = line1 + "\n\n" + line2 + "\n" + line4 + "\n\n" + line5

    try:
        await query.edit_message_text(text, reply_markup=coins_keyboard("price"))
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def chart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("chart:"):
        return

    coin_id = query.data.split(":", 1)[1]
    coin_info = COIN_BY_ID.get(coin_id)
    if not coin_info:
        return

    _, name, symbol = coin_info

    try:
        prices = get_history(coin_id)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Kechirasiz, grafikni olishda xatolik.",
            reply_markup=coins_keyboard("chart"),
        )
        return

    if not prices:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Malumot topilmadi.",
            reply_markup=coins_keyboard("chart"),
        )
        return

    chart_url = build_chart_url(coin_id, f"{name} ({symbol})", prices)

    caption = f"{name} ({symbol}) - 7 kunlik natija"

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=chart_url,
        caption=caption,
        reply_markup=coins_keyboard("chart"),
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="^menu:"))
    app.add_handler(CallbackQueryHandler(price_handler, pattern="^price:"))
    app.add_handler(CallbackQueryHandler(chart_handler, pattern="^chart:"))
    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
