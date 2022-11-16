import random

from app.themes._base import BaseSprite
from app.utils import copy_update_palette

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
