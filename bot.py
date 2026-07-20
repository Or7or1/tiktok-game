import os
import asyncio
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

async def run_tiktok_async():
    print("🟢 run_tiktok_async ЗАПУЩЕН")
    print(f"🔎 Пытаюсь подключиться к TikTok: @{TIKTOK_USERNAME}")

    try:
        print("🔧 Создаю TikTokLiveClient...")
        client = TikTokLiveClient(unique_id=TIKTOK_USERNAME)
        print("✅ TikTokLiveClient создан!")
    except Exception as e:
        print(f"💥 Ошибка создания клиента: {repr(e)}")
        return

    @client.on(ConnectEvent)
    async def on_connect(event):
        print("🔥 CONNECT EVENT ПОЛУЧЕН")

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

        socketio.emit("score_update", {
            "girls": current_scores["girls"],
            "boys": current_scores["boys"],
            "event": {
                "username": username,
                "gift": gift_name,
                "points": points,
                "team": team,
                "count": count
            }
        })

    print("🔁 Начинаю цикл подключения...")
    while True:
        try:
            print("⏳ Проверяю эфир...")

            is_live = await client.is_live()
            print(f"📡 Эфир идёт: {is_live}")

            if not is_live:
                print("😴 Эфир не идёт. Жду 30 секунд...")
                await asyncio.sleep(30)
                continue

            print("🚀 Подключаюсь к эфиру...")
            await client.start()

        except Exception as e:
            print(f"❌ TikTok ошибка: {repr(e)}")
            print("🔄 Повторная попытка через 30 секунд...")
            await asyncio.sleep(30)


def run_tiktok():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("✅ asyncio loop создан")
        loop.run_until_complete(run_tiktok_async())
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА в run_tiktok: {repr(e)}")

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