
# # poker_sever/game/services/table_service.py

# from poker_server.state.table import get_table_state, set_table_state
# from poker_server.models.poker_table import PokerTable
# from poker_server import db


# def get_or_create_table_state(table_id):
#     state = get_table_state(table_id)
#     if state is None:
#         # קח את הנתונים מהDB
#         table = db.session.query(PokerTable).filter_by(id=table_id).first()
#         if not table:
#             # שולחן לא קיים בDB - תקבל כאן החלטה: error? יצירת שולחן דיפולטי?  
#             raise Exception(f"Table with id {table_id} not found in DB")

#         # צור את המצב בהתבסס על הנתונים מהDB
#         state = {
#             "name": table.name,
#             "max_players": table.max_players,
#             "small_blind": table.small_blind,
#             "big_blind": table.big_blind,
#             "dealer_position":None,
#             "players": [{"seat": i+1, "player_id": None, "nickname": None, "chips": 0} for i in range(table.max_players)],
#             "pot": 0,
#             "status": "waiting"
#         }
#         set_table_state(table_id, state)
#     return state










