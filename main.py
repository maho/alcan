from functools import partial
from math import radians
import random

from cymunk import Body, Circle, PivotJoint, Segment, Space, Vec2d
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

import defs

class PhysicsObject(object):
    """ super object, which holds physics in class attributes """

    space = None
    bodyobjects = {}
    
    mass = NumericProperty(10, allownone=True)
    momentum = NumericProperty('INF', allownone=True)



    def __init__(self):
        if self.space is None:
            self.init_physics()

    @staticmethod
    def init_physics():
        """ instead of using space as global variable """
        cls = PhysicsObject
        cls.space = Space()
        cls.space.iterations = 60
        cls.space.gravity = defs.gravity

        radius = 100

        cls.floor = Segment(cls.space.static_body, Vec2d(-1000, defs.floor_level - radius), Vec2d(5000, defs.floor_level - radius), radius)
        cls.floor.elasticity = 0.6
        cls.floor.friction = 0.4
        cls.space.add_static(cls.floor)

    @classmethod
    def update_space(cls):
        cls.space.step(1.0/20.0)

        for b, o in cls.bodyobjects.items():
            o.update_to_body()

    def add_to_space(self, body, space):
        space = self.space

        if self.mass is not None:
            space.add(self.body)

        space.add(self.shape)

        self.bodyobjects[self.body] = self

    def update_to_body(self):
        p = self.body.position
        self.center = tuple(p)

#        if self.center_y < defs.kill_level:
#            self.out_of_bounds()
#
#    def out_of_bounds(self):
#        del(self.bodyobjects[self.body])
#        self.space.remove(self.body)
#        self.space.remove(self.shape)
#        self.parent.remove_widget(self)

        



class AnimObject(Widget, PhysicsObject):

    collision_type = NumericProperty(0)
    layers = None

    def __init__(self, *args, **kwargs):
        super(AnimObject, self).__init__(*args, **kwargs)

        self.add_body()

    def add_body(self, dt=None):

        if not self.parent: #object not initialized yet
            #call myself in next frame, 
            Clock.schedule_once(self.add_body)
            return

        if self.mass is None:
            self.momentum is None

        self.body = Body(self.mass, self.momentum)
        self.body.position = self.center

        self.shape = self.create_shape()



        self.add_to_space(self.body, self.shape)

    def create_shape(self):
        sx, sy = self.size
        radius = (sx + sy)/4 #half of avg
        shape = Circle(self.body, radius)
        shape.elasticity = 0.6
        shape.friction = 0.4
        shape.collision_type = self.collision_type
        if self.layers:
            shape.layers = self.layers

        return shape


class Element(AnimObject):
    collision_type = 1
    layers = defs.NORMAL_LAYER

    def __init__(self, elname, *a, mass=50, momentum=10, **kw):
        super(Element, self).__init__(*a, **kw)
        self.elname = elname
        self.imgsrc = "img/" + elname + ".png"

    def unjoint(self):
        """ remove existing joint """
        if not self.joint:
            return
        joint = self.joint
        self.joint = None
        self.space.remove(joint)
        del(joint)

class Cannon(AnimObject):
    collision_type = 2
    angle = NumericProperty(0)
    offset = ObjectProperty((0,0))
    layers = defs.CARRIED_THINGS_LAYER

    def __init__(self, *args, **kwargs):
        super(Cannon, self).__init__(*args, **kwargs)

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




class Wizard(AnimObject):

    collision_type = 3
    layers = defs.NORMAL_LAYER

    def __init__(self, *a, **kw):
        super(Wizard, self).__init__(*a, mass=defs.wizard_mass, **kw)
        self.down_pos = None

    def carry_element(self, element, dt=None):
        #move element to "carried elements layer"
        element.shape.layers = defs.CARRIED_THINGS_LAYER

        #bind it to wizard
        ##move element up
        pivot = self.body.position + Vec2d(defs.wizard_hand)
        element.body.position = pivot
        element.joint = PivotJoint(self.body, element.body, pivot)
        self.space.add(element.joint)



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
        super(AlcanGame, self).__init__(*args, **kwargs)

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_up=self.on_key_up)

        Clock.schedule_interval(self.update, 1.0/20.0)

        #collision handlers
        self.space.add_collision_handler(Wizard.collision_type, Element.collision_type, self.wizard_vs_element)
        self.space.add_collision_handler(Element.collision_type, Cannon.collision_type, self.cannon_vs_element)


    def wizard_vs_element(self, space, arbiter):
        wizard, element = [ self.bodyobjects[s.body] for s in arbiter.shapes ]

        if isinstance(wizard, Element):
            wizard, element = element, wizard

        Clock.schedule_once(partial(wizard.carry_element, element))

    def cannon_vs_element(self, space, arbiter):
        cannon, element = [ self.bodyobjects[s.body] for s in arbiter.shapes ]

        if isinstance(cannon, Element):
            cannon, element = element, cannon

        Clock.schedule_once(partial(cannon.carry_element, element))




    def on_key_up(self, window, key, *largs):
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

        if random.random() < defs.drop_chance:
            self.drop_element()

    def drop_element(self):
        """ drop element from heaven """
        
        w, h = self.size
        protl, protr = defs.protected_area
        protw = protr - protl

        #get proper x coordinate
        x = random.randint(0, w) - protw*2
        if x > protl:
            x += protw
        if x > w - protr:
            x += protw

        element = Element('water', center=(x, h))
        self.add_widget(element)

    



class AlcanApp(App):
    def build(self):
        return AlcanGame()


if __name__ == '__main__':
    AlcanApp().run()
