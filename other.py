from anim import AnimObject, ClockStopper
import defs


class Hint(ClockStopper):
    pass

class GameOver(AnimObject):
    def __init__(self, *a, **kw):
        super(GameOver, self).__init__(*a, **kw)
        self.layers = -1 - defs.CARRIED_THINGS_LAYER
