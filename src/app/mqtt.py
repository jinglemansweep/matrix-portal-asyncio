import asyncio
import gc
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_esp32spi.adafruit_esp32spi_socket as socket


class MQTTClient:
    def __init__(self, interface, secrets, debug=False):
        MQTT.set_socket(socket, interface)  # network._wifi.esp
        self.debug = debug
        self._client = MQTT.MQTT(
            broker=secrets.get("mqtt_broker"),
            username=secrets.get("mqtt_user"),
            password=secrets.get("mqtt_password"),
            port=secrets.get("mqtt_port", 1883),
        )
        self._setup_callbacks()
        self.connect()
        gc.collect()

    async def poll(self, timeout=0.0001):
        while True:
            self._client.loop(timeout=timeout)
            await asyncio.sleep(timeout*2)

    def connect(self):
        self._client.connect()

    def disconnect(self):
        self._client.disconnect()

    def subscribe(self, topic, qos=1):
        self._client.subscribe(topic, qos)

    def _on_message(self, client, topic, message):
        print(f"MQTT: {topic} => {message}")

    def _on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT Broker!")
        print("Flags: {0}\n RC: {1}".format(flags, rc))

    def _on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT Broker!")

    def _on_subscribe(self, client, userdata, topic, granted_qos):
        print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))

    def _on_unsubscribe(self, client, userdata, topic, pid):
        print("Unsubscribed from {0} with PID {1}".format(topic, pid))

    def _on_publish(self, client, userdata, topic, pid):
        print("Published to {0} with PID {1}".format(topic, pid))

    def _on_message(self, client, topic, message):
        print("New message on topic {0}: {1}".format(topic, message))

    def _setup_callbacks(self):
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_subscribe = self._on_subscribe
        self._client.on_unsubscribe = self._on_unsubscribe
        self._client.on_publish = self._on_publish
        self._client.on_message = self._on_message
