import base64
import datetime
import json
import ssl
from time import sleep
from typing import List
import paho.mqtt.client as mqtt
from sqlalchemy import func

from database.session import get_db
from victron.models import NordPoolData, NordPoolPrices, VictronAvailableSchedules, VictronEnergy, VictronScheduleHistory, VictronSchedulesToFill
from victron.service import get_nordpool_data
from .victron_schedules import Schedule


flag_connected = 0
schedules = []

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client: mqtt.Client, userdata, flags, rc):
    global flag_connected
    print("Connected with result code "+str(rc))
    flag_connected = 1
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    val = json.loads(msg.payload)
    print(msg.topic+" -> "+str(val))

def on_disconnect(client: mqtt.Client, userdata, rc):
    global flag_connected
    print("Disconnected with code " + str(rc))
    client.loop_stop()
    flag_connected = 0

def log_victron_schedule_update(update_time, schedule_time, duration, schedule_id, user_id):
    db = next(get_db())
    history_record = VictronScheduleHistory(
        update_time = update_time,
        schedule_time = f"{schedule_time}:00)",
        duration = duration,
        schedule_id = schedule_id,
        user_id = user_id,
    )
    db.add(history_record)
    db.commit()

def fill_schedules():
    global flag_connected
    
    print("Fill schedules")
    
    db = next(get_db())
    victron_data: List[VictronEnergy] = db.query(VictronEnergy).all()
    for item in victron_data:
        username = item.email
        password = base64.b64decode(item.password.decode("utf-8"))
        portal_id = item.portal_id
        user_id = item.user_id
        
        schedules_query = db.query(VictronSchedulesToFill).filter(VictronSchedulesToFill.user_id == user_id)
        schedules_db = schedules_query.order_by(VictronSchedulesToFill.id.desc()).first()
        
        if not schedules_db:
            print("No new schedules found.")
            return None
        
        new_schedules = schedules_db.to_fill.replace("'", '"')
        
        available_schedules_db: VictronAvailableSchedules = db.query(VictronAvailableSchedules).filter(VictronAvailableSchedules.user_id == user_id).first()
        available_schedules = []
        
        if available_schedules_db:
            if available_schedules_db.first:
                available_schedules.append("0")
            if available_schedules_db.second:
                available_schedules.append("1")
            if available_schedules_db.third:
                available_schedules.append("2")
            if available_schedules_db.fourth:
                available_schedules.append("3")
            if available_schedules_db.fifth:
                available_schedules.append("4")
        else:
            available_schedules = ["0", "1", "2", "3", "4"]

        client = mqtt.Client("FillSchedules")
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
        client.username_pw_set(username=username, password=password)
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        client.connect("mqtt87.victronenergy.com", port=8883)

        client.loop_start()
        
        # Send ping to wake up Remote Console
        client.publish("R/%s/system/0/Serial" % portal_id)
        while 1:
            if flag_connected == 0:
                schedules = json.loads(new_schedules)["Schedules"]
                print(schedules)
                leftover = schedules[:]
                for schedule in schedules:
                    try:
                        schedule_to_set = available_schedules.pop(0)
                    except IndexError:
                        break
                    if int(schedule["EndWeekday"]) - int(schedule["StartWeekday"]) == 0:
                        duration = int(schedule["EndTime"]) - int(schedule["StartTime"])
                    else:
                        duration = 24 * 3600 - int(schedule["StartTime"]) + int(schedule["EndTime"])
                    day_published = client.publish("W/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%s/Day" % (portal_id, schedule_to_set), json.dumps({"value": schedule["StartWeekday"]}))
                    day_published.wait_for_publish()
                    print("Day published = " + str(day_published.is_published()))
                    duration_published = client.publish("W/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%s/Duration" % (portal_id, schedule_to_set), json.dumps({"value": duration}))
                    duration_published.wait_for_publish()
                    print("Duration published = " + str(duration_published.is_published()))
                    start_published = client.publish("W/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%s/Start" % (portal_id, schedule_to_set), json.dumps({"value": schedule["StartTime"]}))
                    start_published.wait_for_publish()
                    print("Start published = " + str(start_published.is_published()))
                    leftover.pop(0)
                    log_victron_schedule_update(update_time=datetime.datetime.now(), schedule_time=int(schedule["StartTime"])/3600, duration=duration, schedule_id=schedule_to_set, user_id=user_id)

                if len(leftover) > 0:
                    schedules_to_save = {"Schedules" : []}
                    for schedule in leftover:
                        schedules_to_save["Schedules"].append(schedule)
                    schedules_db.to_fill = str(schedules_to_save)
                    db.commit()
                else:
                    schedules_query.delete()
                    db.commit()
                
                sleep(1)
                client.disconnect()
                sleep(1)
                if not client.is_connected():
                    print("Client successfully disconnected")
                break
            else:
                print("Waiting for the connection to be established...")
                sleep(1)

def generate_schedules():
    
    db = next(get_db())
    
    nordpool_data: NordPoolData = get_nordpool_data(db=db)[0]
    if not nordpool_data:
        print("No schedules found")
        return "No schedules found"
    last_update_datetime = nordpool_data.last_update_time
    last_update_date = last_update_datetime.date()
    prices: List[NordPoolPrices] = db.query(NordPoolPrices).filter(func.date(NordPoolPrices.start_time) > last_update_date).all()

    victron_data: List[VictronEnergy] = db.query(VictronEnergy).all()
    for item in victron_data:
        username = item.email
        password = base64.b64decode(item.password.decode("utf-8"))
        portal_id = item.portal_id
        user_id = item.user_id
        price_to_compare = item.price_to_compare

        start_schedule_datetime = {"start_weekday": -1, "start_time": -1}
        end_schedule_datetime = {"end_weekday": -1, "end_time": -1}
        schedules_to_fill = {"Schedules" : []}
        for row in prices:
            if row.price <= price_to_compare:
                # Calculate start & end datetime for setting to Victron scheduler
                start_weekday = row.start_time.weekday()
                start_time = str(row.start_time.time().hour * 3600)
                if start_weekday == 6:
                    start_weekday = 0
                else:
                    start_weekday = start_weekday + 1

                if start_schedule_datetime["start_weekday"] == -1 and start_schedule_datetime["start_time"] == -1:
                    # print(f"SET start weekday {start_weekday} and time {start_time}")
                    start_schedule_datetime["start_weekday"] = start_weekday
                    start_schedule_datetime["start_time"] = start_time
                    print(start_schedule_datetime)

                end_weekday = row.end_time.weekday()
                end_time = str(row.end_time.time().hour * 3600)
                if end_weekday == 6:
                    end_weekday = 0
                else:
                    end_weekday = end_weekday + 1
                if end_schedule_datetime["end_weekday"] == -1 and end_schedule_datetime["end_time"] == -1:
                    # print(f"SET end weekday {end_weekday} and time {end_time}")
                    end_schedule_datetime["end_weekday"] = end_weekday
                    end_schedule_datetime["end_time"] = end_time
                    print(end_schedule_datetime)
                    continue

                if end_schedule_datetime["end_weekday"] == start_weekday and end_schedule_datetime["end_time"] == start_time:
                    # print(f"UPDATE end time {end_time}")
                    # if end_schedule_datetime["end_weekday"] == end_weekday:
                    end_schedule_datetime["end_time"] = end_time
                    end_schedule_datetime["end_weekday"] = end_weekday
                    # elif int(end_time) == 0:
                    #     end_schedule_datetime["end_time"] = str(24*3600)

                    print(end_schedule_datetime)
                    continue
                else:
                    if start_schedule_datetime["start_weekday"] != -1 and end_schedule_datetime["end_weekday"] != -1:
                        schedules_to_fill["Schedules"].append({"StartWeekday": start_schedule_datetime["start_weekday"], "StartTime": start_schedule_datetime["start_time"], "EndWeekday": end_schedule_datetime["end_weekday"], "EndTime": end_schedule_datetime["end_time"]})

                    start_schedule_datetime["start_weekday"] = start_weekday
                    start_schedule_datetime["start_time"] = start_time
                    end_schedule_datetime["end_weekday"] = end_weekday
                    end_schedule_datetime["end_time"] = end_time
                    print(start_schedule_datetime)
                    print(end_schedule_datetime)
        if start_schedule_datetime["start_weekday"] != -1 and end_schedule_datetime["end_weekday"] != -1:
            last_victron_schedule: VictronSchedulesToFill = db.query(VictronSchedulesToFill).filter(VictronSchedulesToFill.user_id == user_id).order_by(VictronSchedulesToFill.id.desc()).first()
            if {"StartWeekday": start_schedule_datetime["start_weekday"], "StartTime": start_schedule_datetime["start_time"], "EndWeekday": end_schedule_datetime["end_weekday"], "EndTime": end_schedule_datetime["end_time"]} not in schedules_to_fill["Schedules"]:
                    schedules_to_fill["Schedules"].append({"StartWeekday": start_schedule_datetime["start_weekday"], "StartTime": start_schedule_datetime["start_time"], "EndWeekday": end_schedule_datetime["end_weekday"], "EndTime": end_schedule_datetime["end_time"]})
                    if not last_victron_schedule or last_victron_schedule.to_fill != str(schedules_to_fill):
                        new_schedules = VictronSchedulesToFill(
                            to_fill = str(schedules_to_fill),
                            user_id = user_id,
                        )
                        print("Adding new schedules")
                        print(new_schedules.to_fill)
                        db.add(new_schedules)
                        db.commit()