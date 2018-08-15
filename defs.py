""" definitions/constants """

syslog_host= ("dlaptop", 5555)

fps = 20

gravity = (0, -750)
baloon_force = (300, 7900)
max_hints = 3

friction = 0.55
floor_level = -5
kill_level = -1000

wizard_mass = 200
wizard_touch_impulse_x = 1000
wizard_hand = (40, -20)  # offset from center, where wizard carry things
wizard_max_speed = 400
wizard_friction = 4 * 9 / 13
wizard_release_impulse = (-100, 2200)

shoot_force = 7700

mintouchdist = 150

map_size = (1280, 720)

skip_drop_time = 3 # how much time to skip dropping new elements, before we know what is result of shot
drop_useless_chance = 0.000
drop_chance = 0.005
drop_zone = (0, 400)
num_elements_in_zone = (2, 8)
explode_when_nocomb = False  # explode elements when they make impossible combination

left_beam_fine_pos = 0
beam_speed = 20  # number of pixels per minute

# constants

NORMAL_LAYER = 1
CARRIED_THINGS_LAYER = (1 << 1)
SHOOTED_THINGS_LAYER = (1 << 2)
VISUAL_EFFECTS_LAYER = (1 << 3)
PLATFORMS_LAYER = (1 << 4)

LEFT_BOUND = 1001
RIGHT_BOUND = 1002
BOTTOM_BOUND = 1003

INTRO_TEXT = """
Long time ago, in the middle ages...

The Swiss Alchemists obsessed with finding way to invent way to breed dragon,
bring into life theories about transmutation elements into another.

Because of lack of philosopher's stone, the Swiss Alchemists has secretly begun
construction of Large Element Collider, the powerful and complex experimental
facility.

Now L.E.C. is constructed, help them to breed dragon from base elements.

"""
