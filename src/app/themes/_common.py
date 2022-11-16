import time
from adafruit_display_text.label import Label
from displayio import Group
from rtc import RTC


def build_splash_group(font):
    group = Group()
    group.append(Label(x=5, y=5, text="jinglemansweep", font=font, color=0x666666))
    group.append(Label(x=5, y=25, text="loading...", font=font, color=0x666600))
    return group


class ClockLabel(Label):
    def __init__(self, x, y, font, color=0x111111):
        super().__init__(text="00:00:00", font=font, color=color)
        self.x = x
        self.y = y
        self.new_second = None

    def tick(self, state):
        frame = state["frame"]
        self.hidden = not state["time_visible"]
        now = RTC().datetime
        ts = time.monotonic()
        if self.new_second is None or ts > self.new_second + 1:
            self.new_second = ts
            hhmmss = "{:0>2d}:{:0>2d}:{:0>2d}".format(
                now.tm_hour, now.tm_min, now.tm_sec
            )
            self.text = hhmmss


class CalendarLabel(Label):
    def __init__(self, x, y, font, color=0x001100):
        super().__init__(text="00/00", font=font, color=color)
        self.x = x
        self.y = y
        self.new_hour = None
        self.new_minute = None
        self.new_second = None

    def tick(self, state):
        frame = state["frame"]
        self.hidden = not state["date_visible"]
        now = RTC().datetime
        ts = time.monotonic()
        if self.new_second is None or ts > self.new_second + 1:
            self.new_second = ts
            if self.new_minute is None or now.tm_sec == 0:
                self.new_minute = ts
                # print("new minute")
                if self.new_hour is None or now.tm_min == 0:
                    self.new_hour = ts
                    ddmm = "{:0>2d}/{:0>2d}".format(now.tm_mday, now.tm_mon)
                    self.text = ddmm
                    # print("new hour")
