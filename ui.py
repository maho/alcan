from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.button import Button

def opposite(x, y):
    return x < 0 and y > 0 or x > 0 and y < 0

class IntroLabel(Button):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
    
    def on_size(self, label, size):
        Clock.schedule_once(self.adjust_size, 0)
        
    def adjust_size(self, dt):

        step = 3

        while True:
            w, h = self.size
            tw, th = self.texture_size
            
            Logger.debug("tw=%s w=%s th=%s h=%s step=%s", tw, w, th, h, step)
           
            dir_dfs = -1 if (tw > w or th > h) else 1

            if opposite(dir_dfs, step):
                step *= -0.5
                Logger.debug("step set to %s", step)

            if abs(step) < 0.1:
                Logger.debug("reached finish")
                break

            self.font_size += step
            Logger.debug("font_size=%s", self.font_size)
            self.texture_update()
            



