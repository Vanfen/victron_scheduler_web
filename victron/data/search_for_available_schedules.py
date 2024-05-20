import base64
import json
import ssl
from time import sleep
from typing import List
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from database.session import get_db
from victron.models import VictronAvailableSchedules, VictronEnergy


flag_connected = 0
schedules = {"0": False, "1": False, "2": False, "3": False, "4": False}

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
        

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global schedules    
    val = json.loads(msg.payload)
    print(msg.topic+" -> "+str(val))
    # Parse the response message
    if "Charge" in msg.topic:
        # Get schedule id
        schedule_id = msg.topic[(msg.topic.find('Charge')+7):(msg.topic.find('Charge')+8)]
        if "Day" in msg.topic:
            if val['value'] == -7:
                schedules[schedule_id] = True


def on_disconnect(client: mqtt.Client, userdata, rc):
    global flag_connected
    print("Disconnected with code " + str(rc))
    client.loop_stop()
    flag_connected = 0

def write_available_schedules_to_file(db: Session, user_id: int):
    global schedules
    db_schedules = db.query(VictronAvailableSchedules).filter(VictronAvailableSchedules.user_id == user_id).first()
    print(schedules)
    if db_schedules:
        db_schedules.first=schedules["0"]
        db_schedules.second=schedules["1"]
        db_schedules.third=schedules["2"]
        db_schedules.fourth=schedules["3"]
        db_schedules.fifth=schedules["4"]
    else:
        new_schedules = VictronAvailableSchedules(
            first=schedules["0"],
            second=schedules["1"],
            third=schedules["2"],
            fourth=schedules["3"],
            fifth=schedules["4"],
            user_id=user_id,
        )
        db.add(new_schedules)
    db.commit()
    schedules = {"0": False, "1": False, "2": False, "3": False, "4": False}
    # with open("victron/data/available_schedules.txt", "w+") as file:
    #     for schedule_id in schedules:
    #         file.write(str(schedule_id) + "\n")

def search_for_available_schedules():
    global flag_connected
    global portal_id

    print("Search for available schedules")

    db = next(get_db())
    victron_data: List[VictronEnergy] = db.query(VictronEnergy).all()
    for item in victron_data:
        username = item.email
        password = base64.b64decode(item.password.decode("utf-8"))
        portal_id = item.portal_id
        user_id = item.user_id

        client = mqtt.Client("FindAvailable")
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
        client.username_pw_set(username=username, password=password)
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        client.connect("mqtt87.victronenergy.com", port=8883)

        client.loop_start()
        
        client.publish("R/%s/system/0/Serial" % portal_id)

        while 1:
            if flag_connected == 1:
                # Write id's of available schedules to the file
                write_available_schedules_to_file(db=db, user_id=user_id)
                sleep(1)
                client.disconnect()
                sleep(1)
                if not client.is_connected():
                    print("Client successfully disconnected")
                break
            else:
                print("Waiting for the connection to be established...")
                sleep(1)
