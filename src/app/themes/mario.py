import adafruit_imageload
from cedargrove_palettefader.palettefader import PaletteFader
from displayio import Group
from app.themes._base import BaseSprite

SPRITESHEET_FILE = "/app/themes/mario.bmp"

PALETTE_GAMMA = 1.0
PALETTE_BRIGHTNESS = 0.1
PALETTE_NORMALIZE = True

GRAVITY = 0.75

SPRITE_BRICK = 1
SPRITE_ROCK = 2
SPRITE_MARIO_STILL = 0
SPRITE_MARIO_JUMP = 4
SPRITE_MARIO_WALK1 = 5
SPRITE_MARIO_WALK2 = 6
SPRITE_MARIO_WALK3 = 7


class MarioTheme:
    def __init__(self, display):
        # Display & Resources
        self.display = display
        self.bitmap, bitmap_palette = adafruit_imageload.load(SPRITESHEET_FILE)
        bitmap_palette.make_transparent(255)
        self.palette = PaletteFader(
            bitmap_palette, PALETTE_BRIGHTNESS, PALETTE_GAMMA, PALETTE_NORMALIZE
        )
        # Primitives
        root = Group()
        group_actors = Group()
        self.mario = MarioSprite(
            bitmap=self.bitmap, palette=self.palette.palette, x=0, y=8
        )
        group_actors.append(self.mario)
        root.append(group_actors)
        group_floor = Group()
        self.floor_brick = BrickSprite(
            bitmap=self.bitmap, palette=self.palette, x=0, y=24, width=4
        )
        group_floor.append(self.floor_brick)
        root.append(group_floor)
        # Properties
        self.frame = 0
        # Render Display
        self.display.show(root)

    async def loop(self):
        self.mario.tick(self.frame)
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
            palette=palette.palette,
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
            palette=palette.palette,
            x=x,
            y=y,
            width=width,
            height=height,
            default_tile=SPRITE_ROCK,
        )
