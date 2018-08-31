from functools import partial
from collections import OrderedDict, defaultdict
import random

from cymunk import Vec2d
from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window
from kivy.logger import Logger
from kivy.properties import NumericProperty, ObjectProperty

from anim import AnimObject, ClockStopper, PhysicsObject
from baloon import Baloon, PointsBaloon
from cannon import Cannon
import defs
from element import Element, load_elmap
from ui import IntroLabel
from wizard import Wizard
from other import GameOver, Hint, Success
from utils import adhoco


class AlcanGame(ClockStopper, PhysicsObject):

    bfs = NumericProperty('inf')
    scale = NumericProperty(1.0)
    points = NumericProperty(0)
    stacklayout = ObjectProperty()

    def __init__(self, *args, **kwargs):

        super(AlcanGame, self).__init__(*args, **kwargs)

        self.oo_to = adhoco(remove=set(), add=[])
        self.elements_in_zone = []
        self.keys_pressed = set()
        self.game_is_over = False
        self.visible_hints = OrderedDict()
        self.hints_stats = defaultdict(lambda: 0)
        self.skip_drop = False

        EventLoop.window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        self.schedule_interval(self.update, 1.0 / defs.fps)

        # collision handlers
        self.space.add_collision_handler(Wizard.collision_type,
                                         Element.collision_type,
                                         self.wizard_vs_element,
                                         separate=self.wizard_vs_element_end)
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
        self.set_bfs()
        self.trigger_resize()

    def clear(self):
        self.stop_all_clocks()
        EventLoop.window.funbind('on_key_down', self.on_key_down)
        EventLoop.window.funbind('on_key_up', self.on_key_up)
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
                                                      text="Large Elements Collider")), 3)

    def schedule_add_widget(self, oclass, *oargs, **okwargs):
        self.oo_to.add.append((oclass, oargs, okwargs))

    def set_bfs(self):
        self.hints_to_show = Element.steps_to_reach()
        self.bfs = len(self.hints_to_show)

    def set_hint(self, a, b, c):
        if (a, b) in self.visible_hints:
            return False


        hint = Hint()
        self.stacklayout.add_widget(hint)
        self.visible_hints[a, b] = hint
        self.hints_stats[a, b] += 1
        hint.a = a
        hint.b = b
        hint.c = c
        
        if len(self.visible_hints) > defs.max_hints:
            (a, b), hint = self.visible_hints.popitem(0)
            self.stacklayout.remove_widget(hint)

        return True



    def rotate_hint(self):
        """ calculate hint for new element appeared """
        available_elements = Element.available_elnames

        possible_combinations = []
        elmap = load_elmap()
        for (a, b) in self.hints_to_show:
            c = elmap[a, b]
            possible_combinations.append((a, b, c))

        possible_combinations.sort(key=lambda x: self.hints_stats[x[0], x[1]])

        for a, b, c in possible_combinations:
            if self.set_hint(a, b, c):
                break

    def remove_obj(self, obj, __dt=None, just_schedule=True):
        if just_schedule:
            self.oo_to.remove.add(obj)
            return
        Logger.info("game: remove object obj=%s", obj)
        obj.before_removing()
        self.space.remove(obj.body)
        self.space.remove(obj.shape)
        self.remove_widget(obj)
        del self.bodyobjects[obj.body]

    def replace_objs(self, As, BClass, *Bargs, **Bkwargs):
        massum = 0.0
        momentum = Vec2d(0, 0)
        for x in As:
            massum += x.body.mass
            momentum += x.body.velocity * x.body.mass
            Logger.debug("momentum is %s after adding mass=%s vel=%s", momentum, x.body.velocity, x.body.mass)
            self.remove_obj(x)
        Bkwargs['pos'] = As[0].pos
        Bkwargs['size'] = As[0].size
        Bkwargs['momentum'] = momentum / len(As)  # I have no idea why I should divide it by number of As. 
        #  Afair it should work well without dividing, 

        self.schedule_add_widget(BClass, *Bargs, **Bkwargs)

    def wizard_vs_element(self, __space, arbiter):
        """ collision handler - wizard vs element """
        wizard, element = [self.bodyobjects[s.body] for s in arbiter.shapes]

        if isinstance(wizard, Element):
            wizard, element = element, wizard

        wizard.touching_elements.append(element)

        if wizard.carried_elements:
            return True

        self.schedule_once(partial(wizard.carry_element, element))

    def wizard_vs_element_end(self, __space, arbiter):
        wizard, element = [self.bodyobjects[s.body] for s in arbiter.shapes]

        if isinstance(wizard, Element):
            wizard, element = element, wizard

        wizard.touching_elements.remove(element)

        if not wizard.carried_elements and wizard.touching_elements:
            self.schedule_once(partial(wizard.carry_element, wizard.touching_elements[0]))

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
        retpoints = e1.collide_with_another(e2)

        if retpoints:
            x, y = e1.center

            self.add_widget(PointsBaloon((x, y + 30), retpoints))

            self.points += retpoints

        return True

    def wizard_vs_bottom(self, __space, arbiter):
        wiz, bo = arbiter.shapes
        if wiz.collision_type == defs.BOTTOM_BOUND:
            wiz, bo = bo, wiz

        self.gameover()

    def on_key_up(self, __window, key, *__largs, **__kwargs):
        code = Keyboard.keycode_to_string(None, key)
        self.keys_pressed.remove(code)

    def drop_carried_element(self):
        self.wizard.release_element()

    def shoot(self, drop=False):
        if self.cannon.shoot():
            self.skip_drop = True
            Clock.schedule_once(lambda dt: setattr(self, 'skip_drop', False), defs.skip_drop_time)
        elif drop:
            self.wizard.release_element()


    def on_key_down(self, window, key, *largs, **kwargs):
        # very dirty hack, but: we don't have any instance of keyboard anywhere, and
        # keycode_to_string should be in fact classmethod, so passing None as self is safe
        code = Keyboard.keycode_to_string(None, key)
        self.keys_pressed.add(code)

        if code == 'spacebar':
            self.shoot(drop=True)

    def on_touch_down(self, touch):
        touch.push()
        touch.apply_transform_2d(lambda x,y: (x/self.scale, y/self.scale))  # quick and dirty, roughly like in Scatter but way simplier

        try:
            if super().on_touch_down(touch):
                return True
        finally:
            touch.pop()


    def on_touch_move(self, touch):
        if touch.is_double_tap:
            return False

        dx, dy = touch.dx, touch.dy
        ix = defs.wizard_touch_impulse_x
        if abs(dx) > abs(dy):
            self.wizard.body.apply_impulse((ix * dx, 0))

        if abs(dy) > abs(dx):
            self.cannon.aim += dy / 2

        return False

    def on_touch_up(self, touch):
        self.keys_pressed.clear()

        return super(AlcanGame, self).on_touch_up(touch)

    def trigger_resize(self):
        w, h = Window.size
        self.on_resize(None, w, h)

    def on_resize(self, __win, w, h):
        mw, mh = defs.map_size
        xratio = w / mw
        yratio = h / mh

        self.scale = min(xratio, yratio)

    def update(self, dt):
        self.update_space()

        mi, ma = defs.num_elements_in_zone
        n = sum(int(not e.activated) for e in self.elements_in_zone)

        if n < mi:
            self.drop_element()

        if random.random() < defs.drop_chance and n < ma:
            self.drop_element()

        for o in self.children:
            if isinstance(o, AnimObject):
                o.update(dt)

        for o in self.oo_to.remove:
            self.remove_obj(o, just_schedule=False)
            assert o not in self.children
        self.oo_to.remove.clear()

        for ocl, oa, okw in self.oo_to.add:
            newo = ocl(*oa, **okw)
            self.add_widget(newo)
        self.oo_to.add[:] = []

        if 'up' in self.keys_pressed:
            self.cannon.aim += 3
        if 'down' in self.keys_pressed:
            self.cannon.aim -= 3

        dx = 0
        if 'left' in self.keys_pressed:
            dx -= 20
        if 'right' in self.keys_pressed:
            dx += 20
        if dx:
            self.wizard.body.apply_impulse((defs.wizard_touch_impulse_x * dx, 0))

        self.update_beam_pos(dt)

    def update_beam_pos(self, dt):
       
        if random.random() < defs.beam_speed * dt / 600:
            px, py = self.left_beam.body.position
            self.left_beam.body.position = (px +10, py)

    def drop_element(self):
        """ 
            drop element from heaven 

            but check if there is no drop blockade
        """

        if self.skip_drop:
            return

        _w, h = self.size

        # get proper x coordinate
        x = random.randint(*defs.drop_zone)

        element = Element.random(elizo=self.elements_in_zone)
        if not element:
            return
        element.center = (x, h)
        self.add_widget(element)

    def reached_elname(self, elname):
        if elname == "dragon":
            Logger.debug("reached DRAGON!!!!!")
            wi = Success(center=self.center, size=(700, 400))
            self.add_widget(wi)
            self.game_is_over = True
            App.get_running_app().sm.schedule_gameover()
