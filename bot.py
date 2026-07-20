import os
import asyncio
import threading
import time

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
# НАСТРОЙКИ
# =====================

TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "fit.siren")

GIFTS = {
    "Rose":   {"points": 1,  "team": "girls"},
    "TikTok": {"points": 1,  "team": "boys"},
}

scores = {"girls": 0, "boys": 0}
score