import asyncio
import board
import busio
import displayio
import framebufferio
import keypad
import rgbmatrix
import time

# from adafruit_matrixportal.matrix import Matrix
# from adafruit_matrixportal.network import Network
# from adafruit_lis3dh import LIS3DH_I2C
from rtc import RTC

from app.utils import matrix_rotation, parse_timestamp

BIT_DEPTH = 5
FPS_TARGET = 30
NTP_ENABLE = False
NTP_INTERVAL = 60 * 60  # 1h
ASYNCIO_LOOP_DELAY = 0.1  # secs

displayio.release_displays()


class Manager:
    def __init__(self, theme, debug=False):
        print(f"MANAGER::INIT theme={theme} debug={debug}")
        # RGB Matrix
        # self.matrix = Matrix(bit_depth=BIT_DEPTH)
        self.matrix = rgbmatrix.RGBMatrix(
            width=64,
            height=64,
            bit_depth=BIT_DEPTH,
            rgb_pins=[board.R0, board.G0, board.B0, board.R1, board.G1, board.B1],
            addr_pins=[board.ROW_A, board.ROW_B, board.ROW_C, board.ROW_D, board.ROW_E],
            clock_pin=board.CLK,
            latch_pin=board.LAT,
            output_enable_pin=board.OE,
        )
        # Accelerometer
        # self.accelerometer = LIS3DH_I2C(busio.I2C(board.SCL, board.SDA), address=0x19)
        # _ = self.accelerometer.acceleration  # drain startup readings
        # Display Buffer
        self.display = framebufferio.FramebufferDisplay(self.matrix, auto_refresh=False)
        # self.display = self.matrix.display
        # self.display.rotation = matrix_rotation(self.accelerometer)
        # Networking
        # self.network = Network(status_neopixel=board.NEOPIXEL, debug=debug)
        # Theme
        self.theme = theme(display=self.display)
        # GPIO Buttons
        self.last_pressed = None

    def run(self):
        print(f"MANAGER::RUN")
        while True:
            try:
                asyncio.run(self.loop())
            finally:
                print(f"MANAGER::ERROR - asyncio crash, restarting")
                asyncio.new_event_loop()

    async def ntp_update(self):
        timestamp = self.network.get_local_time()
        print(f"MANAGER::NTP - set: {timestamp}, retrying in {NTP_INTERVAL}s")
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

    def refresh_display(self):
        self.display.refresh(
            minimum_frames_per_second=0, target_frames_per_second=FPS_TARGET
        )

    async def loop(self):
        print(f"MANAGER::LOOP")
        if NTP_ENABLE:
            asyncio.create_task(self.ntp_update())
        # asyncio.create_task(self.check_gpio_buttons())
        await self.theme.setup()
        print("theme setup")
        while True:
            await self.theme.loop(button=self.last_pressed)
            self.refresh_display()
            # self.display.refresh(target_frames_per_second=FPS_TARGET, minimum_frames_per_second=0)
            self.last_pressed = None
            time.sleep(0.001)
