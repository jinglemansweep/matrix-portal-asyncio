import asyncio
import board
import busio
import gc
import keypad
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
from adafruit_lis3dh import LIS3DH_I2C
from rtc import RTC
from secrets import secrets

from app.mqtt import MQTTClient
from app.utils import matrix_rotation, parse_timestamp

NTP_ENABLE = secrets.get("ntp_enable", True)
NTP_INTERVAL = secrets.get("ntp_interval", 3600)
BIT_DEPTH = secrets.get("matrix_bit_depth", 6)
COLOR_ORDER = secrets.get("matrix_color_order", "RGB")

# Hardware setup


class Manager:
    def __init__(self, theme, debug=False):
        print(f"Manager > Init: Theme = {theme}, Debug = {debug}")
        self.debug = debug
        # RGB Matrix
        self.matrix = Matrix(bit_depth=BIT_DEPTH, color_order=COLOR_ORDER)
        # Accelerometer
        self.accelerometer = LIS3DH_I2C(busio.I2C(board.SCL, board.SDA), address=0x19)
        _ = self.accelerometer.acceleration  # drain startup readings
        # Display Buffer
        self.display = self.matrix.display
        self.display.rotation = matrix_rotation(self.accelerometer)
        # Networking
        self.network = Network(status_neopixel=board.NEOPIXEL, debug=debug)
        self.network.connect()
        # MQTT
        self.mqtt = MQTTClient(self.network._wifi.esp, secrets, debug=debug)
        # Theme
        self.theme = theme(display=self.display)
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
        with keypad.Keys(
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
                print(f"Manager > Debug: Frame = {self.frame}")
