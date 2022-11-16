import gc
gc.collect()

print("Boot > Init: Mem={}".format(gc.mem_free()))

import displayio
displayio.release_displays()

from app import Manager
from app.themes.mario import MarioTheme

manager = Manager(theme=MarioTheme)
gc.collect()

manager.run()