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

# Static Resources

sprites_bitmap, sprites_palette = load_sprites_brightness_adjusted("/sprites.bmp", transparent_index=31)
font_bitocra = bitmap_font.load_font("/bitocra7.bdf")

DEBUG = secrets.get("debug", False)
NTP_ENABLE = secrets.get("ntp_enable", True)
NTP_INTERVAL = secrets.get("ntp_interval", 3600)
BIT_DEPTH = secrets.get("matrix_bit_depth", 6)
COLOR_ORDER = secrets.get("matrix_color_order", "RGB")


# Manager Logic


class Manager:
    def __init__(self, theme, debug=DEBUG):
        print(f"Manager > Init: Theme = {theme}")
        self.debug = debug
        # RGB Matrix
        self.matrix = Matrix(bit_depth=BIT_DEPTH, color_order=COLOR_ORDER)
        # Accelerometer
        self.accelerometer = LIS3DH_I2C(I2C(board.SCL, board.SDA), address=0x19)
        _ = self.accelerometer.acceleration  # drain startup readings
        # Display Buffer
        self.display = self.matrix.display
        self.display.rotation = matrix_rotation(self.accelerometer)
        self.display.show(build_splash_group(font=font_bitocra))
        # Networking
        self.network = Network(status_neopixel=board.NEOPIXEL, debug=self.debug)
        self.network.connect()
        gc.collect()
        # MQTT
        self.mqtt = MQTTClient(self.network._wifi.esp, secrets, debug=self.debug)
        gc.collect()
        # Theme
        self.theme = theme(display=self.display, bitmap=sprites_bitmap, palette=sprites_palette, font=font_bitocra, debug=self.debug)
        gc.collect()
        # GPIO Buttons
        self.last_pressed = None
        # State
        self.state = {"frame": 0}

    def run(self):
        print(f"Manager > Run")
        while True:
            try:
                asyncio.run(self.loop())
            finally:
                print(f"Manager > Error: asyncio crash, restarting")
                asyncio.new_event_loop()

    async def ntp_update(self):
        timestamp = self.network.get_local_time()
        print(
            f"Manager > NTP: Set RTC to '{timestamp}', trying again in {NTP_INTERVAL}s"
        )
        timetuple = parse_timestamp(timestamp)
        RTC().datetime = timetuple
        await asyncio.sleep(NTP_INTERVAL)
        asyncio.create_task(self.ntp_update())

    async def check_gpio_buttons(self):
        with Keys(
            (board.BUTTON_UP, board.BUTTON_DOWN), value_when_pressed=False, pull=True
        ) as keys:
            while True:
                key_event = keys.events.get()
                if key_event and key_event.pressed:
                    key_number = key_event.key_number
                    self.last_pressed = key_number
                await asyncio.sleep(0)

    async def loop(self):
        print(f"Manager > Loop: Init")
        gc.collect()
        if NTP_ENABLE:
            asyncio.create_task(self.ntp_update())
        asyncio.create_task(self.check_gpio_buttons())
        await asyncio.create_task(self.theme.setup())
        self.mqtt.subscribe("test/topic", 1)
        print(f"Manager > Loop: Start")
        while True:
            gc.collect()
            frame = self.state["frame"]
            await asyncio.create_task(self.theme.loop(button=self.last_pressed))
            await asyncio.create_task(self.mqtt.poll())
            self.last_pressed = None
            self.state["frame"] = frame + 1
            if self.debug:
                print(
                    "Manager > Debug: Mem={} | Frame={}".format(
                        gc.mem_free(), self.state["frame"]
                    )
                )
