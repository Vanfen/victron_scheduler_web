
import base64
import json
from fastapi import Depends
from auth.service import get_user_by_username
from database.session import get_db
from victron.models import VictronEnergy, VictronScheduleHistory
from victron.schemas import NordPoolDataCreate
from sqlalchemy.orm import Session
from victron.service import set_nordpool_data, set_nordpool_prices


def get_profile_data(username: str, db=Depends(get_db)):
    user = get_user_by_username(username=username, db=db)
    data = db.query(VictronEnergy).filter(VictronEnergy.user_id == user.id).first()
    username = data.username
    password = base64.b64decode(data.password.decode("utf-8"))
    portal_id = data.portal_id
    return username, password, portal_id

from .fill_schedules import fill_schedules
from .np_data_fetch import parse_nord_pool_data
# from .remove_used_schedules import refresh_schedules
from .search_for_available_schedules import search_for_available_schedules
from .send_notification import send_schedule_update_notification_via_email


# def run_cleaning_of_schedules():
    # refresh_schedules()

def fill_leftovers():
    # run_cleaning_of_schedules()
    with open("./new_schedules.txt", "r") as file:
        schedules = file.readlines()
    if len(schedules) != 0:
        fill_schedules()
    else:
        print("There are no leftovers.")

def run_victron(country_code: str = "LV"):
    db = next(get_db())
    parsed_data = parse_nord_pool_data(country_code=country_code)
    # string_data = ""
    # with open("./data/parsed_data.txt", "r") as file:
    #     string_data = file.readline()
    # parsed_data = json.loads(string_data)
    data = NordPoolDataCreate(
        last_update_time=parsed_data[country_code]["NordPool_Update_Time"],
        max_price=parsed_data[country_code]["Max"],
        min_price=parsed_data[country_code]["Min"],
        avg_price=parsed_data[country_code]["Average"],
    )
    set_nordpool_data(data=data,db=db)
    set_nordpool_prices(np_data=parsed_data, country_code=country_code, db=db)
    # if parsed_data is not None:
    #     run_cleaning_of_schedules()
    #     search_for_available_schedules()
    #     fill_schedules()
    #     send_schedule_update_notification_via_email(parsed_data=parsed_data, country=list(parsed_data.keys())[0])
    #     log_victron_schedule_update(parsed_data=parsed_data)
    # else:
    #     print("Nothing to update.")

def get_victron_activity_log(db: Session, latest: bool = True):
    filters = []
    last_date = db.query(VictronScheduleHistory).order_by(VictronScheduleHistory.id.desc()).first()
    if latest:
        filters.append(VictronScheduleHistory.update_time == last_date.update_time)
    log = db.query(VictronScheduleHistory).filter(*filters).all()
    return log