from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.services.postgres_handler import get_db
import src.database.auth_crud as crud
from src.utils.jwt_manager import JWTManager
from src.schemas.auth_schema import UserCreate, UserUpdate, UserResponse, Token, UserType
from src.core.custom_logger import CustomLogger
from functools import wraps

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
jwt_manager = JWTManager()
logger = CustomLogger("AuthEndpoints")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = jwt_manager.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_user_type(allowed_types: list[UserType]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: UserResponse = Depends(get_current_user), **kwargs):
            if current_user.user_type not in allowed_types:
                logger.warning(f"Unauthorized access attempt by {current_user.username}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to perform this action"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for {user.email}")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning(f"Registration failed: Email {user.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = crud.create_user(
        db=db,
        username=user.username,
        email=user.email,
        password=user.password,
        user_type=user.user_type
    )
    logger.info(f"Successfully registered new {user.user_type} user: {user.username}")
    return new_user

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login attempt for user: {form_data.username}")
    db_user = crud.get_user_by_username(db, username=form_data.username)
    
    if not db_user or not jwt_manager.verify_password(form_data.password, db_user.password_hash):
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = jwt_manager.create_access_token(
        data={
            "sub": db_user.username,
            "user_type": db_user.user_type.value
        }
    )
    
    # Return token with additional user information
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_type": db_user.user_type,
        "username": db_user.username,
        "email": db_user.email,
        "user_id": db_user.id
    }

@router.put("/users/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile information.
    Only allows updating username and email.
    """
    logger.info(f"Update request for user: {current_user.username}")
    
    # Check if email is being updated and is already taken
    if user_update.email and user_update.email != current_user.email:
        if crud.get_user_by_email(db, email=user_update.email):
            logger.warning(f"Update failed: Email {user_update.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Check if username is being updated and is already taken
    if user_update.username and user_update.username != current_user.username:
        if crud.get_user_by_username(db, username=user_update.username):
            logger.warning(f"Update failed: Username {user_update.username} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    try:
        # Update user
        updated_user = crud.update_user(
            db=db,
            user_id=current_user.id,
            **user_update.model_dump(exclude_unset=True)
        )
        logger.info(f"Successfully updated user: {updated_user.username}")
        return updated_user
    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

