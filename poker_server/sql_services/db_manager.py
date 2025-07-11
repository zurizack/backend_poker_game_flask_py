# poker_server/data/db_manager.py

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session # For session type hinting
from datetime import date

# --- Ensure these import paths are correct according to your project structure ---
# Flask-SQLAlchemy db object (from poker_server's __init__.py)
from .. import db 
# Database models
from ..models.user import User
from ..models.poker_table import PokerTable

# Configure logger for DBManager
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DBManager:
    """
    Manages interaction with the database using SQLAlchemy (based on Flask-SQLAlchemy).
    Responsible for saving and loading player and table data.
    Implements the Singleton Pattern to ensure a single instance of the manager.
    """
    _instance: Optional['DBManager'] = None # Type hint for the singleton instance

    def __new__(cls, flask_db_instance: Any):
        """
        Implements the Singleton pattern for DBManager.
        :param flask_db_instance: The initialized Flask-SQLAlchemy db object.
        """
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance._db = flask_db_instance
            logger.info("DBManager initialized successfully and using Flask-SQLAlchemy DB object.")
        return cls._instance

    def get_session(self) -> Session:
        """
        Returns the current Flask-SQLAlchemy database session.
        """
        return self._db.session

    # --- User Management ---

    def register_user(self, first_name: str, last_name: str, email: str, nickname: str, password: str, birthdate: Optional[date] = None, initial_chips: int = 1000) -> Optional[int]:
        """
        Registers a new user in the database.
        Returns the ID of the registered user, or None if the nickname/email is already taken.
        """
        session = self.get_session()
        try:
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                nickname=nickname,
                chips=initial_chips,
                birthdate=birthdate # Can be None
            )
            new_user.set_password(password) # Uses the existing method in the User model
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user) # Refresh the object to get the new ID
            logger.info(f"User '{nickname}' (ID: {new_user.id}) registered successfully.")
            return new_user.id
        except IntegrityError:
            session.rollback() # Rolls back changes if there's a uniqueness violation (nickname/email already exists)
            logger.warning(f"Error: Nickname or email for '{nickname}' already exists.")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error registering user '{nickname}': {e}", exc_info=True)
            return None
        finally:
            session.close() # Closes the session

    def authenticate_user(self, nickname: str, password: str) -> Optional[Dict]:
        """
        Authenticates a user and returns their basic data if authentication is successful.
        :return: A dictionary with user data (id, nickname, chips, is_admin) or None if authentication fails.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.nickname == nickname).first()

            if user:
                if user.check_password(password): # Uses the existing method in the User model
                    logger.info(f"User '{nickname}' authenticated successfully.")
                    return {
                        "id": user.id,
                        "nickname": user.nickname,
                        "chips": user.chips,
                        "is_admin": user.is_admin,
                        "first_name": user.first_name, # Added additional fields existing in the model
                        "last_name": user.last_name,
                        "email": user.email
                    }
                else:
                    logger.warning(f"Error: Incorrect password for '{nickname}'.")
                    return None
            else:
                logger.warning(f"Error: Username '{nickname}' not found.")
                return None
        except Exception as e:
            logger.error(f"Error authenticating user '{nickname}': {e}", exc_info=True)
            return None
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Fetches a User object from the database by its ID.
        Note: This method returns a User object directly, not a dictionary.
        """
        session = self.get_session()
        try:
            # Using get() for Primary Key is more efficient
            user = session.get(User, user_id) 
            if user:
                logger.debug(f"User {user_id} fetched successfully from DB: {user.nickname}.")
            else:
                logger.warning(f"User {user_id} not found in DB.")
            return user
        except Exception as e:
            logger.error(f"Error fetching user {user_id} from DB: {e}", exc_info=True)
            return None
        finally:
            session.close()

    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """
        Returns all user data from the DB by ID.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "nickname": user.nickname,
                    "chips": user.chips,
                    "is_admin": user.is_admin,
                    "birthdate": str(user.birthdate) if user.birthdate else None # Convert to string if exists
                }
            logger.warning(f"No user found with ID: {user_id}.")
            return None
        except Exception as e:
            logger.error(f"Error getting user data {user_id}: {e}", exc_info=True)
            return None
        finally:
            session.close()

    def save_user_changes(self, user: User):
        """
        Saves changes made to a User object (like chip updates).
        """
        session = self.get_session()
        try:
            # The user object should already be "attached" to the session if it was fetched from it.
            # If not, session.add(user) will add it.
            session.add(user) 
            session.commit()
            logger.debug(f"User {user.id} changes saved to DB. New chips: {user.chips}.")
        except Exception as e:
            session.rollback() 
            logger.error(f"Error saving user {user.id} changes to DB: {e}", exc_info=True)
        finally:
            session.close()

    def update_user_chips(self, user_id: int, new_chips_amount: int) -> bool:
        """
        Updates the chip amount of a user in the database.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.chips = new_chips_amount
                session.commit()
                logger.info(f"User {user_id} chips updated to: {new_chips_amount}.")
                return True
            logger.warning(f"Warning: No user found with ID {user_id} to update chips.")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating chips for user {user_id}: {e}", exc_info=True)
            return False
        finally:
            session.close()

    # --- Poker Table Management ---

    def get_table_data_for_server(self, table_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetches basic data about a specific poker table from the database.
        Returns a pure Python dictionary with table data, or None if the table is not found.
        (Moved from poker_server/sql_services/table_data.py)
        """
        logger.info(f"DBManager: Fetching basic table data for table ID: {table_id}.")
        session = self.get_session()
        try:
            # Using get() for Primary Key is efficient
            table = session.query(PokerTable).get(table_id) 
            
            if not table:
                logger.warning(f"DBManager: Table {table_id} not found in SQL database.")
                return None
            
            return {
                'id': table.id, # Remains int as defined in the model
                'name': table.name,
                'max_players': table.max_players,
                'small_blind': table.small_blind,
                'big_blind': table.big_blind,
                'created_at': str(table.created_at) # Convert to string for convenient representation
            }
        except Exception as e:
            session.rollback() # Ensure rollback if there's an error
            logger.error(f"DBManager: Error fetching table {table_id} from SQL DB: {e}", exc_info=True)
            return None
        finally:
            session.close()

    def create_poker_table(self, name: str, small_blind: int, big_blind: int, max_players: int = 9) -> Optional[int]:
        """
        Creates a new poker table in the database.
        Returns the ID of the created table, or None if an error occurred.
        """
        session = self.get_session()
        try:
            new_table = PokerTable(
                name=name,
                small_blind=small_blind,
                big_blind=big_blind,
                max_players=max_players
            )
            session.add(new_table)
            session.commit()
            session.refresh(new_table) # To get the new ID
            logger.info(f"Poker table '{name}' (ID: {new_table.id}) created successfully.")
            return new_table.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating poker table '{name}': {e}", exc_info=True)
            return None
        finally:
            session.close()

    def get_all_poker_tables(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all existing poker tables in the database.
        """
        session = self.get_session()
        tables_data = []
        try:
            tables = session.query(PokerTable).all()
            for table in tables:
                tables_data.append({
                    'id': table.id,
                    'name': table.name,
                    'max_players': table.max_players,
                    'small_blind': table.small_blind,
                    'big_blind': table.big_blind,
                    'created_at': str(table.created_at)
                })
            logger.info(f"Fetched {len(tables_data)} poker tables from the database.")
            return tables_data
        except Exception as e:
            logger.error(f"Error fetching all poker tables: {e}", exc_info=True)
            return []
        finally:
            session.close()

    # ... (additional methods can be added here as needed, e.g., update_table_settings, delete_table) ...
