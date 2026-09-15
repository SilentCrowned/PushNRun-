# modules
import pygame
import asyncio
from pathlib import Path
from config import *
from menuManager import *
from levelManager import MazeGenerator
from camera import Camera
from lavaManager import Lava
from obstacles import PushableBox, Trap
from levers import Lever, Gate
from modifiers import pick_modifier

pygame.init()

# --- Window setup: resizable, with an F11 fullscreen toggle ---
screen_width, screen_height = WIDTH, HEIGHT
is_fullscreen = False
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
FONT = pygame.font.SysFont(None, 32)
clock = pygame.time.Clock()

level = 1
pygame.display.set_caption(f"PUSH N RUN! (LEVEL {level})")

# World size is fixed at startup regardless of window size — resizing
# the window changes how much of the world you can see, not the world
# itself (that would regenerate the maze mid-run, which we don't want).
WORLD_WIDTH, WORLD_HEIGHT = WIDTH * WORLD_SCALE, HEIGHT * WORLD_SCALE


def build_level(lvl):
    """
    (Re)build everything that depends on the current level: the maze
    itself, its boxes/traps/lever+gate pairs, and this level's random
    modifier (drawn from config.MODIFIERS, using the maze's own seeded
    RNG so it's deterministic for a given (seed, level)).
    """
    maze = MazeGenerator.generate_level(
        WORLD_WIDTH, WORLD_HEIGHT, CELL_SIZE,
        level=lvl, seed=SEED,
        min_cell_size=MIN_CELL_SIZE, shrink_per_level=SHRINK_PER_LEVEL,
    )
    walls = maze.get_wall_rects(thickness=WALL_THICKNESS)
    modifier = pick_modifier(maze.rng, MODIFIERS)

    boxes = [PushableBox(x, y, BOX_SIZE) for x, y in maze.box_spawns]

    trap_cycle = TRAP_ARMED_SECONDS + modifier.trap_safe_seconds
    traps = [
        Trap(x, y, int(maze.cell_size * TRAP_SCALE), TRAP_ARMED_SECONDS, modifier.trap_safe_seconds,
             phase_offset=maze.rng.random() * trap_cycle)
        for x, y in maze.trap_spawns
    ]

    levers, gates = [], []
    for segment_rect, lever_center in maze.gate_specs:
        levers.append(Lever(*lever_center))
        gates.append(Gate(segment_rect))

    return maze, walls, boxes, traps, levers, gates, modifier


maze, walls, boxes, traps, levers, gates, modifier = build_level(level)

# Declaring Objects — spawn at the maze's start cell instead of a
# hardcoded position, since the maze is now much bigger than the screen.
spawn_x, spawn_y = maze.spawn_point()
runner = Player(spawn_x, spawn_y, 5, BLUE, FONT, can_sprint=True, can_push=False)
pusher = Player(spawn_x, spawn_y, 3, RED, FONT, can_sprint=False, can_push=True)


def apply_modifier_to_players(mod):
    runner.sprint_multiplier = mod.sprint_multiplier
    runner.slide_factor = mod.slide_factor
    pusher.slide_factor = mod.slide_factor
    pusher.speed = pusher.base_speed * mod.push_speed_multiplier


apply_modifier_to_players(modifier)

# Camera setup: one camera per player, feeding a split-screen viewport.
camera_runner = Camera(screen_width // 2, screen_height, WORLD_WIDTH, WORLD_HEIGHT)
camera_pusher = Camera(screen_width - screen_width // 2, screen_height, WORLD_WIDTH, WORLD_HEIGHT)

lava = Lava(
    WORLD_WIDTH, WORLD_HEIGHT,
    enabled=LAVA_ENABLED,
    rise_interval=LAVA_RISE_INTERVAL,
    rise_amount=LAVA_RISE_AMOUNT,
)

# Loading skins — glob() on a missing folder just returns no matches
# (skins stays []), so this is safe even before assets exist.
skin_folder = Path("assets/players/")
runner.skins = [f.stem for f in skin_folder.glob("*.png")]
pusher.skins = [f.stem for f in skin_folder.glob("*.png")]

# Select-screen buttons for cycling skins, shown during the menu state.
runner_button = Button(int(w_midpointRun) - 75, int(h_midpoint) - 60, 220, 40, "Runner Skin", FONT, player=runner)
pusher_button = Button(int(w_midpointPush) - 75, int(h_midpoint) - 60, 220, 40, "Pusher Skin", FONT, player=pusher)
runner_ready, pusher_ready = False, False

# Game States
menu = True
running = False
quit_requested = False
debug_mode = False
debug_task = None  # holds the currently running debug coroutine, if any


def build_viewports():
    """Split the window into left (runner) / right (pusher) halves as subsurfaces of screen."""
    half_w = screen_width // 2
    left = screen.subsurface(pygame.Rect(0, 0, half_w, screen_height))
    right = screen.subsurface(pygame.Rect(half_w, 0, screen_width - half_w, screen_height))
    return left, right


viewport_left, viewport_right = build_viewports()


def handle_resize(new_width, new_height):
    """Rebuild the window, its two viewports, and both cameras' dimensions to match."""
    global screen, screen_width, screen_height, viewport_left, viewport_right
    screen_width, screen_height = max(400, new_width), max(300, new_height)
    flags = pygame.FULLSCREEN if is_fullscreen else pygame.RESIZABLE
    screen = pygame.display.set_mode((screen_width, screen_height), flags)
    viewport_left, viewport_right = build_viewports()
    camera_runner.screen_width, camera_runner.screen_height = viewport_left.get_width(), screen_height
    camera_pusher.screen_width, camera_pusher.screen_height = viewport_right.get_width(), screen_height


def toggle_fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        info = pygame.display.Info()
        handle_resize(info.current_w, info.current_h)
    else:
        handle_resize(WIDTH, HEIGHT)


def respawn_player(player, offset=(0, 0)):
    sx, sy = maze.spawn_point()
    player.rect.topleft = (sx + offset[0], sy + offset[1])


def respawn_players():
    respawn_player(runner)
    respawn_player(pusher, offset=(34, 0))


def rebuild_level(new_level):
    global level, maze, walls, boxes, traps, levers, gates, modifier
    level = new_level
    maze, walls, boxes, traps, levers, gates, modifier = build_level(level)
    apply_modifier_to_players(modifier)
    respawn_players()
    lava.reset()
    pygame.display.set_caption(f"PUSH N RUN! (LEVEL {level}) \u2014 Modifier: {modifier.name}")
    print(f"Level {level}! Modifier: {modifier.name}. Cell size now {maze.cell_size}px "
          f"({maze.cols}x{maze.rows} cells, {len(boxes)} boxes, {len(traps)} traps, {len(levers)} levers).")


def advance_level():
    """Called when both players reach the finish line together."""
    rebuild_level(level + 1)


def reset():
    """Rebuild level 1 from scratch — bound to the R key."""
    rebuild_level(1)


async def debug():
    print(f"{'=' * 15}\nDEBUG MODE\n{'=' * 15}")
    while debug_mode:
        print("Level\tModifier\tLava\tRunner\tPusher")
        print(f"{level}\t{modifier.name}\t{'ON' if lava.enabled else 'OFF'}\t"
              f"x:{runner.rect.x},y:{runner.rect.y}\tx:{pusher.rect.x},y:{pusher.rect.y}")
        await asyncio.sleep(2)


def draw_world(surface, camera):
    """Draw one player's half of the split screen: maze, hazards, objects, both players."""
    maze.draw(surface, wall_thickness=WALL_THICKNESS, camera=camera)
    maze.draw_finish(surface, camera=camera)
    for gate in gates:
        gate.draw(surface, camera=camera)
    for lever in levers:
        lever.draw(surface, camera=camera)
    for trap in traps:
        trap.draw(surface, camera=camera)
    for box in boxes:
        box.draw(surface, camera=camera)
    lava.draw(surface, camera=camera)
    runner.draw(surface, camera=camera)
    pusher.draw(surface, camera=camera)


async def main():
    global menu, running, quit_requested, debug_mode, debug_task, runner_ready, pusher_ready

    # --- Menu / character-select state ---
    while menu:
        screen.fill(WHITE)

        runner.draw_static(screen, w_midpointRun, h_midpoint)
        pusher.draw_static(screen, w_midpointPush, h_midpoint)
        runner_button.draw(screen)
        pusher_button.draw(screen)

        status = FONT.render(
            f"Runner ready: {runner_ready}   Pusher ready: {pusher_ready}",
            True, BLACK,
        )
        screen.blit(status, (20, screen_height - 60))
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                menu = False
                quit_requested = True
            elif e.type == pygame.VIDEORESIZE and not is_fullscreen:
                handle_resize(e.w, e.h)
            elif e.type == pygame.KEYDOWN:
                if e.key == FULLSCREEN_KEY:
                    toggle_fullscreen()
                elif e.key == pygame.K_w:
                    runner.previous_skin()
                elif e.key == pygame.K_s:
                    runner.next_skin()
                elif e.key == pygame.K_d:
                    runner_ready = True
                elif e.key == pygame.K_a:
                    runner_ready = False
                elif e.key == pygame.K_UP:
                    pusher.previous_skin()
                elif e.key == pygame.K_DOWN:
                    pusher.next_skin()
                elif e.key == pygame.K_RIGHT:
                    pusher_ready = True
                elif e.key == pygame.K_LEFT:
                    pusher_ready = False

        if runner_ready and pusher_ready:
            menu = False
            running = True

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    if quit_requested:
        running = False

    # --- Main gameplay state ---
    while running:
        # clock.get_time() reflects the previous frame's duration
        # (clock.tick() is called at the bottom of the loop, as before);
        # first frame is 0, which is fine since nothing time-based fires instantly.
        dt = clock.get_time() / 1000.0
        keys = pygame.key.get_pressed()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.VIDEORESIZE and not is_fullscreen:
                handle_resize(e.w, e.h)
            elif e.type == pygame.KEYDOWN:
                if e.key == FULLSCREEN_KEY:
                    toggle_fullscreen()
                elif e.key == pygame.K_LALT:
                    debug_mode = not debug_mode
                    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
                    if debug_mode and (debug_task is None or debug_task.done()):
                        debug_task = asyncio.create_task(debug())
                elif e.key == pygame.K_l:
                    lava.toggle()
                    print(f"Lava mechanic: {'ON' if lava.enabled else 'OFF'}")

        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_r]:
            reset()

        # Runner-only sprint input; try_sprint() is a no-op for a
        # player with can_sprint=False, so this is safe either way.
        if keys[pygame.K_LSHIFT]:
            runner.try_sprint()

        # --- Updates ---
        runner.update(dt)
        pusher.update(dt)
        lava.update(dt)
        for trap in traps:
            trap.update(dt)
        for lever, gate in zip(levers, gates):
            lever.update([runner.rect, pusher.rect])
            gate.update(lever)

        # Gates count as extra walls only while closed.
        effective_walls = walls + [gate.rect for gate in gates if gate.closed]

        # "Panic" modifier swaps which control scheme drives which player.
        runner_controls = 2 if modifier.swapped_controls else 1
        pusher_controls = 1 if modifier.swapped_controls else 2
        runner.move(runner_controls, keys, walls=effective_walls, boxes=boxes)
        pusher.move(pusher_controls, keys, walls=effective_walls, boxes=boxes)

        camera_runner.update(runner.rect)
        camera_pusher.update(pusher.rect)

        for trap in traps:
            if trap.catches(runner.rect):
                respawn_player(runner)
            if trap.catches(pusher.rect):
                respawn_player(pusher, offset=(34, 0))
        if lava.collides_with(runner.rect):
            respawn_player(runner)
        if lava.collides_with(pusher.rect):
            respawn_player(pusher, offset=(34, 0))

        # Co-op finish: BOTH players need to be at the finish line together.
        if maze.finish_rect.colliderect(runner.rect) and maze.finish_rect.colliderect(pusher.rect):
            advance_level()

        # --- Drawing ---
        screen.fill(BLACK)
        draw_world(viewport_left, camera_runner)
        draw_world(viewport_right, camera_pusher)
        pygame.draw.line(screen, WHITE, (screen_width // 2, 0), (screen_width // 2, screen_height), 3)

        pygame.display.flip()
        clock.tick(60)

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
