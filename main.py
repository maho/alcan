from functools import partial
from math import radians
import os
import random
import time

from cymunk import PivotJoint, Vec2d
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window
from kivy.logger import Logger
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from anim import AnimObject, PhysicsObject
from baloon import Baloon
import defs
from element import Element


class Cannon(AnimObject):
    collision_type = 2
    angle = NumericProperty(0)
    offset = ObjectProperty((0, 0))

    def __init__(self, *args, **kwargs):
        super(Cannon, self).__init__(*args, **kwargs)
        self.layers = defs.CARRIED_THINGS_LAYER

        self.bullets = []

    def create_shape(self):
        """ make cannon a sensor """
        shape = super(Cannon, self).create_shape()
        shape.sensor = True
        return shape

    def carry_element(self, element, __dt=None):
        # unbind joint from element
        element.unjoint()

        # move it to center of cannon
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
            x.shape.layers = defs.SHOOTED_THINGS_LAYER
            x.activate()
        self.bullets = []


class Wizard(AnimObject):

    collision_type = 3

    def __init__(self, *a, **kw):
        super(Wizard, self).__init__(*a, mass=defs.wizard_mass, **kw)
        self.layers = defs.NORMAL_LAYER
        self.carried_elements = []
        self.applied_force = Vec2d(0, 0)

    def carry_element(self, element, __dt=None):
        if time.time() - element.released_at < 1.0:
            return True
        # move element to "carried elements layer"
        element.shape.layers = defs.CARRIED_THINGS_LAYER

        # bind it to wizard
        # #move element up
        pivot = self.body.position + Vec2d(defs.wizard_hand)
        element.body.position = pivot
        element.joint = PivotJoint(self.body, element.body, pivot)
        self.space.add(element.joint)
        self.parent.num_elements_in_zone -= 1

        self.carried_elements.append(element)
        element.wizard = self

    def add_body(self, dt=None):
        super(Wizard, self).add_body(dt=dt)
        if self.body:  # if obj is initialized ye
            self.body.velocity_limit = defs.wizard_max_speed

    def create_shape(self):
        shape = super(Wizard, self).create_shape()
        shape.friction = defs.wizard_friction
        return shape

    def release_element(self):
        if not self.carried_elements:
            return False
        for x in self.carried_elements[:]:
            x.body.apply_impulse(defs.wizard_release_impulse)
            x.unjoint()
            x.shape.layers = defs.NORMAL_LAYER
            x.released_at = time.time()

        return True


class AlcanGame(Widget, PhysicsObject):

    bfs = NumericProperty('inf')

    def __init__(self, *args, **kwargs):

        Window.size = defs.map_size

        super(AlcanGame, self).__init__(*args, **kwargs)

        self.oo_to_remove = set()
        self.oo_to_add = []
        self.num_elements_in_zone = 0
        self.keys_pressed = set()

        from kivy.base import EventLoop
        EventLoop.window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        Clock.schedule_interval(self.update, 1.0/defs.fps)

        # collision handlers
        self.space.add_collision_handler(Wizard.collision_type,
                                         Element.collision_type,
                                         self.wizard_vs_element)
        self.space.add_collision_handler(Element.collision_type,
                                         Cannon.collision_type,
                                         self.cannon_vs_element)
        self.space.add_collision_handler(Element.collision_type,
                                         Element.collision_type,
                                         self.element_vs_element)

        Window.bind(on_resize=self.on_resize)

        self.add_widget(Baloon(center=(300, 300), object_to_follow=self.wizard,
                               text="Alchemist"))
        Clock.schedule_once(lambda dt: self.add_widget(Baloon(center=(400, 300), size=(200, 50),
                                                       object_to_follow=self.cannon,
                                                       text="Large Elements Collider")),
                            3)

        self.bfs = Element.steps_to_reach()

    def schedule_add_widget(self, oclass, *oargs, **okwargs):
        self.oo_to_add.append((oclass, oargs, okwargs))

    def remove_obj(self, obj, __dt=None, just_schedule=True):
        if just_schedule:
            Logger.debug("game: schedule %s to be removed", obj)
            self.oo_to_remove.add(obj)
            return
        Logger.info("game: remove object obj=%s", obj)
        obj.before_removing()
        self.space.remove(obj.body)
        self.space.remove(obj.shape)
        self.remove_widget(obj)
        del(self.bodyobjects[obj.body])

    def replace_obj(self, a, BClass, *Bargs, **Bkwargs):
        self.remove_obj(a)
        Bkwargs['center'] = a.center
        self.schedule_add_widget(BClass, *Bargs, **Bkwargs)

    def wizard_vs_element(self, __space, arbiter):
        """ collision handler - wizard vs element """
        wizard, element = [self.bodyobjects[s.body] for s in arbiter.shapes]

        if isinstance(wizard, Element):
            wizard, element = element, wizard

        if wizard.carried_elements:
            return True

        Clock.schedule_once(partial(wizard.carry_element, element))

    def cannon_vs_element(self, space, arbiter):
        cannon, element = [self.bodyobjects[s.body] for s in arbiter.shapes]

        if isinstance(cannon, Element):
            cannon, element = element, cannon

        if cannon.bullets:
            return True  # cannot hold more than one bullet

        return Clock.schedule_once(partial(cannon.carry_element, element))

    def element_vs_element(self, space, arbiter):
        e1, e2 = [self.bodyobjects[s.body] for s in arbiter.shapes]

        # Clock.schedule_once(partial(e1.collide_with_another,e2))
        return e1.collide_with_another(e2)

    def on_key_up(self, window, key, *largs, **kwargs):
        code = Keyboard.keycode_to_string(None, key)
        self.keys_pressed.remove(code)

    def on_key_down(self, window, key, *largs, **kwargs):
        # very dirty hack, but: we don't have any instance of keyboard anywhere, and
        # keycode_to_string should be in fact classmethod, so passing None as self is safe
        code = Keyboard.keycode_to_string(None, key)
        self.keys_pressed.add(code)

        if code == 'spacebar':
            if not self.wizard.release_element():
                self.cannon.shoot()

    def on_touch_move(self, touch):
        if touch.is_double_tap:
            return

        dx, dy = touch.dx, touch.dy
        ix = defs.wizard_touch_impulse_x
        if abs(dx) > abs(dy):
            Logger.debug("horizontal")
            self.wizard.body.apply_impulse((ix * dx, 0))

        if abs(dy) > abs(dx):
            Logger.debug("vertical")
            self.cannon.angle += dy/2

    def on_touch_down(self, touch):
        if touch.is_double_tap:
            if not self.wizard.release_element():
                self.cannon.shoot()

    def on_touch_up(self, touch):
        self.keys_pressed.clear()
        self.wizard.stop_move()

    def on_resize(self, win, w, h):
        mw, mh = defs.map_size
        xratio = w/mw
        yratio = h/mh

        self.scale = min(xratio, yratio)

    def update(self, dt):
        self.update_space()

        mi, ma = defs.num_elements_in_zone
        n = self.num_elements_in_zone
        if n < mi:
            Logger.debug("drop because num elements is below %s", mi)
            self.drop_element()

        if random.random() < defs.drop_chance and n < ma:
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

        if 'up' in self.keys_pressed:
            self.cannon.angle += 1.5
        if 'down' in self.keys_pressed:
            self.cannon.angle -= 1.5

        dx = 0
        if 'left' in self.keys_pressed:
            dx -= 10
        if 'right' in self.keys_pressed:
            dx += 10
        if dx:
            self.wizard.body.apply_impulse((defs.wizard_touch_impulse_x * dx, 0))

    def drop_element(self):
        """ drop element from heaven """
        w, h = self.size

        # get proper x coordinate
        x = random.randint(*defs.drop_zone)

        element = Element.random(center=(x, h))
        if not element:
            return
        self.add_widget(element)
        self.num_elements_in_zone += 1


class AlcanApp(App):
    def build(self):
        return AlcanGame()


if __name__ == '__main__':

    if "DEBUG" in os.environ:
        def debug_signal_handler(signal, frame):
            import pudb
            pudb.set_trace()

        import signal
        signal.signal(signal.SIGINT, debug_signal_handler)

    AlcanApp().run()
