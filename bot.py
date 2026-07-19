from flask import Flask, render_template
from flask_socketio import SocketIO
from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent, ConnectEvent
import threading


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")


TIKTOK_USERNAME = "fit.siren"


GIFTS = {
    "Rose": {"points": 1, "team": "girls"},
    "TikTok": {"points": 1, "team": "boys"},
}


scores = {
    "girls": 0,
    "boys": 0
}


@app.route('/')
def index():
    return render_template('overlay.html')


@socketio.on('connect')
def handle_connect():
    socketio.emit('score_update', scores)


def run_tiktok():
    client = TikTokLiveClient(unique_id=TIKTOK_USERNAME)

    @client.on(ConnectEvent)
    async def on_connect(event):
        print(f"✅ Подключено к стриму {TIKTOK_USERNAME}")

    @client.on(GiftEvent)
    async def on_gift(event):
        gift_name = event.gift.name
        username = event.user.nickname
        count = event.gift.repeat_count or 1

        repeat_end = getattr(event.gift, "repeat_end", None)
        gift_type = getattr(event.gift, "gift_type", None)

        print(f"🎁 Подарок: {username} отправил {gift_name} x{count}")
        print(f"ℹ️ gift_type={gift_type}, repeat_end={repeat_end}")

        if gift_type == 1 and repeat_end != 1:
            print("⏳ Серия подарков ещё идёт, жду окончания...")
            return

        if gift_name not in GIFTS:
            print(f"⚠️ Подарок '{gift_name}' не прописан в GIFTS")
            return

        gift_data = GIFTS[gift_name]
        points = gift_data["points"] * count
        team = gift_data["team"]

        scores[team] += points

        print(f"✅ {team.upper()} +{points} | Счёт: {scores}")

        socketio.emit('score_update', {
            "girls": scores["girls"],
            "boys": scores["boys"],
            "event": {
                "username": username,
                "gift": gift_name,
                "points": points,
                "team": team,
                "count": count
            }
        })

    client.run()


if __name__ == '__main__':
    tiktok_thread = threading.Thread(target=run_tiktok, daemon=True)
    tiktok_thread.start()

    print("🌐 Сервер запущен: http://localhost:5000")
    print("📺 Открой этот адрес в TikTok Live Studio как Browser Source")

    socketio.run(app, host='0.0.0.0', port=5000)
