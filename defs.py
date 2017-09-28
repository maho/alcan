""" definitions/constants """

fps = 20

gravity = (0, -700)
baloon_force = (0, 7500)

friction = 0.3
floor_level = 50
kill_level = -1000

wizard_mass = 100
wizard_touch_impulse_x = 1000
wizard_hand = (30, -20)  # offset from center, where wizard carry things
wizard_max_speed = 400
wizard_friction = 4
wizard_release_impulse = (100, 1900)

shoot_force = 7000

mintouchdist = 100

map_size = (1280, 720)

drop_chance = 0.002
drop_zone = (0, 400)
num_elements_in_zone = (1, 5)
explode_when_nocomb = False  # explode elements when they make impossible combination

# constants

NORMAL_LAYER = 1
CARRIED_THINGS_LAYER = (1 << 1)
SHOOTED_THINGS_LAYER = (1 << 2)
VISUAL_EFFECTS_LAYER = (1 << 3)
