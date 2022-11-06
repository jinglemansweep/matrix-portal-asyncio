import random
import adafruit_imageload
from cedargrove_palettefader.palettefader import PaletteFader
from displayio import Group
from app.themes._base import BaseSprite

SPRITESHEET_FILE = "/app/themes/mario.bmp"

PALETTE_GAMMA = 1.0
PALETTE_BRIGHTNESS = 0.1
PALETTE_NORMALIZE = True

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
        self.bitmap, bitmap_palette = adafruit_imageload.load(SPRITESHEET_FILE)
        bitmap_palette.make_transparent(31)
        self.palette = PaletteFader(
            bitmap_palette, PALETTE_BRIGHTNESS, PALETTE_GAMMA, PALETTE_NORMALIZE
        ).palette
        # Primitives
        root = Group()
        # Ground
        group_floor = Group()
        self.floor_brick = BrickSprite(
            bitmap=self.bitmap, palette=self.palette, x=0, y=24, width=4
        )
        group_floor.append(self.floor_brick)
        root.append(group_floor)
        # Items
        group_items = Group()
        self.item_pipe = PipeSprite(bitmap=self.bitmap, palette=self.palette, x=48, y=8)
        group_floor.append(self.item_pipe)
        root.append(group_items)
        # Actors
        group_actors = Group()
        self.goomba = GoombaSprite(bitmap=self.bitmap, palette=self.palette, x=24, y=8)
        group_actors.append(self.goomba)
        self.mario = MarioSprite(bitmap=self.bitmap, palette=self.palette, x=0, y=8)
        group_actors.append(self.mario)
        root.append(group_actors)
        # Properties
        self.frame = 0
        # Render Display
        self.display.show(root)

    async def loop(self):
        self.mario.tick(self.frame)
        self.goomba.tick(self.frame)
        self.frame += 1


class MarioSprite(BaseSprite):
    def __init__(self, bitmap, palette, x, y):
        super().__init__(
            bitmap=bitmap,
            palette=palette,
            x=x,
            y=y,
            default_tile=SPRITE_MARIO_STILL,
        )
        self.sprite_idx = 0
        self.y_float = y
        self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_float -= 10

    def tick(self, frame):

        super().tick(frame=frame)

        if frame % 100 == 0:
            self.jump()

        if frame % 400 == 0:
            self.set_velocity(1, 0)

        if frame % 400 == 200:
            self.stop()

        if self.is_jumping:
            self.y_float += GRAVITY

        if self.y_float > self.y_base:
            self.y_float = self.y_base
            self.is_jumping = False

        if frame % 3 == 0:
            self.sprite_idx += 1
            if self.sprite_idx > 2:
                self.sprite_idx = 0

        self[0] = (
            SPRITE_MARIO_WALK1 + self.sprite_idx
            if self.x_velocity > 0
            else SPRITE_MARIO_JUMP
            if self.is_jumping
            else SPRITE_MARIO_STILL
        )
        self.y = int(self.y_float)

        if self.x > 64:
            self.x = 0


class BrickSprite(BaseSprite):
    def __init__(self, bitmap, palette, x, y, width=1, height=1):
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
    def __init__(self, bitmap, palette, x, y, width=1, height=1):
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
            if x > self.x_base + self.range:
                x = self.x_base + self.range
            if x < self.x_base - self.range:
                x = self.x_base - self.range
            self.x = x
