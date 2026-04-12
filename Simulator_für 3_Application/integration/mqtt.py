import json
import logging
import time
from datetime import datetime, timedelta
from random import randrange

import paho.mqtt.client as mqtt

# Get the logger
logger = logging.getLogger(__name__)


class MqttClient:
    def __init__(self, config, profile):
        self.profile = profile
        self.broker_host = config['mqtt'].get('broker')
        self.broker_port = int(config['mqtt'].get('port'))
        self.transport = config['mqtt'].get('transport')
        self.topic = f"{config['DEFAULT'].get('company')}/{config['DEFAULT'].get('container')}"
        self.token = config['mqtt'].get('token')
        client_id = "simulator_" + str(randrange(100))
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, protocol=mqtt.MQTTv5, transport=self.transport)
        self.client.on_connect = self.on_connect
        self.client.username_pw_set(self.token)
        self.connected = False
        self.clock = float(config['simulation'].get('clock-rate'))

    def on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
        else:
            print("Connection failed with code", rc)

    def connect(self):
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()

    def is_connected(self):
        return self.connected

    async def publish(self, route, points):
        if not self.connected:
            print("Not connected to MQTT broker. Please connect first.")
            return
        start_time = datetime.now()
        msg = {"timestamp": start_time, "action": "START", "name": route}
        self.client.publish(
            self.topic + "/state", payload=json.dumps(msg, default=str))
        # loop over all recorded points
        act_time = start_time
        for i, point in enumerate(points):
            temp, hum = self.profile.simulate(i, len(points))
            act_time = act_time + timedelta(0, 5)  # simulate interval of 5sec
            msg = {"timestamp": act_time,
                   "lat": point[0], "lon": point[1], "temp": temp, "hum": hum}
            self.client.publish(self.topic + "/message",
                                payload=json.dumps(msg, default=str))
            logging.debug('sent message {}'.format(msg))
            # wait
            time.sleep(self.clock)
        msg = {"timestamp": datetime.now(), "action": "STOP", "name": route}
        self.client.publish(self.topic + "/state", payload=json.dumps(msg, default=str))

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("Disconnected from MQTT broker")
