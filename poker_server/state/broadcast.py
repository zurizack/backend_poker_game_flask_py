      # poker_server/state/broadcast.py

# # from poker_server.state.active_player_state import get_all_players
# from poker_server.game.sockets.emitters import get_socketio

# def broadcast_players_update(table_id: int):
#     socketio = get_socketio()
#     players = get_all_players(table_id)
#     socketio.emit('players_update', {
#         "table_id": table_id,
#         "players": players
#     }, room = f"poker_table_{table_id}")


