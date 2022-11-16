import gc

from adafruit_display_text.label import Label


from app.themes._base import BaseTheme


class GradiusTheme(BaseTheme):
    __theme_name__ = "gradius"

    def __init__(self, display, bitmap, palette, font, debug=False):
        super().__init__(display, bitmap, palette, font, debug)

    async def setup(self):
        super().setup()
        self.actors["label_test"] = TestLabel(10, 10, font=self.font)
        self.group.append(self.actors["label_test"])

    async def teardown(self):
        super().teardown()

    async def tick(self, frame):
        await super().tick(frame)

    async def on_button(self, button):
        await super().on_button(button)


class TestLabel(Label):
    def __init__(self, x, y, font, color=0x111111):
        super().__init__(text="GRADIUS", font=font, color=color)
        self.x = x
        self.y = y
