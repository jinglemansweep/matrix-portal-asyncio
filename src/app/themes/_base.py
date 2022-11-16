import random
from displayio import TileGrid


class BaseTheme:
    def __init__(self, display, bitmap, palette, font, debug=False):
        self.display = display
        self.bitmap = bitmap
        self.palette = palette
        self.font = font
        self.debug = debug
        self.frame = 0

    async def setup(self):
        pass

    async def loop(self):
        self.frame += 1

    async def on_button(self, button):
        print('Button > Press: {}'.format(button))


class BaseSprite(TileGrid):
    _name = "sprite"

    def __init__(self, bitmap, palette, x, y, width=1, height=1, default_tile=0):
        super().__init__(
            bitmap=bitmap,
            pixel_shader=palette,
            x=x,
            y=y,
            width=width,
            height=height,
            default_tile=default_tile,
            tile_width=16,
            tile_height=16,
        )
        self.reseed()
        self.x_orig = x  # original sprite X coords
        self.y_orig = y  # original sprite y coords
        self.x_velocity = 0  # current sprite x velocity
        self.y_velocity = 0  # current sprite y velocity
        self.x_dest = None  # current destination x coord to move to on tick
        self.y_dest = None  # current destination y coord to move to on tick
        self.x_dir_last = 0  # last movement x direction
        self.y_dir_last = 0  # last movement y direction

    def move_to(self, x=None, y=None):
        # print(f"{self._name} move_to: x={x} y={y}")
        if x is not None:
            self.x_dest = x
        if y is not None:
            self.y_dest = y

    def set_velocity(self, x_velocity=0, y_velocity=0):
        if x_velocity is not None:
            self.x_velocity = x_velocity
        if y_velocity is not None:
            self.y_velocity = y_velocity

    def stop(self):
        self.set_velocity(0, 0)
        self.x_dest = None
        self.y_dest = None

    def reseed(self):
        self.seed = random.randint(0, 1000)

    def update_move_velocities(self):
        # print(f"self: {self}, x: {self.x}, x_dest: {self.x_dest}")
        if self.x_dest is not None and self.x_dest != self.x:
            self.x_velocity = self.x_dir_last = 1 if self.x_dest > self.x else -1
        else:
            self.x_velocity = 0
            self.x_dest = None
        if self.y_dest is not None and self.y_dest != self.y:
            self.y_velolicty = self.y_dir_last = 1 if self.y_dest > self.y else -1
        else:
            self.y_velocity = 0
            self.y_dest = None

    def tick(self, frame):
        self.update_move_velocities()
        self.reseed()
        self.x += self.x_velocity
        self.y += self.y_velocity
