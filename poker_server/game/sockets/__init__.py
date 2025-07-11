# # poker_server/game/sockets/__init__.py


# def register_socket_handlers(socketio):

#     from poker_server.game.sockets.socket_listener import register_handlers

#     register_handlers(socketio)


# poker_server/game/sockets/__init__.py

def register_socket_handlers(socketio):
    """
    Registers the Socket.IO handlers for the game, now using the OOP listener.
    """
    # ייבוא הפונקציה החדשה מהקובץ החדש socket_listener_oop.py
    from backend.poker_server.game.sockets.socket_listener_oop import register_handlers_oop

    # קוראים לפונקציה החדשה
    register_handlers_oop(socketio)
    