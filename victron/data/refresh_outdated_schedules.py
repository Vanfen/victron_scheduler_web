import base64
import datetime
import json
import os
import ssl
from time import sleep
from typing import List
import paho.mqtt.client as mqtt

from database.session import get_db
from victron.models import VictronEnergy
from .victron_schedules import Schedule


flag_connected = 0
schedules = []

portal_id = ""

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client: mqtt.Client, userdata, flags, rc):
    global flag_connected
    print("Connected with result code "+str(rc))
    flag_connected = 1
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

    ids = [0, 1, 2, 3, 4]
    for num in ids:
        client.subscribe("N/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%d/Day" % (portal_id, num))
        client.subscribe("N/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%d/Start" % (portal_id, num))
        client.subscribe("N/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%d/Duration" % (portal_id, num))
        

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    val = json.loads(msg.payload)
    print(msg.topic+" -> "+str(val))
    # Parse the response message
    if "Charge" in msg.topic:
        # Get schedule id
        schedule_id = int(msg.topic[(msg.topic.find('Charge')+7):(msg.topic.find('Charge')+8)])
        # Add a new schedule to the list if not present
        if all(schedule.get_id() != schedule_id for schedule in schedules):
            new_schedule = Schedule()
            new_schedule.set_id(schedule_id)
            schedules.append(new_schedule)
        if "Day" in msg.topic:
            schedules[-1].set_day(val['value'])
        elif "Start" in msg.topic:
            schedules[-1].set_start_time(val['value'])
        elif "Duration" in msg.topic:
            schedules[-1].set_duration(val['value'])


def on_disconnect(client: mqtt.Client, userdata, rc):
    global flag_connected
    print("Disconnected with code " + str(rc))
    client.loop_stop()
    flag_connected = 0

def get_outdated_schedules():
    schedules_to_remove = []
    for schedule in schedules:
        # Skip disabled schedules
        if abs(schedule.get_day()) == 7:
            continue
        current_weekday = int(datetime.datetime.today().weekday())
        if current_weekday == 0 and schedule.get_python_day() == 6:
            weekdays_delta = 1
        else:
            # Get delta between current weekday and Victron scheduled weekday
            weekdays_delta = current_weekday - schedule.get_python_day()
        today = datetime.datetime.today()
        # Calculate datetime for the schedule start
        schedulte_datetime = today - datetime.timedelta(days=weekdays_delta)
        # Replace current time by the time from schedule
        schedulte_datetime = schedulte_datetime.replace(hour=schedule.get_python_start_time(), minute=0, second=0, microsecond=0)
        # Add schedule duration time
        schedulte_datetime = schedulte_datetime + datetime.timedelta(seconds=schedule.get_duration())
        # Check if currently checked schedule is overdue
        now_datetime = datetime.datetime.now()
        # if now_datetime > schedulte_datetime:
        schedules_to_remove.append(str(schedule.get_id()))
    return schedules_to_remove

def refresh_outdated_schedules():
    global flag_connected
    global portal_id

    print("Search for outdated schedules")

    db = next(get_db())
    victron_data: List[VictronEnergy] = db.query(VictronEnergy).all()
    for item in victron_data:
        username = item.email
        password = base64.b64decode(item.password.decode("utf-8"))
        portal_id = item.portal_id
        user_id = item.user_id

        client = mqtt.Client("FindUsed")
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
        client.username_pw_set(username=username, password=password)
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        client.connect("mqtt87.victronenergy.com", port=8883)

        client.loop_start()
        
        # Send ping to wake up Remote Console
        print(client.publish("R/%s/system/0/Serial" % portal_id))

        attempts = 0

        while 1:
            print("In while")
            if flag_connected == 1:
                # Wait until all schedules read
                while not len(schedules) == 5:
                    # print(schedules)
                    pass
                # Get outdated schedules
                schedules_to_remove = get_outdated_schedules()
                if len(schedules_to_remove) > 0:
                    for sch_num in schedules_to_remove:
                        sch_num = sch_num.rstrip()
                        day_published = client.publish("W/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%s/Day" % (portal_id, sch_num), json.dumps({"value": -7}))
                        day_published.wait_for_publish()
                        print("Day published = " + str(day_published.is_published()))
                        duration_published = client.publish("W/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%s/Duration" % (portal_id, sch_num), json.dumps({"value": 0}))
                        duration_published.wait_for_publish()
                        print("Duration published = " + str(duration_published.is_published()))
                        start_published = client.publish("W/%s/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/%s/Start" % (portal_id, sch_num), json.dumps({"value": 0}))
                        start_published.wait_for_publish()
                        print("Start published = " + str(start_published.is_published()))
                sleep(1)
                client.disconnect()
                sleep(1)
                if not client.is_connected():
                    print("Client successfully disconnected")
                break
            else:
                print("Waiting for the connection to be established...")
                attempts += 1
                sleep(1)
                if attempts > 15:
                    return False
