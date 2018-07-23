""" element (elementary ingredients of matter) and managing it """

from functools import partial
from random import choice, random, sample
import re
import os

from cymunk import PivotJoint
from kivy.logger import Logger
from kivy.properties import BooleanProperty, NumericProperty
from kivy.vector import Vector

from anim import AnimObject
import bfs
import defs


def load_elmap():
    """ load elmap from data/elmap.txt"""
    if load_elmap.data:
        return load_elmap.data

    fname = "data/elmap.txt"
    if "DEBUG" in os.environ:
        fname = "data/elmap-DEBUG.txt"

    with open(fname) as f:
        for line in f:
            g = re.match(r"^(.*)=(.*)\+(.*)$", line)
            if not g:
                continue
            c = g.group(1).strip()
            a = g.group(2).strip()
            b = g.group(3).strip()

            key = tuple(sorted([a, b]))
            assert key not in load_elmap.data, "duplicate combination %s" % key
            load_elmap.data[key] = c

    return load_elmap.data


load_elmap.data = {}


def combine_elements(a, b):
    """ check in elmap, if (a,b) pair should generate
        something else """

    elmap = load_elmap()

    try:
        return elmap[tuple(sorted([a, b]))]
    except KeyError:
        return None


class Explosion(AnimObject):
    """ widget/object which shows explosion on the screen """

    frame = NumericProperty(1)

    def __init__(self, *a, **kw):
        super(Explosion, self).__init__(*a, **kw)
        self.layers = defs.VISUAL_EFFECTS_LAYER

    def update(self, dt):
        if self.parent is None:
            Logger.info("self=%s self.parent=%s self.frame=%s but parent is None",
                        self, self.parent, self.frame)
            return
        if self.frame > 5:
            self.parent.remove_obj(self)
            return
        self.frame += 1

        # dirty hack, how to do it otherwise?
        oldsize = sum(self.size)/2
        size = (100*(5 - self.frame) + 18*(self.frame-1))/4
        ds = oldsize - size
        self.size = (size, size)
        self.pos = Vector(self.pos) + (ds/2, ds/2)


class Element(AnimObject):
    """ element object (water, fire ....) """
    collision_type = 1
    # is activated when shooted, and then it combine with other element
    activated = BooleanProperty(False)

    available_elnames = {'water', 'air', 'earth', 'fire'}
    present_elnames = []
    shown_baloons = set()

    def __init__(self, elname, activate=False, *a, **kw):
        Logger.debug("new element kwargs=%s", kw)
        self.elname = elname
        super(Element, self).__init__(*a, **kw)

        self.imgsrc = "img/" + elname + ".png"
        self.layers = defs.NORMAL_LAYER
        self.wizard = None  # who carry element?
        self.joint_in_use = None
        self.released_at = -1

        if activate:
            self.activate()

        self.present_elnames.append(elname)

    def __repr__(self):
        return "[E:%s id=%s]" % (self.elname, id(self))

    def on_init(self):
        self.parent.elements_in_zone.append(self)

    def on_body_init(self):
        assert self.parent is not None
        if self.elname not in self.shown_baloons:
            self.shown_baloons.add(self.elname)
            self.show_baloon(self.elname)
            self.parent.bfs = self.steps_to_reach()

    def before_removing(self):
        self.present_elnames.remove(self.elname)

    def activate(self, __dt=None, timeout=0.3):
        """ make it green and ready to react with other element """
        if timeout == 'now':
            self.activated = True
            self.shape.layers = defs.NORMAL_LAYER
            if 'activation' not in self.shown_baloons:
                self.shown_baloons.add('activation')
                self.show_baloon('activated \nready to reaction', size=(150, 80))
            return

        self.schedule_once(partial(self.activate, timeout='now'), timeout)

    def joint(self, with_who, point):
        self.unjoint()
        self.joint_in_use = PivotJoint(self.body, with_who.body, point)
        self.space.add(self.joint_in_use)

    def unjoint(self):
        """ remove existing joint """
        if not self.joint_in_use:
            return
        joint = self.joint_in_use
        self.joint_in_use = None
        self.space.remove(joint)

        if self.wizard:
            self.wizard.carried_elements.remove(self)
            self.wizard = None

    def collide_with_another(self, element, __dt=None):
        """ collide with another element. Generate combination, or explosion
            or bounce (return True)
        """
        if not element.activated or not self.activated:
            return True

        Logger.debug("collision: %s vs %s (%s vs %s)", self.elname, element.elname, self, element)
        if self.parent is None:
            Logger.debug("hey, my parent is still none, (and me=%s)", self)
            return
        new_elname = combine_elements(self.elname, element.elname)

        if new_elname is None:
            if random() < defs.explode_when_nocomb:
                self.parent.replace_obj(self, Explosion, center=self.center)
                self.parent.remove_obj(element)
                self.parent.elements_in_zone.remove(element)
                self.parent.elements_in_zone.remove(self)
                self.parent.points -= 1
            return True

        self.parent.set_hint(self.elname, element.elname, new_elname)
        self.available_elnames.add(new_elname)
        self.parent.reached_elname(new_elname)

        self.parent.replace_obj(self, Element, new_elname, activate=True)
        self.parent.remove_obj(element)
        self.parent.elements_in_zone.remove(element)
        self.parent.elements_in_zone.remove(self)

    @classmethod
    def random(cls, elizo):
        """ generate random element from available.

            Generate useful element, depending on drop_useless_chance

`           elizo - elements in zone, list of Element instances

        """
        all_elnames = [x.elname for x in elizo]
        activated_elnames = [x.elname for x in elizo if x.activated]
        # zero pass - if useless element is allowed, then return anything
        # also return anything if activated zone is empty

        if random() < defs.drop_useless_chance or not activated_elnames:
            elname = choice(list(cls.available_elnames))
            Logger.debug("elements: appear pure random element")
            return Element(elname)

        # don't give element we already know
        avenlnames = cls.available_elnames

        for x in sample(avenlnames, len(avenlnames)):
            if cls.is_useful(x, present=all_elnames, activated=activated_elnames):
                return Element(elname=x)

    @classmethod
    def steps_to_reach(cls):
        """ how many inventions neccessary to reach dragon """
        return bfs.bfs(cls.available_elnames, 'dragon')

    @classmethod
    def is_useful(cls, elname, present, activated):
        """ combine elname with each of available elbames and check if it can
        bring something new to elnames  """

        if elname in present:
            return False

        for x in activated:
            result = combine_elements(x, elname)
            if not result:
                continue
            if result in cls.available_elnames:  # don't produce something we already know
                continue
            
            Logger.debug("USEFUL?: elname=%s, activated=%s present=%s:  %s + %s gives %s", elname, activated, present, elname, x, result)
            return True

        return False

    @classmethod
    def reset(cls):
        cls.available_elnames = {'water', 'air', 'earth', 'fire'}
        cls.present_elnames = []
        cls.shown_baloons = set()
