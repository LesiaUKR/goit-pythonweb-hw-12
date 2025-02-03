from unittest.mock import Mock
from fastapi import status
import pytest
from sqlalchemy import select

from src.database.models import User
from tests.conftest import TestingSessionLocal
from src.services.auth import create_access_token

user_data = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678"
}

def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data

@pytest.mark.asyncio
async def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_409_CONFLICT, response.text
    data = response.json()
    assert data["detail"] == "A user with this email already exists."


def test_not_confirmed_login(client):
    response = client.post("api/auth/login",
                           json={"email": user_data.get("email"),
                                 "password": user_data.get("password")})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    data = response.json()
    assert data["detail"] == "Email is not verified."

@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.is_verified = True
            await session.commit()

    response = client.post("api/auth/login",
                           json={"email": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer", f'Token type should be {data["token_type"]}'

def test_wrong_password_login(client):
    response = client.post("api/auth/login",
                           json={"email": user_data.get("email"), "password": "password"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    data = response.json()
    assert data["detail"] == "Invalid email or password."

def test_wrong_username_login(client):
    response = client.post("api/auth/login",
                           json={"email": "wrong@email", "password": user_data.get("password")})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    data = response.json()
    assert data["detail"] == "Invalid email or password."

def test_validation_error_login(client):
    response = client.post("api/auth/login",
                           json={"password": user_data.get("password")})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_forgot_password_request(client, monkeypatch):
    """
    Тестує відправку запиту на скидання пароля
    """

    # Переконуємось, що користувач існує і має підтверджену email-адресу
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data["email"]))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.is_verified = True
            await session.commit()

    # Мокуємо функцію відправки email
    mock_send_reset_email = Mock()
    monkeypatch.setattr("src.api.auth.send_reset_password_email", mock_send_reset_email)

    response = client.post("/api/auth/forgot-password", json={"email": user_data["email"]})

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["message"] == "Перевірте свою електронну пошту для скидання пароля"

    # Перевіряємо, чи викликалася функція відправки email
    mock_send_reset_email.assert_called_once()

@pytest.mark.asyncio
async def test_confirm_reset_password(client):
    """
    Тестує зміну пароля за допомогою токена скидання
    """

    # Генеруємо токен для існуючого користувача
    async with TestingSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == user_data["email"]))
        current_user = result.scalar_one_or_none()
        assert current_user is not None, "Користувач повинен існувати"

    # Додаємо логування перед створенням токена
    new_password = "newSecurePass123"
    print(f"Generating reset token for: {user_data['email']}")

    # Оновлення токена з додаванням пароля
    reset_token = await create_access_token(
        data={"sub": user_data["email"], "password": new_password}
    )

    # Надсилаємо запит на оновлення пароля
    response = client.post(
        f"/api/auth/confirm_reset_password/{reset_token}",
        json={"password": new_password},
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["detail"] == "Password has been reset successfully"

def test_forgot_password_nonexistent_user(client):
    """
    Тестуємо ситуацію, коли користувач не знайдений
    """
    response = client.post("/api/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    data = response.json()
    assert data["detail"] == "User not found"


def test_confirm_reset_password_invalid_token(client):
    """
    Тестуємо ситуацію, коли токен недійсний або прострочений
    """
    response = client.post("/api/auth/confirm_reset_password/invalid_token",
                           json={"password": "newSecurePass123"})

    # Додаємо логування
    print(
        f"Response from invalid token reset: {response.status_code} - {response.text}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
    data = response.json()
    assert data["detail"] == "Invalid email verification token"

