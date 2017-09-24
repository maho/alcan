from functools import partial
from math import radians
import random

from cymunk import Body, Circle, PivotJoint, Segment, Space, Vec2d
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window
from kivy.logger import Logger
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from anim import AnimObject, PhysicsObject
import defs
from element import Element



class Cannon(AnimObject):
    collision_type = 2
    angle = NumericProperty(0)
    offset = ObjectProperty((0,0))

    def __init__(self, *args, **kwargs):
        super(Cannon, self).__init__(*args, **kwargs)
        self.layers = defs.CARRIED_THINGS_LAYER

        self.bullets = []

    def create_shape(self):
        """ make cannon a sensor """
        shape = super(Cannon, self).create_shape()
        shape.sensor = True
        return shape

    def carry_element(self, element, dt=None):
        #unbind joint from element
        element.unjoint()
        
        #move it to center of cannon
        pivot = self.body.position + Vec2d(self.offset)
        element.body.position = pivot
        element.joint = PivotJoint(self.body, element.body, pivot)
        self.space.add(element.joint)

        self.bullets.append(element)

    def shoot(self):
        impulse = Vec2d(0, defs.shoot_force)
        impulse.rotate(radians(self.angle))
        for x in self.bullets:
            x.unjoint()
            x.body.apply_impulse(impulse)
            x.shape.layers = defs.NORMAL_LAYER
        self.bullets = []




class Wizard(AnimObject):

    collision_type = 3

    def __init__(self, *a, **kw):
        super(Wizard, self).__init__(*a, mass=defs.wizard_mass, **kw)
        self.down_pos = None
        self.layers = defs.NORMAL_LAYER

    def carry_element(self, element, dt=None):
        #move element to "carried elements layer"
        element.shape.layers = defs.CARRIED_THINGS_LAYER

        #bind it to wizard
        ##move element up
        pivot = self.body.position + Vec2d(defs.wizard_hand)
        element.body.position = pivot
        element.joint = PivotJoint(self.body, element.body, pivot)
        self.space.add(element.joint)
        self.parent.num_elements_in_zone -= 1

    def add_body(self, dt=None):
        super(Wizard, self).add_body(dt=dt)
        if self.body: #if obj is initialized ye
            self.body.velocity_limit = defs.wizard_max_speed

    def on_touch_up(self, touch):
        px, py = touch.pos
        opx, opy = self.center
        
        dx, dy = px - opx, py - opy

        if abs(dx) < defs.mintouchdist and abs(dy) < defs.mintouchdist:
            return

        if abs(dx) > 2*abs(dy):
            if dx > 0:
                self.move_right()
            else:
                self.move_left()
        

    def on_touch_down(self, touch):
        self.down_pos = touch.pos

    
    def move_right(self):
        self.body.apply_impulse(defs.wizard_impulse)

    def move_left(self):
        ix, iy = defs.wizard_impulse

        self.body.apply_impulse((ix*-1, iy))

class AlcanGame(Widget, PhysicsObject):
    def __init__(self, *args, **kwargs):
    
        Window.size = defs.map_size

        super(AlcanGame, self).__init__(*args, **kwargs)

        self.oo_to_remove = set()
        self.oo_to_add = []
        self.num_elements_in_zone = 0

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self.on_keyboard)

        Clock.schedule_interval(self.update, 1.0/defs.fps)

        #collision handlers
        self.space.add_collision_handler(Wizard.collision_type, Element.collision_type, self.wizard_vs_element)
        self.space.add_collision_handler(Element.collision_type, Cannon.collision_type, self.cannon_vs_element)
        self.space.add_collision_handler(Element.collision_type, Element.collision_type, self.element_vs_element)

    def schedule_add_widget(self, oclass, *oargs, **okwargs):
        self.oo_to_add.append((oclass, oargs, okwargs))

    def remove_obj(self, obj, dt=None, just_schedule=True):
        if just_schedule:
            Logger.debug("game: schedule %s to be removed", obj)
            self.oo_to_remove.add(obj)
            return
        Logger.info("game: remove object obj=%s", obj)
        self.space.remove(obj.body)
        self.space.remove(obj.shape)
        self.remove_widget(obj)
        del(self.bodyobjects[obj.body])

    def replace_obj(self, a, BClass, *Bargs, **Bkwargs):
        self.remove_obj(a)
        Bkwargs['center'] = a.center
        self.schedule_add_widget(BClass, *Bargs, **Bkwargs)


    def wizard_vs_element(self, space, arbiter):
        wizard, element = [self.bodyobjects[s.body] for s in arbiter.shapes]

        if isinstance(wizard, Element):
            wizard, element = element, wizard

        Clock.schedule_once(partial(wizard.carry_element, element))

    def cannon_vs_element(self, space, arbiter):
        cannon, element = [ self.bodyobjects[s.body] for s in arbiter.shapes ]

        if isinstance(cannon, Element):
            cannon, element = element, cannon

        Clock.schedule_once(partial(cannon.carry_element, element))

    def element_vs_element(self, space, arbiter):
        e1, e2 = [self.bodyobjects[s.body] for s in arbiter.shapes]

        Clock.schedule_once(partial(e1.collide_with_another,e2))


    def on_keyboard(self, window, key, *largs):
        #code = self._keyboard.keycode_to_string(key)
        kid, code = key

        if code == 'left':
            self.wizard.move_left()
        elif code == 'right':
            self.wizard.move_right()
        elif code == 'up':
            self.cannon.angle += 3
        elif code == 'down':
            self.cannon.angle -= 3
        elif code == 'spacebar':
            self.cannon.shoot()
        else:
            print("unknown code=",code)

    def update(self, dt):
        self.update_space()

        mi, ma = defs.num_elements_in_zone
        n = self.num_elements_in_zone
        if (random.random() < defs.drop_chance or n < mi) and n < ma:
            self.drop_element()

        for o in self.children:
            if isinstance(o, AnimObject):
                o.update(dt)

        for o in self.oo_to_remove:
            self.remove_obj(o, just_schedule=False)
            Logger.debug("%s just removed", o)
            assert o not in self.children
        self.oo_to_remove.clear()

        for ocl, oa, okw in self.oo_to_add:
            newo = ocl(*oa, **okw)
            Logger.debug("newo %s created", newo)
            self.add_widget(newo)
        self.oo_to_add.clear()

    def drop_element(self):
        """ drop element from heaven """
        w, h = self.size

        #get proper x coordinate
        x = random.randint(*defs.drop_zone)

        element = Element.random(center=(x, h))
        self.add_widget(element)
        self.num_elements_in_zone += 1



class AlcanApp(App):
    def build(self):
        return AlcanGame()


if __name__ == '__main__':
    AlcanApp().run()