import math
import random
import time
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from displayio import Group
from rtc import RTC

from app.themes._base import BaseSprite, BaseTheme
from app.utils import load_sprites_brightness_adjusted, copy_update_palette

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


class MarioTheme(BaseTheme):
    spritesheet_file = "/app/themes/mario.bmp"

    def __init__(self, display):
        super().__init__(display)
        # Display & Resources
        self.display = display
        self.bitmap, self.palette = load_sprites_brightness_adjusted(
            self.spritesheet_file, transparent_index=31
        )
        self.font_bitocra = bitmap_font.load_font("/bitocra7.bdf")

    async def setup(self):
        # Call base setup
        await super().setup()
        # Primitives
        self.group_root = Group()
        # Background
        self.group_root.append(Group())  # empty placeholder group for now
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
        self.group_root.append(group_actors)
        # Labels
        group_labels = Group()
        self.label_clock = ClockLabel(31, 3, font=self.font_bitocra)
        group_labels.append(self.label_clock)
        self.label_calendar = CalendarLabel(1, 3, font=self.font_bitocra)
        group_labels.append(self.label_calendar)
        self.group_root.append(group_labels)
        # Render Display
        await self.update_background()

    async def loop(self, button=None):
        if self.frame % 500 == 0:
            if (self.sprite_mario.x <= -16 or self.sprite_mario.x >= 64) and (
                self.sprite_goomba.x <= -16 or self.sprite_goomba.x >= 64
            ):
                print(
                    f"THEME::LOOP - mario (x: {self.sprite_mario.x}) and goomba (x: {self.sprite_goomba.x}) off screen, regenerating background"
                )
                await self.update_background()
        if button is not None:
            print(f"THEME::BUTTON - button:{button}")
            await self.update_background()
        self.label_clock.tick(self.frame)
        self.label_calendar.tick(self.frame)
        self.sprite_mario.tick(self.frame)
        self.sprite_goomba.tick(self.frame)
        # Call base loop at end of function (to increment frame index etc)
        await super().loop(button)

    async def update_background(self):
        self.group_root[0] = self._build_random_background_group()
        self.display.show(self.group_root)

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
        week_num = math.floor(now.tm_yday / 7)
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


class ClockLabel(Label):
    def __init__(self, x, y, font, color=0x111111):
        super().__init__(text="00:00:00", font=font, color=color)
        self.x = x
        self.y = y
        self.new_second = None

    def tick(self, frame):
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

    def tick(self, frame):
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


class MarioSprite(BaseSprite):
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
        self.x_range = [-32, 96]
        self.y_float = y
        self.is_jumping = False
        self.x_dir_last = 1

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_float -= 10

    def tick(self, frame):
        if frame % 800 == 0:
            self.jump()
        if self.seed >= 0 and self.seed <= 3:
            self.move_to(x=random.randint(self.x_range[0], self.x_range[1]))
        if self.is_jumping:
            self.y_float += GRAVITY
        if self.y_float > self.y_orig:
            self.y_float = self.y_orig
            self.is_jumping = False
        if frame % 4 == 0:
            self.idx_sprite += 1
            if self.idx_sprite > 2:
                self.idx_sprite = 0

        facing_right = self.x_dir_last > 0

        walk_start_idx = (
            SPRITE_MARIO_R_WALK_START if facing_right else SPRITE_MARIO_L_WALK_START
        )

        self[0] = (
            walk_start_idx + self.idx_sprite
            if self.x_velocity != 0
            else (SPRITE_MARIO_R_JUMP if facing_right else SPRITE_MARIO_L_JUMP)
            if self.is_jumping
            else (SPRITE_MARIO_R_STILL if facing_right else SPRITE_MARIO_L_STILL)
        )
        self.y = int(self.y_float)
        super().tick(frame)


class GoombaSprite(BaseSprite):
    _name = "goomba"

    def __init__(self, bitmap, palette, x, y):
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            default_tile=SPRITE_GOOMBA_STILL,
        )
        self.x_range = [-32, 96]
        self.idx_sprite = 0

    def tick(self, frame):
        if self.seed >= 0 and self.seed <= 5:
            self.move_to(x=random.randint(self.x_range[0], self.x_range[1]))
        if frame % 8 == 0:
            self.idx_sprite += 1
            if self.idx_sprite > 1:
                self.idx_sprite = 0
        self[0] = (
            SPRITE_GOOMBA_WALK + self.idx_sprite
            if self.x_velocity != 0
            else SPRITE_GOOMBA_STILL
        )
        super().tick(frame)


class BrickSprite(BaseSprite):
    _name = "brick"

    def __init__(self, bitmap, palette, x, y, width=1, height=1, underground=False):
        if underground:
            palette = copy_update_palette(
                palette,
                {7: 0x000033, 10: 0x0060, 11: 0x006066, 12: 0x000055, 13: 0x000044},
            )
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            width=width,
            height=height,
            default_tile=SPRITE_BRICK,
        )


class RockSprite(BaseSprite):
    _name = "rock"

    def __init__(self, bitmap, palette, x, y, width=1, height=1, underground=False):
        if underground:
            palette = copy_update_palette(
                palette,
                {7: 0x000033, 10: 0x006077, 11: 0x006066, 12: 0x000055, 13: 0x000044},
            )
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            width=width,
            height=height,
            default_tile=SPRITE_ROCK,
        )


class PipeSprite(BaseSprite):
    _name = "pipe"
    PALETTE_BLUE = {14: 0x000066, 15: 0x000011}
    PALETTE_GREY = {14: 0x111111, 15: 0x080808}

    def __init__(self, bitmap, palette, x, y, height=1, color=None):
        if color is not None:
            palette = copy_update_palette(palette, color)
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            width=1,
            height=height,
            default_tile=SPRITE_PIPE,
        )
