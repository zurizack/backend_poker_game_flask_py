# # poker_server/game/services/table_service_oop.py

# import logging
# from typing import Optional
# from poker_server.game.engine.table_oop import Table # ודא שזה poker_server.game.engine.table_oop
# from backend.poker_server.state.public_table_state import get_table_state, set_table_state, delete_table_state # ייבוא מ-state/table.py המאוחד

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# class TableService:
#     """
#     Provides services for managing Table objects, including loading from and saving to Redis.
#     """
#     def get_or_create_table_state(self, table_id: str, # כפי שתיקנו, table_id הוא str
#                                   max_players: int = 6, 
#                                   small_blind: int = 10, 
#                                   big_blind: int = 20) -> Table:
#         """
#         Attempts to load a Table object from Redis. If not found, creates a new one.
#         :param table_id: The ID of the table.
#         :param max_players: Default max players for a new table.
#         :param small_blind: Default small blind for a new table.
#         :param big_blind: Default big blind for a new table.
#         :return: A Table object (either loaded or newly created).
#         """
#         table = get_table_state(table_id)
#         if table is None:
#             logger.info(f"Table {table_id} not found in Redis. Creating new table.")
#             table = Table(table_id, max_players, small_blind, big_blind)
#             # בשלב זה לא נשמור אוטומטית ביצירה, ה-handler יעשה זאת לאחר פעולה
#         return table

#     def save_table_state(self, table_obj: Table):
#         """
#         Saves the current state of a Table object to Redis.
#         :param table_obj: The Table object to save.
#         """
#         set_table_state(table_obj)

#     def delete_table(self, table_id: str):
        """
        Deletes a table's state from Redis.
        :param table_id: The ID of the table to delete.
        """
        delete_table_state(table_id)