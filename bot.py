from flask import Flask
from threading import Thread

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot Running"

def run():
    app_web.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
import os
import pandas as pd
import yfinance as yf
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = os.getenv("8672236452:AAED45zNAWTyjTeZ1FBHdPZpfsrPsV1abmk")
CHAT_ID = os.getenv("5373263577")

DEFAULT_PAIR = os.getenv("PAIR", "EURJPY=X")
INTERVAL = os.getenv("INTERVAL", "1m")

auto_signal = False
current_pair = DEFAULT_PAIR


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def get_signal(pair):
    data = yf.download(pair, period="1d", interval=INTERVAL, progress=False)

    if data.empty or len(data) < 40:
        return "тЪая╕П Market data ржкрж╛ржУрзЯрж╛ ржпрж╛рзЯржирж┐ред ржкрж░рзЗ ржЪрзЗрж╖рзНржЯрж╛ ржХрж░рзБржиред"

    data["EMA9"] = data["Close"].ewm(span=9).mean()
    data["EMA21"] = data["Close"].ewm(span=21).mean()
    data["RSI"] = calculate_rsi(data["Close"])

    last = data.iloc[-1]

    close = float(last["Close"])
    open_price = float(last["Open"])
    ema9 = float(last["EMA9"])
    ema21 = float(last["EMA21"])
    rsi = float(last["RSI"])

    support = float(data["Low"].tail(20).min())
    resistance = float(data["High"].tail(20).max())

    bullish = close > open_price
    bearish = close < open_price

    signal = "WAIT"
    confidence = 50
    reason = []

    if ema9 > ema21 and bullish and rsi > 52:
        signal = "UP ЁЯЯв"
        confidence = 68
        reason = ["EMA9 EMA21 ржПрж░ ржЙржкрж░рзЗ", "Bullish candle", "RSI 52 ржПрж░ ржЙржкрж░рзЗ"]

    elif ema9 < ema21 and bearish and rsi < 48:
        signal = "DOWN ЁЯФ┤"
        confidence = 68
        reason = ["EMA9 EMA21 ржПрж░ ржирж┐ржЪрзЗ", "Bearish candle", "RSI 48 ржПрж░ ржирж┐ржЪрзЗ"]

    else:
        reason = ["Clear confirmation ржирзЗржЗ", "Market risky / sideways рж╣рждрзЗ ржкрж╛рж░рзЗ"]

    return f"""
ЁЯУК Trading Signal

ЁЯТ▒ Pair: {pair}
тП▒ Timeframe: {INTERVAL}

ЁЯУИ Signal: {signal}
ЁЯОп Confidence: {confidence}%

ЁЯТ░ Price: {close:.3f}
ЁЯЯв Support: {support:.3f}
ЁЯФ┤ Resistance: {resistance:.3f}
ЁЯУК RSI: {rsi:.2f}

ЁЯХп Reason:
- {chr(10).join(reason)}

тЪая╕П Demo account ржП test ржХрж░рзБржиред Guaranteed signal ржирж╛ред
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "тЬЕ Trading Signal Bot ржЪрж╛рж▓рзБ рж╣рзЯрзЗржЫрзЗред\n\n"
        "Commands:\n"
        "/signal - ржПржЦржиржХрж╛рж░ signal\n"
        "/pair EURJPY=X - pair change\n"
        "/auto_on - auto signal ржЪрж╛рж▓рзБ\n"
        "/auto_off - auto signal ржмржирзНржз\n"
        "/status - current status"
    )


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_signal(current_pair)
    await update.message.reply_text(msg)


async def set_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_pair

    if not context.args:
        await update.message.reply_text("Example:\n/pair EURJPY=X")
        return

    current_pair = context.args[0].upper()
    await update.message.reply_text(f"тЬЕ Pair set рж╣рзЯрзЗржЫрзЗ: {current_pair}")


async def auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_signal
    auto_signal = True
    await update.message.reply_text("тЬЕ Auto signal ржЪрж╛рж▓рзБ рж╣рзЯрзЗржЫрзЗред")


async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_signal
    auto_signal = False
    await update.message.reply_text("тЫФ Auto signal ржмржирзНржз рж╣рзЯрзЗржЫрзЗред")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ЁЯУМ Current Pair: {current_pair}\n"
        f"тП▒ Interval: {INTERVAL}\n"
        f"ЁЯдЦ Auto Signal: {'ON' if auto_signal else 'OFF'}"
    )


async def auto_job(app):
    if auto_signal and CHAT_ID:
        msg = get_signal(current_pair)
        await app.bot.send_message(chat_id=CHAT_ID, text=msg)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("pair", set_pair))
    app.add_handler(CommandHandler("auto_on", auto_on))
    app.add_handler(CommandHandler("auto_off", auto_off))
    app.add_handler(CommandHandler("status", status))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_job, "interval", minutes=1, args=[app])
    scheduler.start()

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
