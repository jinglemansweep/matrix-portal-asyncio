import gc

gc.collect()

print("Boot > Init: Mem={}".format(gc.mem_free()))

import displayio

displayio.release_displays()

from app import Manager
from app.themes.mario_random import MarioRandomTheme
from app.themes.mario_running import MarioRunningTheme
from app.themes.simple import SimpleTheme

manager = Manager(themes=[MarioRandomTheme, MarioRunningTheme, SimpleTheme])
gc.collect()

manager.run()
