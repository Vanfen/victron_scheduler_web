from time import sleep
from typing import List
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from victron.data.fill_schedules import fill_schedules
from victron.data.fill_schedules import generate_schedules
from victron.data.np_data_fetch import parse_nord_pool_data
# from data.utils import run_victron

from database.session import get_db
from victron.data.search_for_available_schedules import search_for_available_schedules
from victron.data.refresh_outdated_schedules import refresh_outdated_schedules
from victron.schemas import NordPoolDataCreate, NordPoolDataFilter, NordPoolDataPeriod, NordPoolDataShow, NordPoolPricesCreate, NordPoolPricesShow, UserEmail, VictronDataCreate, VictronDataShow
from victron.service import get_nordpool_data, get_nordpool_prices, get_victron_data, set_nordpool_data, set_nordpool_prices, set_victron_data


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

ve_router = APIRouter(
    prefix="/victron",
    tags=["Victron"],
)

@ve_router.get("/run_victorn")
def run():
    parse_nord_pool_data("LV")
    refresh_outdated_schedules()
    search_for_available_schedules()
    generate_schedules()
    fill_schedules()
    return "Done"

@ve_router.post("/set_victron_data", response_model=VictronDataShow)
def set_victron_data_route(ve_data: VictronDataCreate, db: Session = Depends(get_db)):
    data = set_victron_data(data=ve_data, user_email=ve_data.user_email, db=db)
    return data

@ve_router.post("/get_victron_data", response_model=VictronDataShow)
def get_victron_data_route(user_email: UserEmail, db: Session = Depends(get_db)):
    return get_victron_data(user_email=user_email, db=db)

@ve_router.post("/get_nordpool_data", response_model=List[NordPoolDataShow])
def get_nordpool_data_route(param: NordPoolDataPeriod, db: Session = Depends(get_db)):
    return get_nordpool_data(db=db, range=param.range)

@ve_router.post("/get_nordpool_prices", response_model=List[NordPoolPricesShow])
def get_nordpool_prices_route(filter: NordPoolDataFilter, db: Session = Depends(get_db)):
    return get_nordpool_prices(compare_to=filter.compare_to, period=filter.period, db=db)
