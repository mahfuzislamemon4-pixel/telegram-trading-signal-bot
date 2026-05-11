import os
import requests
import yfinance as yf
import pandas as pd

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PAIR = os.getenv("PAIR", "EURJPY=X")
INTERVAL = os.getenv("INTERVAL", "1m")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data, timeout=20)

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def analyze_market():
    data = yf.download(
        PAIR,
        period="1d",
        interval=INTERVAL,
        progress=False
    )

    if data.empty or len(data) < 30:
        return "WAIT", 0, "Market data পাওয়া যায়নি বা candle কম।"

    data["EMA_9"] = data["Close"].ewm(span=9).mean()
    data["EMA_21"] = data["Close"].ewm(span=21).mean()
    data["RSI"] = rsi(data["Close"])

    last = data.iloc[-1]
    prev = data.iloc[-2]

    close = float(last["Close"])
    open_price = float(last["Open"])
    ema9 = float(last["EMA_9"])
    ema21 = float(last["EMA_21"])
    rsi_value = float(last["RSI"])

    support = float(data["Low"].tail(20).min())
    resistance = float(data["High"].tail(20).max())

    bullish_candle = close > open_price
    bearish_candle = close < open_price

    signal = "WAIT"
    confidence = 50
    reasons = []

    if ema9 > ema21 and bullish_candle and rsi_value > 50:
        signal = "UP"
        confidence = 68
        reasons.append("EMA 9 > EMA 21")
        reasons.append("Bullish candle")
        reasons.append("RSI 50 এর উপরে")

    elif ema9 < ema21 and bearish_candle and rsi_value < 50:
        signal = "DOWN"
        confidence = 68
        reasons.append("EMA 9 < EMA 21")
        reasons.append("Bearish candle")
        reasons.append("RSI 50 এর নিচে")

    else:
        reasons.append("Clear confirmation নেই")

    message = f"""
📊 <b>Trading Signal</b>

💱 Pair: <b>{PAIR}</b>
⏱ Timeframe: <b>{INTERVAL}</b>

📈 Signal: <b>{signal}</b>
🎯 Confidence: <b>{confidence}%</b>

💰 Price: <b>{close:.3f}</b>
🟢 Support: <b>{support:.3f}</b>
🔴 Resistance: <b>{resistance:.3f}</b>
📊 RSI: <b>{rsi_value:.2f}</b>

🕯 Reason:
- """ + "\n- ".join(reasons) + """

⚠️ Note: এটা guaranteed signal না। Demo account এ test করুন।
"""
    return message

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("BOT_TOKEN বা CHAT_ID missing")

    result = analyze_market()
    send_message(result)
