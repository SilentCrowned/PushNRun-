# modules
import pygame
import asyncio
import time
from config import *
from menuManager import *
from levelManager import MazeGenerator
from camera import Camera
from lavaManager import Lava

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"PUSH N RUN! (LEVEL {level})")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 32)

# World / level setup
WORLD_WIDTH, WORLD_HEIGHT = WIDTH * WORLD_SCALE, HEIGHT * WORLD_SCALE

LEVEL = 1
maze = MazeGenerator.generate_level(
    WORLD_WIDTH, WORLD_HEIGHT, CELL_SIZE,
    level=LEVEL, seed=SEED,
    min_cell_size=MIN_CELL_SIZE, shrink_per_level=SHRINK_PER_LEVEL,
)
walls = maze.get_wall_rects(thickness=WALL_THICKNESS)

# Declaring Objects — spawn at the maze's start cell instead of a
# hardcoded position, since the maze is now much bigger than the screen.
spawn_x, spawn_y = maze.spawn_point()
runner = Player(spawn_x, spawn_y, 5, BLUE)
pusher = Player(spawn_x + 34, spawn_y, 3, RED)

camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
lava = Lava(
    WORLD_WIDTH, WORLD_HEIGHT,
    enabled=LAVA_ENABLED,
    rise_interval=LAVA_RISE_INTERVAL,
    rise_amount=LAVA_RISE_AMOUNT,
)

# Game States
running = True
now = 0
then = 0
debug_mode = False
debug_task = None  # holds the currently running debug coroutine, if any


def respawn_players():
    sx, sy = maze.spawn_point()
    runner.rect.topleft = (sx, sy)
    pusher.rect.topleft = (sx + 34, sy)


def advance_level():
    """Called when the runner reaches the finish line."""
    global LEVEL, maze, walls
    LEVEL += 1
    maze = MazeGenerator.generate_level(
        WORLD_WIDTH, WORLD_HEIGHT, CELL_SIZE,
        level=LEVEL, seed=SEED,
        min_cell_size=MIN_CELL_SIZE, shrink_per_level=SHRINK_PER_LEVEL,
    )
    walls = maze.get_wall_rects(thickness=WALL_THICKNESS)
    respawn_players()
    lava.reset()
    print(f"Level {level}! Cell size now {maze.cell_size}px ({maze.cols}x{maze.rows} cells).")

def reset():
    global level, maze, walls
    maze = MazeGenerator.generate_level(
            WORLD_WIDTH, WORLD_HEIGHT, CELL_SIZE,
            seed=SEED,
            min_cell_size=MIN_CELL_SIZE, shrink_per_level=SHRINK_PER_LEVEL,
        )
    walls = maze.get_wall_rects(thickness=WALL_THICKNESS)
    respawn_players()
    lava.reset()


async def debug():
    global then
    print(f"{'=' * 15}\nDEBUG MODE\n{'=' * 15}")
    while debug_mode:
        print("Now\tThen\tLevel\tLava\tPlayer Position\nSEED")
        print(f"{now}\t{then}\t{level}\t{'ON' if lava.enabled else 'OFF'}\tx:{runner.rect.x},y:{runner.rect.y}\t{SEED}")
        await asyncio.sleep(2)
    await asyncio.sleep(5)
    then = now


async def main():
    global running, now, debug_mode, debug_task

    while running:
        # clock.get_time() reflects the previous frame's duration
        # (clock.tick() is called at the bottom of the loop, as before);
        # first frame is 0, which is fine since nothing time-based fires instantly.
        dt = clock.get_time() / 1000.0
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        # Events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LALT:
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

        # Updates
        lava.update(dt)
        runner.move(1, keys, walls)
        camera.update(runner.rect)

        if runner.rect.colliderect(maze.finish_rect):
            advance_level()
        elif lava.collides_with(runner.rect):
            respawn_players()

        # Drawing
        screen.fill(BLACK)
        maze.draw(screen, wall_thickness=WALL_THICKNESS, camera=camera)
        maze.draw_finish(screen, camera=camera)
        lava.draw(screen, camera=camera)
        runner.draw(screen, camera=camera)

        pygame.display.flip()
        clock.tick(60)

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())