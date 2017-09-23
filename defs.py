fps = 20

gravity = (0, -700)

friction = 0.5
floor_level = 50
kill_level = -1000

wizard_mass = 100
wizard_impulse = (10000, 1000)
wizard_hand = (30, -20) #offset from center, where wizard carry things
wizard_max_speed = 240

shoot_force = 8000

mintouchdist = 100

protected_area = (300, 500) #range from each side of map, where elements are not dropped (cannon is there)
map_size = (1350, 720)

drop_chance = 0.02

#constants

NORMAL_LAYER = 1
CARRIED_THINGS_LAYER = 1<<1
VISUAL_EFFECTS_LAYER = 1<<2
