# poker_server/state/table.py

# from poker_server.state.client import redis_client
# from poker_server.state.keys import get_player_key, get_table_key
# import json



# def get_table_state(table_id):
#     key = get_table_key(table_id)
#     data = redis_client.get(key)
#     if data:
#         return json.loads(data)
#     return None

# def set_table_state(table_id, state):
#     key = get_table_key(table_id)
#     redis_client.set(key, json.dumps(state))

# def clear_table_players(table_id: str):
#     key =  get_player_key(table_id)
#     redis_client.delete(key)






