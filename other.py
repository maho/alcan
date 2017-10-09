from kivy.uix.boxlayout import BoxLayout

from anim import AnimObject
import defs


class Hint(BoxLayout):
    pass
    # def __init__(self):
    #     super(Hint, self).__init__()


class GameOver(AnimObject):
    def __init__(self, *a, **kw):
        super(GameOver, self).__init__(*a, **kw)
        self.layers = -1 - defs.CARRIED_THINGS_LAYER
