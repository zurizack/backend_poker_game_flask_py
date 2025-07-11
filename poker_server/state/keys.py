# # state/keys.py


# state/keys.py

def get_public_table_state_key(table_id: str) -> str:
    """מחזיר את המפתח עבור ה-Hash של מצב השולחן הציבורי."""
    return f"poker:table:{table_id}:public"





