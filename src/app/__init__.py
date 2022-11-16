import asyncio
import board
from busio import I2C
import gc
from keypad import Keys
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
from adafruit_bitmap_font import bitmap_font
from adafruit_lis3dh import LIS3DH_I2C
from displayio import Group
from rtc import RTC
from secrets import secrets


from app.utils import matrix_rotation, parse_timestamp, load_sprites_brightness_adjusted
from app.themes._common import build_splash_group

# Constants

BUTTON_UP = 0
BUTTON_DOWN = 1

BUTTON_THEME_CHANGE = BUTTON_DOWN
BUTTON_THEME_ACTION = BUTTON_UP

# Static Resources

sprites_bitmap, sprites_palette = load_sprites_brightness_adjusted(
    "/sprites.bmp", transparent_index=31
)
font_bitocra = bitmap_font.load_font("/bitocra7.bdf")

DEBUG = secrets.get("debug", False)
NTP_ENABLE = secrets.get("ntp_enable", True)
NTP_INTERVAL = secrets.get("ntp_interval", 3600)
BIT_DEPTH = secrets.get("matrix_bit_depth", 6)
COLOR_ORDER = secrets.get("matrix_color_order", "RGB")
MQTT_PREFIX = secrets.get("mqtt_prefix", "matrixportal")


# Manager Logic


class Manager:
    def __init__(self, themes=None, debug=DEBUG):
        print(f"Manager > Init: Themes={themes}")
        self.debug = debug
        # RGB Matrix
        self.matrix = Matrix(bit_depth=BIT_DEPTH, color_order=COLOR_ORDER)
        # Accelerometer
        self.accelerometer = LIS3DH_I2C(I2C(board.SCL, board.SDA), address=0x19)
        _ = self.accelerometer.acceleration  # drain startup readings
        # Display Buffer
        self.display = self.matrix.display
        self.display.rotation = matrix_rotation(self.accelerometer)
        self.group_splash = build_splash_group(font=font_bitocra)
        self.display.show(self.group_splash)
        # Networking
        self.group_splash[1].text = "wifi"
        self.network = Network(status_neopixel=board.NEOPIXEL, debug=self.debug)
        self.network.connect()
        mac = self.network._wifi.esp.MAC_address
        self.device_id = "{:02x}{:02x}{:02x}{:02x}".format(
            mac[0], mac[1], mac[2], mac[3]
        )
        gc.collect()
        # MQTT
        MQTT.set_socket(socket, self.network._wifi.esp)  # network._wifi.esp
        self.group_splash[1].text = "mqtt"
        self.mqtt = MQTT.MQTT(
            broker=secrets.get("mqtt_broker"),
            username=secrets.get("mqtt_user"),
            password=secrets.get("mqtt_password"),
            port=secrets.get("mqtt_port", 1883),
        )
        self.mqtt.on_connect = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_message = self._on_mqtt_message
        self.mqtt.connect()
        gc.collect()
        # Theme
        self.group_splash[1].text = "themes"
        self.themes = self._install_themes(themes)
        gc.collect()
        # State
        self.state = {
            "frame": 0,
            "theme": 0,
            "button": None,
            "blank": False,
            "time_visible": True,
            "date_visible": True,
        }

    def run(self):
        print(f"Manager > Run")
        while True:
            try:
                asyncio.run(self.loop())
            finally:
                print(f"Manager > Error: asyncio crash, restarting")
                asyncio.new_event_loop()

    async def loop(self):
        print(f"Manager > Loop Init")
        gc.collect()
        if NTP_ENABLE:
            self.group_splash[1].text = "ntp"
            asyncio.create_task(self._ntp_update())
        asyncio.create_task(self._check_gpio_buttons())
        asyncio.create_task(self._mqtt_poll())
        self.group_splash[1].text = "almost done"
        await asyncio.create_task(self._setup_themes())
        self.mqtt.subscribe(f"matrixportal/{self.device_id}/#", 1)
        print(
            "Manager > Loop Start: Device={} | Theme={} | Mem={}".format(
                self.device_id, self.get_theme(), gc.mem_free()
            )
        )
        while True:
            await self.tick()
            await asyncio.sleep(0.0001)

    async def tick(self):
        theme_idx = self.state["theme"]
        frame = self.state["frame"]
        button = self.state["button"]
        blank = self.state["blank"]
        theme = self.get_theme()
        await theme.tick(self.state)
        group = await theme.render_group()
        self.display.show(group if not blank else Group())
        if button is not None:
            if button == BUTTON_THEME_ACTION:
                await asyncio.create_task(theme.on_button())
            elif button == BUTTON_THEME_CHANGE:
                self.set_next_theme()
            self.state["button"] = None
        self.state["frame"] = frame + 1
        if frame % 100 == 0:
            gc.collect()
            if self.debug:
                print(
                    "Manager > Debug: Mem={} | Theme={} [{}] | Frame={}".format(
                        gc.mem_free(), theme.__theme_name__, theme_idx, frame
                    )
                )

    def get_theme(self):
        return self.themes[self.state["theme"]]

    def set_next_theme(self):
        count = len(self.themes)
        idx = self.state["theme"]
        idx += 1
        if idx + 1 > count:
            idx = 0
        self.state["theme"] = idx

    async def _ntp_update(self):
        self.group_splash[1].text = "ntp"
        timestamp = self.network.get_local_time()
        print(
            f"Manager > NTP: Set RTC to '{timestamp}', trying again in {NTP_INTERVAL}s"
        )
        timetuple = parse_timestamp(timestamp)
        RTC().datetime = timetuple
        await asyncio.sleep(NTP_INTERVAL)
        asyncio.create_task(self.ntp_update())

    async def _check_gpio_buttons(self):
        with Keys(
            (board.BUTTON_UP, board.BUTTON_DOWN), value_when_pressed=False, pull=True
        ) as keys:
            while True:
                key_event = keys.events.get()
                if key_event and key_event.pressed:
                    key_number = key_event.key_number
                    self.state["button"] = key_number
                await asyncio.sleep(0.001)

    async def _mqtt_poll(self, timeout=0.000001):
        while True:
            self.mqtt.loop(timeout=timeout)
            await asyncio.sleep(timeout)

    def _on_mqtt_message(self, client, topic, message):
        print(f"MQTT > Message: Topic={topic} | Message={message}")
        if topic == f"{MQTT_PREFIX}/{self.device_id}/visible":
            self.state["blank"] = not self.state["blank"]
        if topic == f"{MQTT_PREFIX}/{self.device_id}/date/visible":
            self.state["date_visible"] = not self.state["date_visible"]
        if topic == f"{MQTT_PREFIX}/{self.device_id}/time/visible":
            self.state["time_visible"] = not self.state["time_visible"]
        if topic == f"{MQTT_PREFIX}/{self.device_id}/theme/next":
            self.set_next_theme()

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        print("MQTT > Connected: Flags={} | RC={}".format(flags, rc))

    def _on_mqtt_disconnect(self, client, userdata, rc):
        print("MQTT > Disconnected")

    def _install_themes(self, theme_classes):
        themes = []
        assert len(theme_classes) > 0
        for ThemeCls in theme_classes:
            theme = ThemeCls(
                display=self.display,
                bitmap=sprites_bitmap,
                palette=sprites_palette,
                font=font_bitocra,
                debug=self.debug,
            )
            themes.append(theme)
        return themes

    async def _setup_themes(self):
        for theme in self.themes:
            await theme.setup()
            gc.collect()
