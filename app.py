import os
import requests
from flask import Flask, request

TOKEN = os.environ["BOT_TOKEN"]
MY_CHAT_ID = os.environ.get("MY_CHAT_ID", "")
CRON_SECRET = os.environ.get("CRON_SECRET", "")
RATE_OFFICIAL = float(os.environ.get("RATE_OFFICIAL", "133.6"))
RATE_PARALLEL = float(os.environ.get("RATE_PARALLEL", "240"))
OUNCE_TO_GRAM = 31.1035
TG = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)


def gold_usd_per_ounce():
    r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
    return float(r.json()["price"])


def price_message():
    oz = gold_usd_per_ounce()
    g = oz / OUNCE_TO_GRAM
    return (
        f"يا سيدي المحترم ويا قاهر البحار السبع.🥇\n"
        f"سعر الذهب الآن🟡\n"
        f"الأونصة: {oz:,.2f} دولار💵\n"
        f"الغرام (سعر رسمي): {g * RATE_OFFICIAL:,.0f} دج\n"
        f"الغرام (سوق موازية): {g * RATE_PARALLEL:,.0f} دج"
    )


def send(chat_id, text):
    requests.post(f"{TG}/sendMessage",
                  json={"chat_id": chat_id, "text": text}, timeout=10)


@app.route("/")
def home():
    return "ok"


@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    msg = (request.get_json(silent=True) or {}).get("message") or {}
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    if chat_id and text.startswith("/gold"):
        try:
            send(chat_id, price_message())
        except Exception:
            send(chat_id, "تعذّر جلب السعر الآن، حاول بعد قليل.")
    return "ok"


@app.route("/morning")
def morning():
    # يستدعيه cron-job.org كل صباح في الثامنة
    if not CRON_SECRET or request.args.get("key") != CRON_SECRET:
        return "forbidden", 403
    try:
        send(MY_CHAT_ID, price_message())
        return "sent"
    except Exception:
        return "error", 500
