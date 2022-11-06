import asyncio
import board
import busio
import keypad

from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from adafruit_lis3dh import LIS3DH_I2C
from rtc import RTC

from app.utils import matrix_rotation, parse_timestamp

BIT_DEPTH = 6
NTP_ENABLE = True
NTP_INTERVAL = 60 * 60  # 1h
ASYNCIO_LOOP_DELAY = 0.005  # secs


class Manager:
    def __init__(self, theme, debug=False):
        print("manager: init", theme, debug)
        # RGB Matrix
        self.matrix = Matrix(bit_depth=BIT_DEPTH)
        # Accelerometer
        self.accelerometer = LIS3DH_I2C(busio.I2C(board.SCL, board.SDA), address=0x19)
        _ = self.accelerometer.acceleration  # drain startup readings
        # Display Buffer
        self.display = self.matrix.display
        self.display.rotation = matrix_rotation(self.accelerometer)
        # Networking
        self.network = Network(status_neopixel=board.NEOPIXEL, debug=debug)
        # Theme
        self.theme = theme(display=self.display)
        # GPIO Buttons
        self.last_pressed = None

    def run(self):
        print("manager.run")
        while True:
            try:
                asyncio.run(self.loop())
            finally:
                print("manager: asyncio crash, restarting")
                asyncio.new_event_loop()

    async def ntp_update(self):
        timestamp = self.network.get_local_time()
        print(f"manager: ntp set: {timestamp}, retrying in {NTP_INTERVAL}s")
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
        print(f"manager: loop")
        if NTP_ENABLE:
            asyncio.create_task(self.ntp_update())
        asyncio.create_task(self.check_gpio_buttons())
        while True:
            asyncio.create_task(self.theme.loop(last_pressed=self.last_pressed))
            self.last_pressed = None
            await asyncio.sleep(ASYNCIO_LOOP_DELAY)
