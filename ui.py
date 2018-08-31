from kivy.clock import Clock
from kivy.uix.button import Button

class IntroLabel(Button):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
    
        Clock.schedule_once(self.adjust_size, 0)
        
    def adjust_size(self, dt):
        while True:
            w, h = self.size
            tw, th = self.texture_size

            if tw >= w or th >= h:
                break
            self.font_size += 0.1
            self.texture_update()
            



