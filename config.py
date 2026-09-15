import pygame

WIDTH, HEIGHT = 1000, 500
CELL_SIZE = 60
SEED = "LVL10"

h_midpoint = HEIGHT / 2
w_midpointRun = (WIDTH / 2) / 2
w_midpointPush = (WIDTH + (WIDTH/2))/2


# LEVEL / WORLD
WORLD_SCALE = 5          # maze world is this many times bigger than the screen
WALL_THICKNESS = 4       # used for BOTH drawing and collision so they always match
MIN_CELL_SIZE = 40       # floor for per-level shrinking; must stay bigger than the
SHRINK_PER_LEVEL = 4     # cell_size lost per level, before hitting MIN_CELL_SIZE

# LAVA MECHANIC
LAVA_ENABLED = True    # can be toggled at runtime with the L key
LAVA_RISE_INTERVAL = 10  # seconds between each rise
LAVA_RISE_AMOUNT = 10   # pixels the lava climbs on each rise

# SCREEN
RESIZABLE = True
FULLSCREEN_KEY = pygame.K_F11

# SPRINT — runner only; the pusher never gets this
SPRINT_MULTIPLIER = 1.8
SPRINT_DURATION = 1.5     # seconds a sprint lasts
SPRINT_COOLDOWN = 2.5     # seconds before it can be used again

# PUSHABLE BOXES — only a player with can_push=True (the pusher) can move these
BOX_SIZE = 30
BOXES_BASE = 2
BOXES_PER_LEVEL = 15       # extra boxes added per level

# TRAPS — cycle armed/safe on a timer; touching one while armed sends that
# player back to spawn (same "reset on contact" idea as the lava)
TRAP_SCALE = 0.7          # trap size relative to a maze cell
TRAP_ARMED_SECONDS = 1.5  # how long a trap stays deadly
TRAP_SAFE_SECONDS = 2.5   # how long it stays safe in between
TRAPS_BASE = 2
TRAPS_PER_LEVEL = 15

# LEVERS / GATES — Fireboy & Watergirl style co-op doors: a gate blocks a
# passage until someone stands on its linked lever
LEVERS_BASE = 1
LEVERS_PER_LEVEL = 30

# MAZE OPENNESS — chance to knock down an extra wall after generation,
# turning the single-path maze into one with loops/alternate routes
BRAID_PROBABILITY = 0.03

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

