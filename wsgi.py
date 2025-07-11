# wsgi.py
import gevent.monkey
gevent.monkey.patch_all()

from poker_server import create_app, socketio

# יצירת מופע האפליקציה.
# Gunicorn יטען את הקובץ הזה ויחפש משתנה בשם 'app' כדי להפעיל את השרת.
app = create_app()

# אופציונלי: אם אתה רוצה להפעיל את Socket.IO דרך Gunicorn,
# וודא ש-socketio מאותחל עם האפליקציה ב-create_app.
# אין צורך להריץ כאן socketio.run(), Gunicorn מטפל בזה.