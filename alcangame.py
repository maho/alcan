from functools import partial
import random

from kivy.app import App
from kivy.core.window import Keyboard, Window
from kivy.logger import Logger
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.button import Button

from anim import AnimObject, ClockStopper, PhysicsObject
from baloon import Baloon
from cannon import Cannon
import defs
from element import Element, load_elmap
from wizard import Wizard
from other import GameOver, Hint
from utils import adhoco


class AlcanGame(ClockStopper, PhysicsObject):

    bfs = NumericProperty('inf')
    scale = NumericProperty(1.0)
    stacklayout = ObjectProperty()

    def __init__(self, *args, **kwargs):

        Window.size = defs.map_size

        super(AlcanGame, self).__init__(*args, **kwargs)

        self.oo_to = adhoco(remove=set(), add=[])
        self.elements_in_zone = []
        self.keys_pressed = set()
        self.game_is_over = False
        self.visible_hints = set()

        from kivy.base import EventLoop
        EventLoop.window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        self.schedule_interval(self.update, 1.0/defs.fps)

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
        self.space.add_collision_handler(Element.collision_type,
                                         defs.BOTTOM_BOUND,
                                         self.element_vs_bottom)
        self.space.add_collision_handler(Wizard.collision_type,
                                         defs.BOTTOM_BOUND,
                                         self.wizard_vs_bottom)

        Window.bind(on_resize=self.on_resize)
        self.bfs = Element.steps_to_reach()

    def clear(self):
        self.stop_all_clocks()
        for x in self.children[:]:
            if isinstance(x, AnimObject):
                self.remove_widget(x)
        self.del_physics()

    def gameover(self):
        if self.game_is_over:
            return
        self.game_is_over = True
        __mw, mh = defs.map_size
        self.add_widget(GameOver(pos=(400, mh), size=(600, 150)))
        App.get_running_app().sm.schedule_gameover()

    def on_init(self):
        self.add_widget(Baloon(center=(300, 300), object_to_follow=self.wizard,
                               text="Alchemist"))
        self.schedule_once(lambda dt: self.add_widget(Baloon(center=(400, 300), size=(200, 50),
                                                      object_to_follow=self.cannon,
                                                      text="Large Elements Collider")),
                           3)

    def schedule_add_widget(self, oclass, *oargs, **okwargs):
        self.oo_to.add.append((oclass, oargs, okwargs))

    def set_hint(self, a, b, c):
        if (a, b) in self.visible_hints:
            return

        if len(self.visible_hints) >= defs.max_hints:
            return

        hint = Hint()
        self.stacklayout.add_widget(hint)
        self.visible_hints.add((a, b))
        hint.a = a
        hint.b = b
        hint.c = c

        def _fn(__dt):
            self.stacklayout.remove_widget(hint)
            self.visible_hints.remove((a, b))

        self.schedule_once(_fn, 6)

    def _calculate_hint(self):
        """ calculate hint for new element appeared """
        available_elements = set()
        for x in self.elements_in_zone:
            available_elements.add(x.elname)

        possible_combinations = []
        for (a, b), c in load_elmap().items():
            if a in available_elements and b in available_elements:
                possible_combinations.append((a, b, c))

        if possible_combinations:
            a, b, c = random.choice(possible_combinations)
            self.set_hint(a, b, c)

    def remove_obj(self, obj, __dt=None, just_schedule=True):
        if just_schedule:
            Logger.debug("game: schedule %s to be removed", obj)
            self.oo_to.remove.add(obj)
            return
        Logger.info("game: remove object obj=%s", obj)
        obj.before_removing()
        self.space.remove(obj.body)
        self.space.remove(obj.shape)
        self.remove_widget(obj)
        del self.bodyobjects[obj.body]

    def replace_obj(self, a, BClass, *Bargs, **Bkwargs):
        self.remove_obj(a)
        Bkwargs['center'] = a.center
        Bkwargs['size'] = a.size
        self.schedule_add_widget(BClass, *Bargs, **Bkwargs)

    def wizard_vs_element(self, __space, arbiter):
        """ collision handler - wizard vs element """
        wizard, element = [self.bodyobjects[s.body] for s in arbiter.shapes]

        if isinstance(wizard, Element):
            wizard, element = element, wizard

        if wizard.carried_elements:
            return True

        self.schedule_once(partial(wizard.carry_element, element))

    def cannon_vs_element(self, __space, arbiter):
        cannon, element = [self.bodyobjects[s.body] for s in arbiter.shapes]

        if isinstance(cannon, Element):
            cannon, element = element, cannon

        if cannon.bullets:
            return True  # cannot hold more than one bullet

        self.schedule_once(partial(cannon.carry_element, element))

    def element_vs_bottom(self, __space, arbiter):
        e, bo = arbiter.shapes
        if e.collision_type == defs.BOTTOM_BOUND:
            e, bo = bo, e

        e = self.bodyobjects[e.body]

        if e.activated:
            self.gameover()

        self.remove_obj(e)
        self.elements_in_zone.remove(e)

    def element_vs_element(self, __space, arbiter):
        e1, e2 = [self.bodyobjects[s.body] for s in arbiter.shapes]

        # Clock.schedule_once(partial(e1.collide_with_another,e2))
        return e1.collide_with_another(e2)

    def wizard_vs_bottom(self, __space, arbiter):
        wiz, bo = arbiter.shapes
        if wiz.collision_type == defs.BOTTOM_BOUND:
            wiz, bo = bo, wiz

        self.gameover()

    def on_key_up(self, __window, key, *__largs, **__kwargs):
        code = Keyboard.keycode_to_string(None, key)
        self.keys_pressed.remove(code)

    def on_key_down(self, __window, key, *__largs, **__kwargs):
        # very dirty hack, but: we don't have any instance of keyboard anywhere, and
        # keycode_to_string should be in fact classmethod, so passing None as self is safe
        code = Keyboard.keycode_to_string(None, key)
        self.keys_pressed.add(code)

        if code == 'spacebar':
            if not self.cannon.shoot():
                self.wizard.release_element()

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
            self.cannon.aim += dy/2

    def on_touch_down(self, touch):
        if touch.is_double_tap:
            if not self.wizard.release_element():
                self.cannon.shoot()

    def on_touch_up(self, touch):
        self.keys_pressed.clear()

    def on_resize(self, __win, w, h):
        mw, mh = defs.map_size
        xratio = w/mw
        yratio = h/mh

        self.scale = min(xratio, yratio)
        Logger.debug("self.scale = %s", self.scale)

    def update(self, dt):
        self.update_space()

        mi, ma = defs.num_elements_in_zone
        n = sum(int(not e.activated) for e in self.elements_in_zone)

        # Logger.debug("elements_in_zone: %s all %s active, %s unique",
        #             len(self.elements_in_zone), n,
        #             len(set(self.elements_in_zone)))

        if n < mi:
            Logger.debug("drop because num elements is below %s", mi)
            self.drop_element()

        if random.random() < defs.drop_chance and n < ma:
            self.drop_element()

        if random.random() < defs.hint_chance:
            self._calculate_hint()

        for o in self.children:
            if isinstance(o, AnimObject):
                o.update(dt)

        for o in self.oo_to.remove:
            self.remove_obj(o, just_schedule=False)
            Logger.debug("%s just removed", o)
            assert o not in self.children
        self.oo_to.remove.clear()

        for ocl, oa, okw in self.oo_to.add:
            newo = ocl(*oa, **okw)
            Logger.debug("newo %s created", newo)
            self.add_widget(newo)
        self.oo_to.add.clear()

        if 'up' in self.keys_pressed:
            self.cannon.aim += 1.5
        if 'down' in self.keys_pressed:
            self.cannon.aim -= 1.5

        dx = 0
        if 'left' in self.keys_pressed:
            dx -= 10
        if 'right' in self.keys_pressed:
            dx += 10
        if dx:
            self.wizard.body.apply_impulse((defs.wizard_touch_impulse_x * dx, 0))

    def drop_element(self):
        """ drop element from heaven """
        _w, h = self.size

        # get proper x coordinate
        x = random.randint(*defs.drop_zone)

        element = Element.random(elizo=self.elements_in_zone)
        element.center = (x, h)
        if not element:
            return
        self.add_widget(element)

    def reached_elname(self, elname):
        Logger.debug("reached_elname(%s)", elname)
        if elname == "dragon":
            Logger.debug("readed DRAGON!!!!!")
            wi = Button(pos=(200, 20), size=(300, 300))
            self.add_widget(wi)
