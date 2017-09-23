from cymunk import Body, Circle, Segment, Space, Vec2d
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window
from kivy.uix.widget import Widget

import defs

class PhysicsObject(object):
    """ super object, which holds physics in class attributes """

    space = None
    bodyobject = []


    def __init__(self):
        if self.space is None:
            self.init_physics()

    @staticmethod
    def init_physics():
        """ instead of using space as global variable """
        cls = PhysicsObject
        cls.space = Space()
        cls.space.iterations = 20
        cls.space.gravity = defs.gravity

        cls.floor = Segment(cls.space.static_body, Vec2d(-1000, defs.floor_level), Vec2d(5000, defs.floor_level), 0)
        cls.floor.elasticity = 0.6
        cls.floor.friction = 0.4
        cls.space.add_static(cls.floor)

    @classmethod
    def update_space(cls):
        cls.space.step(1.0/20.0)

        for b in cls.bodyobject:
            b.update_to_body()

    def add_to_space(self, body, space):
        space = self.space
        space.add(self.body, self.shape)
        self.bodyobject.append(self)

    def update_to_body(self):
        p = self.body.position
        self.center = tuple(p)


class AnimObject(Widget, PhysicsObject):
    def __init__(self, *args, **kwargs):
        super(AnimObject, self).__init__(*args, **kwargs)
       
        self.body = Body(defs.wizard_mass, 'INF')
        self.body.position = self.center

        sx, sy = self.size
        radius = (sx + sy)/4 #half of avg

        self.shape = Circle(self.body, radius)
        self.shape.elasticity = 0.6
        self.shape.friction = 0.4

        self.add_to_space(self.body, self.shape)



class Wizard(AnimObject):

    def __init__(self, *a, **kw):
        super(Wizard, self).__init__(*a, **kw)
        self.down_pos = None

    def on_touch_up(self, touch):
        px, py = touch.pos
        opx, opy = self.center
        
        dx, dy = px - opx, py - opy

        if abs(dx) < defs.minswipe and abs(dy) < defs.minswipe:
            return

        if abs(dx) > 2*abs(dy):
            if dx > 0:
                self.move_right()
            else:
                self.move_left()
        

    def on_touch_down(self, touch):
        self.down_pos = touch.pos

    
    def move_right(self):
        print("right")
        self.body.apply_impulse(defs.wizard_impulse)

    def move_left(self):
        print ("left")
        ix, iy = defs.wizard_impulse

        self.body.apply_impulse((ix*-1, iy))

class AlcanGame(Widget, PhysicsObject):
    def __init__(self, *args, **kwargs):
        super(AlcanGame, self).__init__(*args, **kwargs)

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_up=self.on_key_up)

        Clock.schedule_interval(self.update, 1.0/20.0)

        self.wizard = Wizard(center=(200,200))
        self.add_widget(self.wizard)

    def on_key_up(self, window, key, *largs):
        #code = self._keyboard.keycode_to_string(key)
        kid, code = key

        if code == 'left':
            self.wizard.move_left()
    
        if code == 'right':
            self.wizard.move_right()

    def update(self, dt):
        self.update_space()



class AlcanApp(App):
    def build(self):
        return AlcanGame()


if __name__ == '__main__':
    AlcanApp().run()
