import pygame

WIDTH, HEIGHT = 1000, 500
CELL_SIZE = 60
SEED = "Cheese"

level = 1

h_midpoint = HEIGHT / 2


# LEVEL / WORLD
WORLD_SCALE = 3          # maze world is this many times bigger than the screen
WALL_THICKNESS = 4       # used for BOTH drawing and collision so they always match
MIN_CELL_SIZE = 40       # floor for per-level shrinking; must stay bigger than the
SHRINK_PER_LEVEL = 4     # cell_size lost per level, before hitting MIN_CELL_SIZE

# LAVA MECHANIC
LAVA_ENABLED = True    # can be toggled at runtime with the L key
LAVA_RISE_INTERVAL = 20  # seconds between each rise
LAVA_RISE_AMOUNT = 10    # pixels the lava climbs on each rise

# COLORS
PINK = (255,182,193)
BLUE = (90,160,255)
RED = (255,90,90)
ORANGE = (255,120,0)
GRAY = (160,160,160)
GREEN = (80,220,120)
WHITE = (255,255,255)
BLACK = (20, 20, 20)

# ROOM TEMPLATES
ROOMS = [
    [pygame.Rect(200,300,80,40)],
    [pygame.Rect(250,200,80,40), pygame.Rect(320,300,80,40)],
    [pygame.Rect(220,260,120,40)],
    [pygame.Rect(260,180,80,40)]
]

MODIFIERS = [
    ("Short Fuse", {"step":3}),
    ("Heavy World", {"push":0.5}),
    ("Slippery", {"slide":0.15}),
    ("Rush", {"dash":2.0}),
    ("Panic", {"swap":True})
]