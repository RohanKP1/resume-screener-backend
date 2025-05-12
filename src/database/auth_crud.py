from sqlalchemy.orm import Session
from src.models.auth_model import User, UserType
from src.utils.jwt_manager import JWTManager
from src.core.custom_logger import CustomLogger

logger = CustomLogger("AuthCRUD")
jwt_manager = JWTManager()

def get_user_by_username(db: Session, username: str):
    logger.debug(f"Fetching user by username: {username}")
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    logger.debug(f"Fetching user by email: {email}")
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, username: str, email: str, password: str, user_type: UserType):
    logger.info(f"Creating new {user_type.value} user: {username}")
    hashed_password = jwt_manager.hash_password(password)
    db_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        user_type=user_type
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Successfully created user: {username}")
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise

def update_user(db: Session, user_id: int, **kwargs):
    logger.info(f"Updating user {user_id}")
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        for key, value in kwargs.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Successfully updated user {user_id}")
        return db_user
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.rollback()
        raise