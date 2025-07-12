# poker_server/main.py

import gevent.monkey
gevent.monkey.patch_all()

from dotenv import load_dotenv
import os
import logging

# ✅ הגדרת הלוגים — הכי מוקדם שאפשר
logging.basicConfig(
    level=logging.INFO,  # או DEBUG לצורך פיתוח
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
        # ניתן גם:
        # logging.FileHandler("logs/server.log", encoding="utf-8")
    ]
)

# load_dotenv(dotenv_path=os.path.join("poker_server", ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from . import create_app, socketio # ייבוא create_app ו-socketio

app = create_app() # יצירת האפליקציה, וכעת גם GameManager מאותחל בתוכה

if __name__ == '__main__':
    logging.info("run the poker server ... ")
    socketio.run(app, port=5000, debug=True, allow_unsafe_werkzeug=True)