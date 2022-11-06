import adafruit_display_text.label
import adafruit_imageload
from cedargrove_palettefader.palettefader import PaletteFader
from displayio import Group, TileGrid

SPRITESHEET_FILE = "/app/themes/mario.bmp"

PALETTE_GAMMA = 1.0
PALETTE_BRIGHTNESS = 0.1
PALETTE_NORMALIZE = True

SPRITE_MARIO_STILL = 0
SPRITE_MARIO_JUMP = 4
SPRITE_MARIO_WALK1 = 5
SPRITE_MARIO_WALK2 = 6
SPRITE_MARIO_WALK3 = 7


class MarioTheme:
    def __init__(self, display):
        self.display = display
        self.bitmap, self.palette = adafruit_imageload.load(SPRITESHEET_FILE)
        self.frame = 0

    async def init(self):
        self.mario1 = MarioSprite(bitmap=self.bitmap, palette=self.palette, x=0)
        self.mario2 = MarioSprite(bitmap=self.bitmap, palette=self.palette, x=16)
        self.mario3 = MarioSprite(bitmap=self.bitmap, palette=self.palette, x=32)
        self.mario4 = MarioSprite(bitmap=self.bitmap, palette=self.palette, x=48)
        self.group = Group()
        self.group.append(self.mario1)
        self.group.append(self.mario2)
        self.group.append(self.mario3)
        self.group.append(self.mario4)
        self.display.show(self.group)
        self.mario1.is_walking = True
        self.mario3.is_walking = True

    async def loop(self):
        self.mario1.tick(self.frame)
        self.mario2.tick(self.frame)
        self.mario3.tick(self.frame)
        self.mario4.tick(self.frame)
        self.mario2.y = int(self.frame % 32)
        self.frame += 1


class MarioSprite(TileGrid):
    def __init__(self, bitmap, palette, x=0, y=0):
        palette.make_transparent(255)
        palette_adj = PaletteFader(
            palette, PALETTE_BRIGHTNESS, PALETTE_GAMMA, PALETTE_NORMALIZE
        )
        super().__init__(
            bitmap=bitmap,
            pixel_shader=palette_adj.palette,
            x=x,
            y=y,
            width=1,
            height=1,
            tile_width=16,
            tile_height=16,
            default_tile=SPRITE_MARIO_STILL,
        )
        self.is_walking = False
        self.sprite_idx = 0

    def tick(self, frame):
        print(frame)
        if frame % 3 == 0:
            self.sprite_idx += 1
            if self.sprite_idx > 2:
                self.sprite_idx = 0
        self[0] = (
            SPRITE_MARIO_WALK1 + self.sprite_idx
            if self.is_walking
            else SPRITE_MARIO_STILL
        )
