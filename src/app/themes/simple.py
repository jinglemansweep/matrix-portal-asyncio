import gc

from displayio import Group
from rtc import RTC

from app.themes._base import BaseTheme
from app.themes._common import CalendarLabel, ClockLabel


GRAVITY = 0.75

SPRITE_MARIO_R_STILL = 0
SPRITE_MARIO_R_JUMP = 1
SPRITE_MARIO_R_WALK_START = 2  # 2,3,4
SPRITE_MARIO_L_STILL = 5
SPRITE_MARIO_L_JUMP = 6
SPRITE_MARIO_L_WALK_START = 7  # 7,8,9

SPRITE_BRICK = 10
SPRITE_ROCK = 11
SPRITE_PIPE = 12
SPRITE_GOOMBA_STILL = 15
SPRITE_GOOMBA_WALK = 16

BUTTON_UP = 0
BUTTON_DOWN = 1


class SimpleTheme(BaseTheme):
    __theme_name__ = "simple"

    def __init__(self, display, bitmap, palette, font, debug=False):
        super().__init__(display, bitmap, palette, font, debug)

    async def setup(self):
        # Call base setup
        await super().setup()
        # Background
        now = RTC().datetime
        group_labels = Group()
        self.label_clock = ClockLabel(33, 2, font=self.font)
        group_labels.append(self.label_clock)
        self.label_calendar = CalendarLabel(0, 2, font=self.font)
        group_labels.append(self.label_calendar)
        self.group.append(group_labels)
        gc.collect()

    async def tick(self, state):
        frame = state["frame"]
        self.label_clock.tick(frame)
        self.label_calendar.tick(frame)
        await super().tick(frame)

    async def on_button(self):
        await super().on_button()
