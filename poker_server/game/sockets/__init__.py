# poker_server/game/sockets/__init__.py

def register_socket_handlers(socketio):
    """
    Registers the Socket.IO handlers for the game, now using the OOP listener.
    """
    # Import the new function from the new file socket_listener_oop.py
    from backend.poker_server.game.sockets.socket_listener_oop import register_handlers_oop

    # Call the new function
    register_handlers_oop(socketio)
