from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from src.core.config import Config
from fastapi import HTTPException, status
from src.core.custom_logger import CustomLogger

# Security utilities for password hashing and JWT token generation

class JWTManager:
    def __init__(self):
        self.logger = CustomLogger("JWTManager")
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        self.logger.debug("Hashing password.")
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        self.logger.debug("Verifying password.")
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        self.logger.debug("Creating access token.")
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
        self.logger.info("Access token created successfully.")
        return encoded_jwt

    def decode_access_token(self, token: str) -> dict:
        self.logger.debug("Decoding access token.")
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            self.logger.info("Access token decoded successfully.")
            return payload
        except JWTError as e:
            self.logger.error(f"JWT decode error: {e}")
            raise credentials_exception