import base64
import datetime
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from auth.service import get_user_by_email
from victron.models import NordPoolData, NordPoolPrices, VictronEnergy

from victron.schemas import NordPoolDataCreate, NordPoolPricesCreate, UserEmail, VictronDataCreate


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def set_nordpool_data(data: NordPoolDataCreate, db: Session):
    last_update_time = datetime.datetime.strptime(data.last_update_time, "%d-%b-%Y %H:%M")
    nordpool_data = NordPoolData(
        last_update_time = last_update_time,
        min_price = data.min_price,
        max_price = data.max_price,
        avg_price = data.avg_price
    )
    db.add(nordpool_data)
    db.commit()
    return nordpool_data

def get_nordpool_data(db: Session, range: bool = False):
    if range:
        period = datetime.datetime.now() - datetime.timedelta(days=30)
        nordpool_data = db.query(NordPoolData)\
                          .filter(NordPoolData.last_update_time >= period)\
                          .all()
    else:
        nordpool_data = [db.query(NordPoolData).order_by(NordPoolData.id.desc()).first()]
    return nordpool_data

def set_nordpool_prices(np_data: NordPoolPricesCreate, country_code: str, db: Session):
    for value in np_data[country_code]["Values"]:
        start_time = datetime.datetime.strptime(value["Start_Datetime"], "%d-%b-%Y %H:%M")
        end_time = datetime.datetime.strptime(value["End_Datetime"], "%d-%b-%Y %H:%M")
        price = value["Price"]
        new_data = NordPoolPrices(
            start_time = start_time,
            end_time = end_time,
            price = price
        )
        db.add(new_data)
    db.commit()
    return np_data

def get_nordpool_prices(compare_to: float, period: int, db: Session):
    latest_data = get_nordpool_data(db=db, range=False)
    filters = []
    if period:
        period_date = datetime.datetime.now() - datetime.timedelta(days=period)
        filters.append(func.date(NordPoolPrices.start_time) > period_date)
    else:
        filters.append(func.date(NordPoolPrices.start_time) > latest_data.last_update_time.date())
    if compare_to:
        filters.append(NordPoolPrices.price <= compare_to)
    data = db.query(NordPoolPrices).filter(*filters).all()
    return data

def set_victron_data(data: VictronDataCreate, user_email: str, db: Session):
    user = get_user_by_email(email=user_email, db=db)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not user:
        raise credentials_exception
    
    db_data = db.query(VictronEnergy).filter(VictronEnergy.user_id == user.id).first()
    print(data.password)
    password = base64.b64encode(data.password.encode("utf-8"))
    print(password)
    if db_data:
        db_data.email = data.email
        db_data.password= password
        db_data.portal_id = data.portal_id
        db_data.price_to_compare = data.price_to_compare
        db.commit()
        return db_data
    else:
        # Add new victron energy data to db
        ve_data = VictronEnergy(
            email = data.email,
            password = password,
            portal_id = data.portal_id,
            price_to_compare = data.price_to_compare,
            user_id = user.id,
        )
        db.add(ve_data)
        db.commit()
        return ve_data

def get_victron_data(user_email: UserEmail, db: Session):
    user = get_user_by_email(email=user_email.user_email, db=db)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    data_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Please fill the victron data",
    )
    if not user:
        raise credentials_exception
    db_data = db.query(VictronEnergy).filter(VictronEnergy.user_id == user.id).first()
    if not db_data:
        raise data_exception
    print(db_data.password)

    print(type(db_data.password))
    print(len(db_data.password))
    db_data.password = base64.b64decode(db_data.password.decode("utf-8"))
    return db_data