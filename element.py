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
from utils import shuffled
from snd import Sounds


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

    def __init__(self, momentum=None, *a, **kw):
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

    def __init__(self, elname, activate=False, momentum=None, *a, **kw):
        """
            momentum - that linear one, mass*V
        """
        Logger.debug("new element kwargs=%s, momentum=%s", kw, momentum)
        self.elname = elname
        super(Element, self).__init__(*a, **kw)

        self.imgsrc = "img/" + elname + ".png"
        self.layers = defs.NORMAL_LAYER
        self.wizard = None  # who carry element?
        self.joint_in_use = None
        self.released_at = -1
        self.momentum = momentum

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
            self.parent.set_bfs()
            if self.momentum:
                self.body.velocity = self.momentum / self.body.mass

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
            return None

        Logger.debug("collision: %s vs %s (%s vs %s)", self.elname, element.elname, self, element)
        if self.parent is None:
            Logger.debug("hey, my parent is still none, (and me=%s)", self)
            return
        new_elname = combine_elements(self.elname, element.elname)

        if new_elname is None:
            if random() < defs.explode_when_nocomb:
                self.parent.replace_objs([self, element], Explosion, center=self.center)
                self.parent.elements_in_zone.remove(element)
                self.parent.elements_in_zone.remove(self)
                return -1
            return None

        self.available_elnames.add(new_elname)
        self.parent.reached_elname(new_elname)

        self.parent.replace_objs([self, element], Element, new_elname, activate=True)
        self.parent.elements_in_zone.remove(element)
        self.parent.elements_in_zone.remove(self)

        self.parent.rotate_hint()

        Sounds.merge.play()

        return +5

    @classmethod
    def random(cls, elizo):
        """ generate random element from available.

            Generate useful element, depending on drop_useless_chance

`           elizo - elements in zone, list of Element instances

        """
        Logger.debug("Element.random: elizo=%s available_elnames=%s", elizo, cls.available_elnames)

        all_elnames = [x.elname for x in elizo]
        green_elnames = [x.elname for x in elizo if x.activated]
        white_elnames = [x.elname for x in elizo if not x.activated]

        # first - check if we can just drop enything
        if random() < defs.drop_useless_chance: 
            elname = choice(list(cls.available_elnames))
            Logger.debug("elements: appear pure random element")
            return Element(elname)

        Logger.debug("second")
        # try to drop element E (which is not in zone) which combined with GREEN elements in zone will give 
        # element R which is new
        for x in shuffled(set(cls.available_elnames) - set(white_elnames)):
            #iterate over all availables except those which lay just by wizard
            # (to not duplicate them)
            
            if cls.is_useful(x, with_elnames=green_elnames, avoid=cls.available_elnames):
                return Element(elname=x)

        Logger.debug("third")
        # try to drop element E (which is not in zone) which combined with ANY elements in zone will give 
        # element R which is new
        for x in shuffled(set(cls.available_elnames) - set(white_elnames)):
            #iterate over all availables except those which lay just by wizard

            if cls.is_useful(x, with_elnames=all_elnames, avoid=cls.available_elnames):
                return Element(elname=x)

        # Nothing useful, drop random
        ret = choice(list(cls.available_elnames))
        Logger.debug("fourth nothing useful, drop pure random(%s)", ret)
        return Element(ret)


    @classmethod
    def steps_to_reach(cls):
        """ how many inventions neccessary to reach dragon """
        Logger.debug("steps_to_reach(): cls.available_elnames=%s, dest='dragon'", cls.available_elnames)
        ret = bfs.bfs(cls.available_elnames, 'dragon')
        Logger.debug("returned %s", ret)
        return ret

    @classmethod
    def is_useful(cls, elname, with_elnames, avoid):
        """ combine elname with each of with_elnames and check if it can
            bring something new to elnames, but source element should not belong to 'avoid'  """

        Logger.debug("is_useful elname=%s with=%s avoid=%s", elname, with_elnames, avoid)

        for x in with_elnames:
            result = combine_elements(x, elname)
            if not result:
                continue
            if result in avoid:  # don't produce something we already know
                continue
            
            Logger.debug("USEFUL: elname=%s, with_elnames=%s avoid=%s:  %s + %s gives %s", elname, with_elnames, avoid, elname, x, result)
            return True

        return False

    @classmethod
    def reset(cls):
        cls.available_elnames = {'water', 'air', 'earth', 'fire'}
        cls.present_elnames = []
        cls.shown_baloons = set()
