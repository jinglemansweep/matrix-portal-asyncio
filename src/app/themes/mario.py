import random
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from displayio import Group
from rtc import RTC

from app.themes._base import BaseSprite
from app.utils import load_sprites_brightness_adjusted, copy_update_palette

SPRITESHEET_FILE = "/app/themes/mario.bmp"

GRAVITY = 0.75

SPRITE_MARIO_STILL = 0
SPRITE_MARIO_JUMP = 1
SPRITE_MARIO_WALK1 = 4
SPRITE_MARIO_WALK2 = 5
SPRITE_MARIO_WALK3 = 6
SPRITE_BRICK = 8
SPRITE_ROCK = 9
SPRITE_PIPE = 10
SPRITE_GOOMBA = 12


class MarioTheme:
    def __init__(self, display):
        # Display & Resources
        self.display = display
        self.bitmap, self.palette = load_sprites_brightness_adjusted(
            SPRITESHEET_FILE, transparent_index=31
        )
        self.font_bitocra = bitmap_font.load_font("/bitocra7.bdf")
        # Primitives
        root = Group()
        # Ground
        group_floor = Group()
        self.sprite_floor_brick = BrickSprite(
            bitmap=self.bitmap,
            palette=self.palette,
            x=0,
            y=24,
            width=3,
            underground=True,
        )
        group_floor.append(self.sprite_floor_brick)
        self.sprite_floor_rock = RockSprite(
            bitmap=self.bitmap,
            palette=self.palette,
            x=48,
            y=24,
            width=1,
        )
        group_floor.append(self.sprite_floor_rock)
        root.append(group_floor)
        # Items
        group_items = Group()
        self.sprite_pipe = PipeSprite(
            bitmap=self.bitmap, palette=self.palette, x=48, y=8
        )
        group_floor.append(self.sprite_pipe)
        root.append(group_items)
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
        root.append(group_actors)
        # Labels
        group_labels = Group()
        self.label_clock = ClockLabel(31, 3, font=self.font_bitocra)
        group_labels.append(self.label_clock)
        self.label_calendar = CalendarLabel(1, 3, font=self.font_bitocra)
        group_labels.append(self.label_calendar)
        root.append(group_labels)
        # Properties
        self.frame = 0
        # Render Display
        self.display.show(root)

    async def loop(self, last_pressed=None):
        if last_pressed is not None:
            print("button", last_pressed)

        self.label_clock.tick(self.frame)
        self.label_calendar.tick(self.frame)
        self.sprite_mario.tick(self.frame)
        self.sprite_goomba.tick(self.frame)
        self.sprite_pipe.tick(self.frame)

        self.frame += 1


class ClockLabel(Label):
    def __init__(self, x, y, font, color=0x111111):
        super().__init__(text="00:00:00", font=font, color=color)
        self.x = x
        self.y = y

    def tick(self, frame):
        now = RTC().datetime
        hhmmss = "{:0>2d}:{:0>2d}:{:0>2d}".format(now.tm_hour, now.tm_min, now.tm_sec)
        self.text = hhmmss


class CalendarLabel(Label):
    def __init__(self, x, y, font, color=0x001100):
        super().__init__(text="00/00", font=font, color=color)
        self.x = x
        self.y = y

    def tick(self, frame):
        now = RTC().datetime
        ddmm = "{:0>2d}/{:0>2d}".format(now.tm_day, now.tm_mon)
        self.text = ddmm


class MarioSprite(BaseSprite):
    def __init__(self, bitmap, palette, x, y):
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            default_tile=SPRITE_MARIO_STILL,
        )
        self.idx_sprite = 0
        self.y_float = y
        self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_float -= 10

    def tick(self, frame):

        super().tick(frame=frame)

        if frame % 800 == 0:
            self.jump()

        if frame % 400 == 0:
            self.set_velocity(1, 0)

        if frame % 400 == 200:
            self.stop()

        if self.is_jumping:
            self.y_float += GRAVITY

        if self.y_float > self.y_orig:
            self.y_float = self.y_orig
            self.is_jumping = False

        if frame % 4 == 0:
            self.idx_sprite += 1
            if self.idx_sprite > 2:
                self.idx_sprite = 0

        self[0] = (
            SPRITE_MARIO_WALK1 + self.idx_sprite
            if self.x_velocity > 0
            else SPRITE_MARIO_JUMP
            if self.is_jumping
            else SPRITE_MARIO_STILL
        )
        self.y = int(self.y_float)

        if self.x > 64:
            self.x = -16


class BrickSprite(BaseSprite):
    def __init__(self, bitmap, palette, x, y, width=1, height=1, underground=False):
        if underground:
            palette = copy_update_palette(
                palette,
                {7: 0x00033, 10: 0x006077, 11: 0x006066, 12: 0x000055, 13: 0x000044},
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
    def __init__(self, bitmap, palette, x, y, width=1, height=1, underground=False):
        if underground:
            palette = copy_update_palette(
                palette,
                {7: 0x00033, 10: 0x006077, 11: 0x006066, 12: 0x000055, 13: 0x000044},
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
    def __init__(self, bitmap, palette, x, y, height=1):
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            width=1,
            height=height,
            default_tile=SPRITE_PIPE,
        )


class GoombaSprite(BaseSprite):
    def __init__(self, bitmap, palette, x, y):
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            default_tile=SPRITE_GOOMBA,
        )
        self.range = 10

    def tick(self, frame):

        super().tick(frame=frame)

        if frame % 10 == 0:
            dir = random.randint(-1, 1)
            x = self.x + dir
            if x > self.x_orig + self.range:
                x = self.x_orig + self.range
            if x < self.x_orig - self.range:
                x = self.x_orig - self.range
            self.x = x
