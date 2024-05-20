from dotenv import load_dotenv
from pathlib import Path
import json

from fastapi import APIRouter

from victron.data.utils import get_victron_activity_log
from victron.schemas import VictronScheduleShow

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

data_router = APIRouter(
    prefix="/data",
    tags=["Data"],
)

@data_router.get("/day_ahead_prices")
def root():
    #parse_nord_pool_data("LV")
    content = ""
    with open("data/parsed_data.txt", "r") as file:
        content = file.readline()
        print(content)
    return json.loads(str(content))

@data_router.get("/price_to_compare")
def get_price_to_compare():
    with open("data/price_to_compare.txt") as file:
        return {"Price": file.readline()}
    
@data_router.post("/victron_log", response_model=[VictronScheduleShow])
def get_victron_log(latest: bool = True):
    return get_victron_activity_log(latest=latest)