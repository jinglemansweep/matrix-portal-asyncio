import gc

from displayio import Group
from rtc import RTC

from app.themes._base import BaseSprite, BaseTheme
from app.themes._common import CalendarLabel, ClockLabel
from app.themes.mario_common import BrickSprite


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


class MarioRunningTheme(BaseTheme):
    __theme_name__ = "mario_running"

    def __init__(self, display, bitmap, palette, font, debug=False):
        super().__init__(display, bitmap, palette, font, debug)

    async def setup(self):
        # Call base setup
        await super().setup()
        # Background
        now = RTC().datetime
        group_background = Group()
        self.sprite_floor = BrickSprite(
            bitmap=self.bitmap,
            palette=self.palette,
            x=0,
            y=24,
            width=4,
            underground=False,
        )
        self.sprite_floor_alt = BrickSprite(
            bitmap=self.bitmap,
            palette=self.palette,
            x=64,
            y=24,
            width=4,
            underground=False,
        )
        group_background.append(self.sprite_floor)
        group_background.append(self.sprite_floor_alt)
        self.group.append(group_background)
        # Actors
        group_actors = Group()
        self.sprite_mario = MarioRunningSprite(
            bitmap=self.bitmap, palette=self.palette, x=8, y=8
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
        gc.collect()

    async def tick(self, state):
        self.label_clock.tick(state)
        self.label_calendar.tick(state)
        self.sprite_mario.tick(state)
        if self.sprite_floor.x <= -64:
            self.sprite_floor.x = 64
        else:
            self.sprite_floor.x -= 1
        if self.sprite_floor_alt.x <= -64:
            self.sprite_floor_alt.x = 64
        else:
            self.sprite_floor_alt.x -= 1
        await super().tick(state)

    async def on_button(self):
        await super().on_button()


class MarioRunningSprite(BaseSprite):
    _name = "mario"

    def __init__(self, bitmap, palette, x, y):
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            default_tile=SPRITE_MARIO_R_STILL,
        )
        self.idx_sprite = 0
        self.y_float = y
        self.is_jumping = False
        self.x_dir_last = 1

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_float -= 10

    def tick(self, state):
        frame = state["frame"]
        if frame % 800 == 0:
            self.jump()
        if self.is_jumping:
            self.y_float += GRAVITY
        if self.y_float > self.y_orig:
            self.y_float = self.y_orig
            self.is_jumping = False
        if frame % 4 == 0:
            self.idx_sprite += 1
            if self.idx_sprite > 2:
                self.idx_sprite = 0

        facing_right = True

        walk_start_idx = (
            SPRITE_MARIO_R_WALK_START if facing_right else SPRITE_MARIO_L_WALK_START
        )

        self[0] = (
            (SPRITE_MARIO_R_JUMP if facing_right else SPRITE_MARIO_L_JUMP)
            if self.is_jumping
            else walk_start_idx + self.idx_sprite
        )
        self.y = int(self.y_float)
        super().tick(frame)
