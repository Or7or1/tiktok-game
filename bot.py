import os
import threading

from flask import Flask, render_template
from flask_socketio import SocketIO

from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent, ConnectEvent


# =====================
# FLASK
# =====================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret!")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)


# =====================
# SETTINGS
# =====================

TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "fit.siren")

GIFTS = {
    "Rose": {
        "points": 1,
        "team": "girls"
    },
    "TikTok": {
        "points": 1,
        "team": "boys"
    },
}

scores = {
    "girls": 0,
    "boys": 0
}

score_lock = threading.Lock()


# =====================
# WEB PAGE
# =====================

@app.route("/")
def index():
    return render_template("overlay.html")


@socketio.on("connect")
def handle_connect():
    print("🌐 Overlay подключён")
    socketio.emit("score_update", scores)


# =====================
# TIKTOK BOT
# =====================

def run_tiktok():
    print(f"🔎 Пытаюсь подключиться к TikTok: @{TIKTOK_USERNAME}")

    client = TikTokLiveClient(unique_id=TIKTOK_USERNAME)

    @client.on(ConnectEvent)
    async def on_connect(event):
        print("🔥 CONNECT EVENT ПОЛУЧЕН")
        print(f"✅ Подключено к TikTok LIVE: @{TIKTOK_USERNAME}")

    @client.on(GiftEvent)
    async def on_gift(event):
        gift_name = event.gift.name
        username = event.user.nickname
        count = event.gift.repeat_count or 1

        print(f"🎁 {username}: {gift_name} x{count}")

        if gift_name not in GIFTS:
            print(f"⚠️ Неизвестный подарок: {gift_name}")
            return

        gift_data = GIFTS[gift_name]
        points = gift_data["points"] * count
        team = gift_data["team"]

        with score_lock:
            scores[team] += points
            current_scores = {
                "girls": scores["girls"],
                "boys": scores["boys"]
            }

        print(f"🔥 {team}: +{points}")
        print(f"📊 Счёт: {scores}")

        socketio.emit(
            "score_update",
            {
                "girls": current_scores["girls"],
                "boys": current_scores["boys"],
                "event": {
                    "username": username,
                    "gift": gift_name,
                    "points": points,
                    "team": team,
                    "count": count
                }
            }
        )

    print("⏳ Запускаю TikTok клиент...")

    try:
        client.run()
    except Exception as e:
        print("❌ TikTok ошибка:", repr(e))


# =====================
# START
# =====================

if __name__ == '__main__':
    tiktok_thread = threading.Thread(
        target=run_tiktok,
        daemon=True
    )
    tiktok_thread.start()

    print("🚀 TikTok Game запущен")

    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 5000)),
        allow_unsafe_werkzeug=True
    )