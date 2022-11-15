import asyncio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from secrets import secrets


def on_message(mqtt_client, topic, message):
    print(f"MQTT: {topic} => {message}")


async def poll_mqtt(mqtt_client):
    mqtt_client.loop(timeout=0.0001)

def setup_mqtt_client(network):
    MQTT.set_socket(socket, network._wifi.esp)
    mqtt_client = MQTT.MQTT(
        broker=secrets.get("mqtt_broker"),
        username=secrets.get("mqtt_user"),
        password=secrets.get("mqtt_password"),
        port=secrets.get("mqtt_port", 1883),
    )
    mqtt_client.on_connect = connect
    mqtt_client.on_disconnect = disconnect
    mqtt_client.on_subscribe = subscribe
    mqtt_client.on_unsubscribe = unsubscribe
    mqtt_client.on_publish = publish
    mqtt_client.on_message = message
    mqtt_client.connect()
    return mqtt_client


def connect(mqtt_client, userdata, flags, rc):
    print("Connected to MQTT Broker!")
    print("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    print("Disconnected from MQTT Broker!")


def subscribe(mqtt_client, userdata, topic, granted_qos):
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(mqtt_client, userdata, topic, pid):
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


def publish(mqtt_client, userdata, topic, pid):
    print("Published to {0} with PID {1}".format(topic, pid))


def message(client, topic, message):
    print("New message on topic {0}: {1}".format(topic, message))
