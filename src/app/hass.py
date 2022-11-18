import json

HASS_TOPIC_PREFIX = "homeassistant"
HASS_ENTITY_ID_PREFIX = "mqttmatrix_"


class Entity:
    def __init__(
        self,
        host_id,
        name,
        device_class,
        hass_topic_prefix,
        mqtt,
        options=None,
    ):
        if options is None:
            options = dict()
        self.name = f"{host_id}_{name}"
        self.device_class = device_class
        self.mqtt = mqtt
        self.options = options
        self.hass_topic_prefix = hass_topic_prefix
        topic_prefix = self._build_entity_topic_prefix()
        self.topic_config = f"{topic_prefix}/config"
        self.topic_command = f"{topic_prefix}/set"
        self.topic_state = f"{topic_prefix}/state"
        self.state = dict()

    def configure(self):
        auto_config = dict(
            name=self.name,
            unique_id=self.name,
            device_class=self.device_class,
            schema="json",
            command_topic=self.topic_command,
            state_topic=self.topic_state,
        )
        config = auto_config.copy()
        config.update(self.options)
        print(f"hass.entity.configure: name={self.name} config={config}")
        self.mqtt.publish(self.topic_config, json.dumps(config), retain=True, qos=1)
        self.mqtt.subscribe(self.topic_command, 1)

    def get_state(self):
        return self.state

    def update(self, new_state=None):
        if new_state is None:
            new_state = dict()
        self.state.update(new_state)
        print(f"HASS > Entity Update: Name={self.name} State={self.state}")
        payload = (
            self.state.get("state")
            if self.device_class == "switch"
            else json.dumps(self.state)
        )
        self.mqtt.publish(self.topic_state, payload, retain=True, qos=1)

    def _build_entity_topic_prefix(self):
        return f"{self.hass_topic_prefix}/{self.device_class}/{self.name}"


class HASS:
    def __init__(self, mqtt, device_id, state, topic_prefix=HASS_TOPIC_PREFIX):
        self.device_id = device_id
        self.mqtt = mqtt
        self.topic_prefix = topic_prefix
        self.entities = dict()
        print(f"HASS > Init: Device={device_id} TopicPrefix={topic_prefix}")
        pass

    def add_entity(self, name, device_class, options=None, initial_state=None):
        entity = Entity(
            self.device_id,
            name,
            device_class,
            self.topic_prefix,
            self.mqtt,
            options,
        )
        entity.configure()
        entity.update(initial_state)
        self.entities[name] = entity
        return entity
