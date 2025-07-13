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

    def register_user(self, first_name: str, last_name: str, email: str, username: str, nickname: str, password: str, birthdate: Optional[date] = None, initial_balance: float = 10000.0) -> Optional[int]: # ✅ Added username, nickname
        """
        Registers a new user in the database.
        Returns the ID of the registered user, or None if the username/nickname/email is already taken.
        """
        session = self.get_session()
        try:
            # Check for existing username, nickname, or email
            if session.query(User).filter(User.username == username).first():
                logger.warning(f"Error: Username '{username}' already exists.")
                return None
            if session.query(User).filter(User.nickname == nickname).first():
                logger.warning(f"Error: Nickname '{nickname}' already exists.")
                return None
            if email and session.query(User).filter(User.email == email).first():
                logger.warning(f"Error: Email '{email}' already exists.")
                return None

            new_user = User(
                first_name=first_name,
                last_name=last_name,
                username=username, # ✅ Added username
                nickname=nickname, # ✅ Added nickname
                email=email,
                balance=initial_balance, 
                birthdate=birthdate 
            )
            new_user.set_password(password) 
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user) 
            logger.info(f"User '{username}' (Nickname: '{nickname}', ID: {new_user.id}) registered successfully.") # ✅ Updated log
            return new_user.id
        except IntegrityError:
            session.rollback() 
            logger.warning(f"Error: Integrity error during registration for username '{username}', nickname '{nickname}'. This might indicate a unique constraint violation not caught by explicit checks.") # ✅ Updated log
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error registering user '{username}' (Nickname: '{nickname}'): {e}", exc_info=True) # ✅ Updated log
            return None
        finally:
            session.close() 

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]: # ✅ Changed nickname to username
        """
        Authenticates a user and returns their basic data if authentication is successful.
        :return: A dictionary with user data (id, username, nickname, balance, is_admin) or None if authentication fails.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first() # ✅ Changed User.nickname to User.username

            if user:
                if user.check_password(password): 
                    logger.info(f"User '{username}' authenticated successfully.") # ✅ Updated log
                    return {
                        "id": user.id,
                        "username": user.username, # ✅ Added username
                        "nickname": user.nickname, # ✅ Added nickname
                        "balance": user.balance, 
                        "is_admin": user.is_admin, 
                        "first_name": user.first_name, 
                        "last_name": user.last_name,
                        "email": user.email
                    }
                else:
                    logger.warning(f"Error: Incorrect password for '{username}'.") # ✅ Updated log
                    return None
            else:
                logger.warning(f"Error: Username '{username}' not found.") # ✅ Updated log
                return None
        except Exception as e:
            logger.error(f"Error authenticating user '{username}': {e}", exc_info=True) # ✅ Updated log
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
            user = session.get(User, user_id) 
            if user:
                logger.debug(f"User {user_id} fetched successfully from DB: {user.username} (Nickname: {user.nickname}).") # ✅ Updated log
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
                    "username": user.username, # ✅ Added username
                    "nickname": user.nickname, # ✅ Added nickname
                    "balance": user.balance, 
                    "is_admin": user.is_admin, 
                    "birthdate": str(user.birthdate) if user.birthdate else None 
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
        Saves changes made to a User object (like balance updates).
        """
        session = self.get_session()
        try:
            session.add(user) 
            session.commit()
            logger.debug(f"User {user.id} changes saved to DB. New balance: {user.balance}.") 
        except Exception as e:
            session.rollback() 
            logger.error(f"Error saving user {user.id} changes to DB: {e}", exc_info=True)
        finally:
            session.close()

    def update_user_balance(self, user_id: int, new_balance_amount: float) -> bool: 
        """
        Updates the balance amount of a user in the database.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.balance = new_balance_amount 
                session.commit()
                logger.info(f"User {user_id} balance updated to: {new_balance_amount}.") 
                return True
            logger.warning(f"Warning: No user found with ID {user_id} to update balance.") 
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating balance for user {user_id}: {e}", exc_info=True) 
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
            table = session.query(PokerTable).get(table_id) 
            
            if not table:
                logger.warning(f"DBManager: Table {table_id} not found in SQL database.")
                return None
            
            return {
                'id': table.id, 
                'name': table.name,
                'max_players': table.max_players,
                'small_blind': table.small_blind,
                'big_blind': table.big_blind,
                'created_at': str(table.created_at) 
            }
        except Exception as e:
            session.rollback() 
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
            session.refresh(new_table) 
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
