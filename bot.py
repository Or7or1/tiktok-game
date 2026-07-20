import sys
import os

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("=== БОТ ЗАПУСТИЛСЯ ===", flush=True)
print(f"Python версия: {sys.version}", flush=True)
print(f"PORT: {os.environ.get('PORT', 'не задан')}", flush=True)

import asyncio
import threading
import time

print("=== ИМПОРТЫ OK ===", flush=True)

from flask import Flask, render_template
from flask_socketio import SocketIO

print("=== FLASK ИМПОРТИРОВАН ===", flush=True)

from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent, ConnectEvent

print("=== TIKTOK ИМПОРТИРОВАН ===", flush=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret!")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

print("=== FLASK APP СОЗДАН ===", flush=True)

TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "fit.siren")

GIFTS = {
    "Rose":   {"points": 1, "team": "girls"},
    "TikTok": {"points": 1, "team": "boys"},
}

scores = {"girls": 0, "boys": 0}
score_lock = threading.Lock()

@app.route("/")
def index():
    return render_template("overlay.html")

@socketio.on("connect")
def handle_connect():
    print("🌐 Overlay подключён", flush=True)
    socketio.emit("score_update", scores)

async def run_tiktok_async():
    print("🟢 run_tiktok_async ЗАПУЩЕН", flush=True)

    while True:
        try:
            print("🔧 Создаю TikTokLiveClient...", flush=True)
            client = TikTokLiveClient(
                unique_id=TIKTOK_USERNAME,
                sign_api_key=os.getenv("EULERSTREAM_API_KEY", "")
            )
            print("✅ TikTokLiveClient создан!", flush=True)

            @client.on(ConnectEvent)
            async def on_connect(event):
                print(f"✅ Подключено к эфиру @{TIKTOK_USERNAME}", flush=True)

            @client.on(GiftEvent)
            async def on_gift(event):
                gift_name = event.gift.name
                username = event.user.nickname
                count = event.gift.repeat_count or 1

                print(f"🎁 {username}: {gift_name} x{count}", flush=True)

                if gift_name not in GIFTS:
                    print(f"⚠️ Неизвестный подарок: {gift_name}", flush=True)
                    return

                gift_data = GIFTS[gift_name]
                points = gift_data["points"] * count
                team = gift_data["team"]

                with score_lock:
                    scores[team] += points
                    current_scores = dict(scores)

                print(f"🔥 {team}: +{points} | Счёт: {scores}", flush=True)

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

            print("⏳ Проверяю идёт ли эфир...", flush=True)
            is_live = await client.is_live()
            print(f"📡 Эфир идёт: {is_live}", flush=True)

            if not is_live:
                print("😴 Эфир не идёт. Жду 30 секунд...", flush=True)
                await asyncio.sleep(30)
                continue

            print("🚀 Подключаюсь к эфиру...", flush=True)
            await client.start()

        except Exception as e:
            print(f"❌ Ошибка: {repr(e)}", flush=True)
            print("🔄 Повтор через 30 секунд...", flush=True)
            await asyncio.sleep(30)


def run_tiktok():
    try:
        print("⏰ Жду 5 секунд пока Flask запустится...", flush=True)
        time.sleep(5)
        print("🔁 Запускаю asyncio loop...", flush=True)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_tiktok_async())

    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА в run_tiktok: {repr(e)}", flush=True)


if __name__ == '__main__':
    print("🚀 TikTok Game запущен", flush=True)

    tiktok_thread = threading.Thread(target=run_tiktok, daemon=True)
    tiktok_thread.start()

    print("🌐 Запускаю Flask...", flush=True)

    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 10000)),
        allow_unsafe_werkzeug=True
    )