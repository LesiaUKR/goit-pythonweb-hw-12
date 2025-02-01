import logging

from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from src.conf.config import settings
from src.database.database import get_db
from src.services.users import UserService


class Hash:
    """
    Utility class for password hashing and verification using bcrypt.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
        Verify if a given plain password matches the hashed password.

        :param plain_password: User's raw password.
        :param hashed_password: Stored hashed password.
        :return: Boolean indicating whether passwords match.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Generate a hashed password.

        :param password: User's raw password.
        :return: Hashed password.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = HTTPBearer()


async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """
    Generate a new JWT access token.

    :param data: Dictionary containing payload data.
    :param expires_delta: Expiration time in seconds.
    :return: Encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(
            seconds=settings.JWT_EXPIRATION_SECONDS
        )
    to_encode.update({"exp": expire})
    print("to_encode", to_encode)
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Retrieve the current authenticated user from the JWT token.

    :param token: JWT token containing user credentials.
    :param db: Database session.
    :return: Authenticated user object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        print("payload", payload)
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError as e:
        logging.error(f"JWT Error: {e}")
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


def create_email_token(data: dict):
    """
    Generate a JWT token for email verification.

    :param data: Dictionary containing payload data.
    :return: Encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return token


async def get_email_from_token(token: str):
    """
    Decode an email verification token and retrieve the email.

    :param token: Encoded JWT token.
    :return: Decoded email from the token.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        logging.error(f"JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email verification token",
        )
