from pydantic import BaseModel, Field, ConfigDict, EmailStr, validator


class User(BaseModel):
    id: int
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)

# Схема для запиту реєстрації
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# Схема для даних при логін
class UserLogin(BaseModel):
    email: str
    password: str

# Схема для токену
class Token(BaseModel):
    access_token: str
    token_type: str