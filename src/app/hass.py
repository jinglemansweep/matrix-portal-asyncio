import json

HASS_TOPIC_PREFIX = "homeassistant"
HASS_ENTITY_ID_PREFIX = "mqttmatrix_"


def build_topic_prefix(name, device_class):
    return f"{HASS_TOPIC_PREFIX}/{device_class}/{name}"


def advertise_hass_entity(mqtt, name, device_class, options=None):
    topic_prefix = build_topic_prefix(name, device_class)
    auto_config = dict(
        name=name,
        unique_id=name,
        device_class=device_class,
        schema="json",
        command_topic=f"{topic_prefix}/set",
        state_topic=f"{topic_prefix}/state",
    )
    if options is None:
        options = {}
    config = auto_config.copy()
    config.update(options)
    mqtt.publish(f"{topic_prefix}/config", json.dumps(config), retain=True, qos=1)
    mqtt.subscribe(f"{topic_prefix}/set", 1)
