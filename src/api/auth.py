from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Request, status)
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.schemas.users import RequestEmail, Token, User, UserCreate, UserLogin
from src.services.auth import create_access_token, get_email_from_token, Hash
from src.services.email import send_email
from src.services.users import UserService


router = APIRouter(prefix="/auth", tags=["auth"])


# # Реєстрація користувача з підтвердженням по пошті
@router.post("/register",
             response_model=User,
             status_code=status.HTTP_201_CREATED
             )
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new user with email confirmation.

    This endpoint creates a new user, hashes their password, and
    sends a confirmation email with a verification link.

    Args:
        user_data (UserCreate): User registration data.
        background_tasks (BackgroundTasks): Background task manager.
        request (Request): FastAPI request object.
        db (Session): Database session dependency.

    Returns:
        User: The created user object.
    """

    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists.",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


# Логін користувача
@router.post("/login", response_model=Token)
async def login_user(body: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.

    This endpoint verifies the user's email and password, and if
    valid, returns a JWT token.

    Args:
        body (UserLogin): User login credentials.
        db (Session): Database session dependency.

    Returns:
        Token: A JWT access token.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if not user or not Hash().verify_password(body.password,
                                              user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user's email using a token.

    This endpoint extracts the email from the verification token and
    updates the user's status to `is_verified = True`.

    Args:
        token (str): Email verification token.
        db (Session): Database session dependency.

    Returns:
        dict: A message indicating the verification status.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification error"
        )
    if user.is_verified:
        return {"message": "Your email is already verified."}
    await user_service.confirmed_email(email)
    return {"message": "Email successfully verified."}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Resend email verification link.

    This endpoint sends a new email verification link to the user.

    Args:
        body (RequestEmail): Request containing the user's email.
        background_tasks (BackgroundTasks): Background task manager.
        request (Request): FastAPI request object.
        db (Session): Database session dependency.

    Returns:
        dict: A message indicating that the verification email was sent.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.is_verified:
        return {"message": "Your email is already verified."}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for verification instructions."}
