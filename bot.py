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

TIKTOK_USERNAME = os.getenv(
    "TIKTOK_USERNAME",
    "fit.siren"
)


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

    socketio.emit(
        "score_update",
        scores
    )


# =====================
# TIKTOK BOT
# =====================

def run_tiktok():

    try:

        client = TikTokLiveClient(
            unique_id=TIKTOK_USERNAME
        )


        @client.on(ConnectEvent)
        async def on_connect(event):

            print(
                f"✅ Подключено к TikTok LIVE: @{TIKTOK_USERNAME}"
            )


        @client.on(GiftEvent)
        async def on_gift(event):

            gift_name = event.gift.name
            username = event.user.nickname

            count = (
                event.gift.repeat_count
                or 1
            )


            gift_type = getattr(
                event.gift,
                "gift_type",
                None
            )

            repeat_end = getattr(
                event.gift,
                "repeat_end",
                None
            )


            print(
                f"🎁 {username}: {gift_name} x{count}"
            )


            # ждём окончания серии
            if gift_type == 1 and repeat_end != 1:
                return


            if gift_name not in GIFTS:

                print(
                    f"⚠️ Неизвестный подарок: {gift_name}"
                )

                return



            gift = GIFTS[gift_name]

            points = (
                gift["points"]
                * count
            )

            team = gift["team"]



            with score_lock:

                scores[team] += points

                current_score = {
                    "girls": scores["girls"],
                    "boys": scores["boys"]
                }



            print(
                f"🔥 {team}: +{points}"
            )

            print(
                f"📊 Счёт: {current_score}"
            )



            socketio.emit(
                "score_update",
                {
                    **current_score,

                    "event": {
                        "username": username,
                        "gift": gift_name,
                        "points": points,
                        "team": team,
                        "count": count
                    }
                }
            )


        client.run()


    except Exception as e:

        print(
            "❌ Ошибка TikTok клиента:",
            e
        )



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