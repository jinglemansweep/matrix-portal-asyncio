from displayio import TileGrid


class BaseSprite(TileGrid):
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
        self.x_orig = x  # original sprite X coords
        self.y_orig = y  # original sprite y coords
        self.x_velocity = 0  # current sprite x velocity
        self.y_velocity = 0  # current sprite y velocity

    def set_velocity(self, x_velocity=0, y_velocity=0):
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity

    def stop(self):
        self.set_velocity(0, 0)

    def tick(self, frame):
        self.x += self.x_velocity
        self.y += self.y_velocity
