# Fetch data from NordPool

from __future__ import unicode_literals
import datetime
import json
import requests
import pytz
from datetime import date, timedelta
from dateutil.parser import parse as parse_dt
from pytz import timezone
    
from database.session import get_db
from victron.schemas import NordPoolDataCreate

from victron.service import get_nordpool_data, set_nordpool_data, set_nordpool_prices


#Converting time from CET to RIX
def convert_time(time):
    new_time = parse_dt(time)
    local_tz = pytz.timezone('Europe/Riga')
    if new_time.tzinfo is None:
        new_time = timezone('Europe/Amsterdam').localize(new_time).astimezone(local_tz)
    new_time = new_time.strftime("%d-%b-%Y %H:%M") #%d-%b-%Y (%H:%M)
    return new_time

#Changing comma to dot (float values)
def convert_to_float(value):
    try:
        return float(value.replace(',', '.').replace(" ", ""))
    except ValueError:
        return float('inf')

def parse_nord_pool_data(country_code: str):
    db = next(get_db())
    print("Parse Nord-Pool data")

    API_URL = 'http://www.nordpoolspot.com/api/marketdata/page/10' #Hourly

    end_date = date.today() + timedelta(days=1)
    parameters = {"currency": "EUR", "endDate": end_date}
    additional_data = {"Max", "Min", "Average",}

    data = requests.get(API_URL, params=parameters).json()
    if not data:
        return "Data not fetched"
    data = data['data']

    parsed_data = {}
    nordpool_data = get_nordpool_data(db=db)[0]
    if nordpool_data:
        last_update_time_np = nordpool_data.last_update_time
    else:
        last_update_time_np = datetime.datetime.today() - timedelta(days=1)
    
    if last_update_time_np >= datetime.datetime.strptime(convert_time(data['DateUpdated']), "%d-%b-%Y %H:%M"):
        print("Victron schedules are up to date")
        return None
    last_update_time_np = convert_time(data['DateUpdated'])

    for row in data['Rows']:
        for column in row['Columns']:

            name = column['Name']
            #Skip values not for CountyCode
            if name != country_code:
                continue

            if name not in parsed_data:
                parsed_data[name] = { 'Values': []}
            
            if row['IsExtraRow']:
                if row['Name'] in additional_data:
                    parsed_data[name][row['Name']] = convert_to_float(column['Value'])
            else:
                #if (convert_to_float(column['Value']) <= compare_to):
                    parsed_data[name]['Values'].append({
                        'Start_Datetime': convert_time(row['StartTime']),
                        'End_Datetime': convert_time(row['EndTime']),
                        'Price': convert_to_float(column['Value']),
                    })
                    
                    
    if len(parsed_data[country_code]['Values']) != 0:
        parsed_data[country_code]['NordPool_Update_Time'] = last_update_time_np

        set_nordpool_prices(np_data=parsed_data, country_code=country_code, db=db)
        np_data = NordPoolDataCreate(
            last_update_time=str(last_update_time_np),
            min_price=parsed_data[country_code]["Min"],
            max_price=parsed_data[country_code]["Max"],
            avg_price=parsed_data[country_code]["Average"],
        )
        set_nordpool_data(data=np_data, db=db)
        return parsed_data

    return None