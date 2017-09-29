from anim import AnimObject
import defs


class GameOver(AnimObject):
    def __init__(self, *a, **kw):
        super(GameOver, self).__init__(*a, **kw)
        self.layers = -1 - defs.CARRIED_THINGS_LAYER
