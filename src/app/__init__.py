import asyncio
import board
from busio import I2C
import gc
from keypad import Keys
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
from adafruit_bitmap_font import bitmap_font
from adafruit_lis3dh import LIS3DH_I2C
from rtc import RTC
from secrets import secrets

from app.mqtt import MQTTClient
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
        gc.collect()
        # MQTT
        self.group_splash[1].text = "mqtt"
        self.mqtt = MQTTClient(self.network._wifi.esp, secrets, debug=self.debug)
        gc.collect()
        # Theme
        self.group_splash[1].text = "themes"
        self.themes = self.install_themes(themes)
        gc.collect()
        # State
        self.state = {"frame": 0, "theme": 0, "button": None}

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
        asyncio.create_task(self.mqtt.poll())
        self.group_splash[1].text = "almost done"
        await asyncio.create_task(self.setup_themes())
        self.mqtt.subscribe("test/topic", 1)
        print(
            "Manager > Loop Start: Theme={} Mem={}".format(
                self.get_theme(), gc.mem_free()
            )
        )
        while True:
            await self.tick()
            await asyncio.sleep(0.00001)

    async def tick(self):
        theme_idx = self.state["theme"]
        frame = self.state["frame"]
        button = self.state["button"]
        theme = self.get_theme()
        await theme.tick(frame)
        group = await theme.render_group()
        self.display.show(group)
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

    async def _ntp_update(self):
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

    def install_themes(self, theme_classes):
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

    async def setup_themes(self):
        for theme in self.themes:
            await theme.setup()

    def get_theme(self):
        return self.themes[self.state["theme"]]

    def set_next_theme(self):
        count = len(self.themes)
        idx = self.state["theme"]
        idx += 1
        if idx + 1 > count:
            idx = 0
        self.state["theme"] = idx
