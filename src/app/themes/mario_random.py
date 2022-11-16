import gc
from math import floor
import random

from displayio import Group
from rtc import RTC

from app.themes._base import BaseTheme
from app.themes._common import CalendarLabel, ClockLabel
from app.themes.mario_common import (
    BrickSprite,
    GoombaSprite,
    MarioSprite,
    PipeSprite,
    RockSprite,
)


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


class MarioRandomTheme(BaseTheme):
    __theme_name__ = "mario_random"

    def __init__(self, display, bitmap, palette, font, debug=False):
        super().__init__(display, bitmap, palette, font, debug)

    async def setup(self):
        # Call base setup
        await super().setup()
        # Background
        self.group.append(Group())  # empty placeholder group for now
        # Actors
        group_actors = Group()
        self.sprite_goomba = GoombaSprite(
            bitmap=self.bitmap, palette=self.palette, x=24, y=8
        )
        group_actors.append(self.sprite_goomba)
        self.sprite_mario = MarioSprite(
            bitmap=self.bitmap, palette=self.palette, x=0, y=8
        )
        group_actors.append(self.sprite_mario)
        self.group.append(group_actors)
        # Labels
        group_labels = Group()
        self.label_clock = ClockLabel(33, 2, font=self.font)
        group_labels.append(self.label_clock)
        self.label_calendar = CalendarLabel(0, 2, font=self.font)
        group_labels.append(self.label_calendar)
        self.group.append(group_labels)
        # Render Display
        await self.update_background()
        gc.collect()

    async def tick(self, state):
        frame = state["frame"]
        if frame % 1000 == 0:
            if (self.sprite_mario.x <= -16 or self.sprite_mario.x >= 64) and (
                self.sprite_goomba.x <= -16 or self.sprite_goomba.x >= 64
            ):
                await self.update_background()
        self.label_clock.tick(state)
        self.label_calendar.tick(state)
        self.sprite_mario.tick(state)
        self.sprite_goomba.tick(state)
        await super().tick(state)

    async def on_button(self):
        await self.update_background()
        await super().on_button()

    async def update_background(self):
        self.group[0] = self._build_random_background_group()
        gc.collect()

    def _build_random_background_group(self):
        now = RTC().datetime
        # struct_time(tm_year=2022, tm_mon=11, tm_mday=7, tm_hour=20, tm_min=40, tm_sec=50, tm_wday=0, tm_yday=311, tm_isdst=-1)
        len_brick = random.randint(1, 3)
        group = Group()
        floor_brick = BrickSprite(
            bitmap=self.bitmap,
            palette=self.palette,
            x=0,
            y=24,
            width=len_brick,
            underground=now.tm_hour >= 16 or now.tm_hour <= 8,
        )
        group.append(floor_brick)
        floor_rock = RockSprite(
            bitmap=self.bitmap,
            palette=self.palette,
            x=len_brick * 16,
            y=24,
            width=4 - len_brick,
            underground=now.tm_hour >= 20 or now.tm_hour <= 6,
        )
        group.append(floor_rock)
        week_num = floor(now.tm_yday / 7)
        alt_week = week_num % 2 == 0
        # Set pipe colour to blue (blue bin) or grey (black bin) collection reminder
        # Between midday Thursday and midday Friday, collection is Friday morning usually
        pipe_color = None
        if (now.tm_wday == 3 and now.tm_hour > 12) or (
            now.tm_wday == 4 and now.tm_hour < 12
        ):
            pipe_color = (
                PipeSprite.PALETTE_BLUE if alt_week else PipeSprite.PALETTE_GREY
            )
        pipe = PipeSprite(
            bitmap=self.bitmap,
            palette=self.palette,
            x=random.randint(0, 48),
            y=8,
            color=pipe_color,
        )
        group.append(pipe)
        return group
