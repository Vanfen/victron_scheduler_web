from dotenv import load_dotenv
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .service import create_new_user, delete_user, generate_reset_token, get_all_users, authenticate_user, get_current_active_user, logout_user, modify_user_state, refresh_auth_token, reset_password_db, update_email, update_username
from .schemas import AccessToken, ResetPassword, ResetTokenCreate, TokenTuple, UserChangeEmail, UserChangeUsername, UserCreate, UserRemove, UserShow, UserState
from database.session import get_db
from .models import UserAuth
# from .utils import send_reset_token_email


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

@auth_router.post("/register", response_model=UserShow)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Creates new user.
    """
    user =  create_new_user(user=user, db=db)
    return user

@auth_router.post("/token", response_model=TokenTuple)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticates user by username and password.
    Returns the authentication and refresh tokens tuple.
    """
    access_token, refresh_token = authenticate_user(form_data.username, form_data.password, db)
    response.set_cookie(
        key="access_token", value=access_token, httponly=True,
    )
    return {"access_token": {"access_token": access_token, "token_type": "bearer"}, "refresh_token": {"refresh_token": refresh_token, "token_type": "bearer"}}

@auth_router.post("/token_refresh", response_model=AccessToken)
def refresh_login_token(
    response: Response,
    refresh_token: str,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Refreshes the session token.
    Returns new session token.
    """
    new_access_token = refresh_auth_token(username=username, refresh_token=refresh_token, db=db)
    response.set_cookie(
        key="access_token", value=new_access_token, httponly=True,
    )
    return {"access_token": new_access_token, "token_type": "bearer"}

@auth_router.get("/get_current_user", response_model=UserShow)
def get_current_user_from_token(current_user: UserAuth = Depends(get_current_active_user)):
    """
    Returns active user.
    """
    return current_user

@auth_router.get("/get_all_users", response_model=List[UserShow])
def query_all_users(db: Session = Depends(get_db)):
    """
    Returns the list of all users.
    """
    user = get_all_users(db=db)
    return user

@auth_router.post("/forgot_password")
async def forgot_password(request: ResetTokenCreate, db: Session = Depends(get_db)):
    """
    Generates the Reset Password Token and sends it to the provided email.
    """
    reset_token, username, email = generate_reset_token(request, db)
    reset_password_url = "http://127.0.0.1:8000/docs#/default/reset_password_auth_reset_password_patch?token="+reset_token
    # await send_reset_token_email('TickIt Reset Password', email, {'title': 'TickIt Reset Password', 'name': username, 'reset_password_url': reset_password_url})
    return reset_token

@auth_router.post("/reset_password")
def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    """
    Resets the user password.
    """
    # Reset password
    reset_password_db(request, db)
    return {"Password reset": "Success"}

@auth_router.post("/remove_user")
def remove_user(request: UserRemove, db: Session = Depends(get_db), user: UserAuth = Depends(get_current_active_user)):
    """
    Deletes user.
    """
    delete_user(request.password, request.confirm_password, user, db)
    return {"Status": "User successfully removed."}

@auth_router.post("/change_user_state", response_model=UserShow)
def change_user_state(request: UserState, user: UserAuth = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Changes the state of the user - Active/Not Active
    """
    result = modify_user_state(request.username, request.is_active, user, db)
    return result

@auth_router.post("/change_username", response_model=UserShow)
def change_username(requset: UserChangeUsername, user: UserAuth = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Changes the username of active user.
    """
    result = update_username(requset.username, user, db)
    return result

@auth_router.post("/change_email", response_model=UserShow)
def change_email(requset: UserChangeEmail, user: UserAuth = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Changes the email of active user.
    """
    result = update_email(requset.email, user, db)
    return result

@auth_router.post("/logout")
def logout_from_session(response: Response, logout: bool = Depends(logout_user)):
    """
    Removes active session token and refresh token.
    """
    response.delete_cookie(
        key="access_token",
    )
    return {"Logout": "Successful"}
