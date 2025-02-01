from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    """
    Schema representing a user model with basic details.
    """

    id: int
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    Schema for user registration request.
    """

    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    """
    Schema for user login request.
    """

    email: str
    password: str


class Token(BaseModel):
    """
    Schema for authentication token response.
    """

    access_token: str
    token_type: str


class RequestEmail(BaseModel):
    """
    Schema for requesting email verification.
    """

    email: EmailStr
