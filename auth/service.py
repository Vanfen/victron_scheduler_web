import os
import uuid
from pathlib import Path
import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt
from jwt import ExpiredSignatureError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.schemas import ResetPassword, UserCreate, ResetTokenCreate
from auth.models import ResetToken, UserAuth
from database.session import get_db
from auth.utils import OAuth2PasswordBearerWithCookie


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


# Hashing password with bcrypt
def get_password_hash(plain_password: str):
    """
    Generating a hashed password with bcrypt alghoritm.
    """
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

def create_new_user(user: UserCreate, db: Session):
    """
    Creating new user in the database.
    """
    user = UserAuth(
        username = user.username,
        email = user.email,
        hashed_password = get_password_hash(user.password),
        is_active = True,
        date_active = datetime.now(),
        date_created = datetime.now(),
        is_superuser = False,
    )
    # Check if user with passed email already exists
    email_exist = get_user_by_email(user.email, db)
    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with email {0} already existst".format(user.email)
        )
    # Check if user with passed username already exists
    username_exist = get_user_by_username(user.username, db)
    if username_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with username {0} already existst".format(user.username)
        )
    # Add new user to db
    db.add(user)
    db.commit()
    return user

def modify_user_state(username: str, state: bool, user: UserAuth, db: Session):
    """
    Changing the user state - Active/NotActive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not able to perform this action. Not enough permissions.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_username(username, db)
    if user is None:
        raise credentials_exception
    user.is_active = state
    db.commit()
    return user

def delete_user(password: str, confirm_password: str, user: UserAuth, db: Session):
    """
    Removes the user from the database.
    """
    # Check if password and confirm_password are valid
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Password and confirm password don't match."
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Provided password is not valid."
        )
    db.delete(user)
    db.commit()

def get_user_by_username(username: str, db: Session):
    """
    Returns the user if found the match by the username.
    """
    user = db.query(UserAuth).filter(UserAuth.username == username).first()
    return user

def get_user_by_email(email: str, db: Session):
    """
    Returns the user if found the match by the email.
    """
    
    user = db.query(UserAuth).filter(UserAuth.email == email).first()
    return user

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/auth/token")

def decode_token(token: str, is_refresh: bool | None = False):
    """
    Decoding of JWT tokens.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    outdated_token_exception = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Token has been expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username: str = None
    # Get username from token
    try:
        secret_key = os.getenv("SECRET_KEY_REFRESH") if is_refresh else os.getenv("SECRET_KEY")
        # jwt decode automatically throws the error of expired token
        # no need to handle it separately
        payload = jwt.decode(token, secret_key, algorithms=[os.getenv("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise outdated_token_exception
    except JWTError:
        raise credentials_exception     
    return username

# Get active user by auth token
def get_current_active_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Returns the authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = decode_token(token)
    # Get user by username
    user = get_user_by_username(username, db)
    if not user:
        raise credentials_exception
    return user

def get_all_users(db: Session):
    """
    Returns all users list.
    """
    users = db.query(UserAuth).all()
    return users

def verify_password(plain_password: str, hashed_password: str):
    """
    Checks if the passed password is equal to the stored one.
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates the session token for authenticated user.
    """
    to_encode = data.copy()
    # Set token expiry time
    expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return encode_jwt

def create_refresh_token(data: dict):
    """
    Creates the refresh token for authenticated user.
    """
    to_encode = data.copy()
    # Set refresh token expiry time
    expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY_REFRESH"), algorithm=os.getenv("ALGORITHM"))
    return encode_jwt

def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    """
    Authenticates the user if username and password are correct.
    """
    user = get_user_by_username(username=username, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong credentials.")
    update_date_active(username, db)
    access_token = create_access_token(
        data={"sub": user.username},
    )
    user.session_token = access_token
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )
    user.refresh_token = refresh_token
    db.commit()
    db.flush()
    return access_token, refresh_token

def refresh_auth_token(username: str, refresh_token: str, db: Session = Depends(get_db)):
    """
    Refreshes the old session token.
    """
    user = get_user_by_username(username=username, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.refresh_token != refresh_token:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Refresh token is not valid.")
    # Check validity of refresh token
    token = decode_token(refresh_token, is_refresh=True)
    access_token = create_access_token(
        data={"sub": user.username},
    )
    user.session_token = access_token
    db.commit()
    db.flush()
    return access_token

def logout_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Removes session and refresh tokens.
    """
    username = decode_token(token=token)
    user = get_user_by_username(username=username, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.session_token = None
    user.refresh_token = None
    db.commit()
    db.flush()
    return True

def update_date_active(username: str, db: Session):
    """
    Updates the latest login time of the user.
    """
    user = db.query(UserAuth).filter(UserAuth.username == username).first()
    user.date_active = datetime.now()
    db.commit()
    return user

def generate_reset_token(request: ResetTokenCreate, db: Session):
    """
    Generates a reset token for a password change.
    """
    try:
        user = get_user_by_email(request.email, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    # Generate reset token
    reset_token = str(uuid.uuid1())
    new_token = ResetToken(
        user_id=user.id,
        expiry_time=datetime.now()+timedelta(minutes=15),
        token=reset_token,
    )
    # Add token to db
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token.token, user.username, user.email

def check_reset_password_token(request: ResetPassword, db: Session):
    """
    Verifies the validity of the reset token.
    """
    token_data = db.query(ResetToken).filter(ResetToken.token == request.reset_password_token, ResetToken.expiry_time >= datetime.now(), ResetToken.used == False).first()
    if not token_data:
        raise HTTPException(
            status_code=404,
            detail="Reset password token has expired, please request a new one."
        )
    return token_data

def reset_password_db(request: ResetPassword, db: Session):
    """
    Resets the password in the database.
    """
    # Check both new and confirm passwords match
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="New password and confirm password don't match."
        )
    token_data = check_reset_password_token(request, db)
    user_id = token_data.user_id
    new_password = request.new_password
    token = request.reset_password_token
    user = db.query(UserAuth).filter(UserAuth.id == user_id).one()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    update_token = db.query(ResetToken).filter(ResetToken.token == token).one()
    update_token.used = True
    db.commit()

def update_username(username: str, user: UserAuth, db: Session):
    """
    Sets new username.
    """
    if username != "":
        user.username = username
        print("NOT EMPTY")
        print(username)
    db.commit()
    return user

def update_email(email: str, user: UserAuth, db: Session):
    """
    Sets new email.
    """
    if email != "":
        user.email = email
    db.commit()
    return user