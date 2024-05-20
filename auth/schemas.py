from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserShow(BaseModel):
    id: int
    username: str
    email: EmailStr
    date_created: datetime
    date_active: datetime
    is_active: bool

    # to convert the non dict User obj to JSON
    class Config:
        from_attributes = True

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class RefreshToken(BaseModel):
    refresh_token: str
    token_type: str

class TokenTuple(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken

class ResetTokenCreate(BaseModel):
    email: str

class ResetPassword(BaseModel):
    reset_password_token: str
    new_password: str
    confirm_password: str

class UserChangeUsername(BaseModel):
    username: str

class UserChangeEmail(BaseModel):
    email: EmailStr

class UserState(BaseModel):
    username: str
    is_active: bool

class UserRemove(BaseModel):
    password: str
    confirm_password: str
