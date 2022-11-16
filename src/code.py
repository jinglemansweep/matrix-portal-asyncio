import gc

gc.collect()

print("Boot > Init: Mem={}".format(gc.mem_free()))

import displayio

displayio.release_displays()

from app import Manager
from app.themes.gradius import GradiusTheme
from app.themes.mario import MarioTheme

manager = Manager(themes=[MarioTheme, GradiusTheme])
gc.collect()

manager.run()
