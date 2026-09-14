"""
Seeded maze generator for pygame.

Uses recursive backtracking (randomized depth-first search) on a
grid of cells. The same seed always produces the exact same maze,
so you can tie a seed to a level number, a daily challenge, etc.
"""

import random
import pygame
from menuManager import Player
from config import *


class MazeGenerator:
    OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

    def __init__(self, cols, rows, cell_size, seed=None, level=1):
        """
        cols, rows   : maze dimensions in cells
        cell_size    : pixel size of one cell (for drawing)
        seed         : any hashable value (int, str, etc). Same seed
                       -> same maze, every time, on every machine.
        level        : difficulty level this maze belongs to (metadata,
                       doesn't affect generation directly — see
                       generate_level(), which is what actually scales
                       difficulty by choosing cell_size from the level).
        """
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.seed = seed
        self.level = level
        self.rng = random.Random(seed)
        self.origin = (0, 0)  # top-left pixel where the maze is drawn; set by fit_to_screen()/generate_level()

        # Every cell starts fully walled in on all 4 sides.
        self.grid = [
            [{'N': True, 'S': True, 'E': True, 'W': True, 'visited': False}
             for _ in range(cols)]
            for _ in range(rows)
        ]

        self._generate()

        # Start = top-left cell, finish = bottom-right cell (guaranteed
        # reachable, since recursive backtracking visits every cell).
        self.start_cell = (0, 0)
        self.finish_cell = (self.rows - 1, self.cols - 1)
        self.finish_rect = self._cell_marker_rect(self.finish_cell)

    @classmethod
    def fit_to_screen(cls, width, height, cell_size, seed=None, center=True):
        """
        Build a maze sized to exactly fit inside a `width` x `height`
        resolution (e.g. your config's WIDTH/HEIGHT), given a fixed
        cell_size in pixels.

        cols/rows are computed with integer division so the maze
        never overflows the screen. If the resolution doesn't divide
        evenly by cell_size, the few leftover pixels are split evenly
        as a margin on each side (when center=True) so the maze sits
        centered instead of stuck in the top-left corner.
        """
        cols = max(1, width // cell_size)
        rows = max(1, height // cell_size)

        maze = cls(cols, rows, cell_size, seed=seed)
        maze._center_in(width, height, center)
        return maze

    @classmethod
    def generate_level(cls, world_width, world_height, base_cell_size, level=1, seed=None,
                        min_cell_size=40, shrink_per_level=4, center=True):
        """
        Build a maze for a given difficulty `level`, sized to fill a
        world_width x world_height area (e.g. WIDTH*WORLD_SCALE,
        HEIGHT*WORLD_SCALE from config).

        Difficulty scaling: cell_size shrinks by `shrink_per_level`
        pixels per level (down to `min_cell_size`), while the world's
        pixel dimensions stay constant. A smaller cell_size packs more
        cells into the same area, which means more branching corridors,
        more turns, and a longer effective path to the finish — i.e. a
        harder maze — without changing how big the level looks/scrolls.

        min_cell_size exists so corridors never shrink smaller than a
        player can physically fit through (Player is a 30x30 rect).

        Each level gets a distinct-but-deterministic maze: the seed is
        combined with the level number, so the same (seed, level) pair
        always reproduces the same maze, but level 2 isn't just level 1
        redrawn.
        """
        cell_size = max(min_cell_size, base_cell_size - (level - 1) * shrink_per_level)
        cols = max(2, world_width // cell_size)
        rows = max(2, world_height // cell_size)

        level_seed = f"{seed}-L{level}" if seed is not None else None
        maze = cls(cols, rows, cell_size, seed=level_seed, level=level)
        maze._center_in(world_width, world_height, center)
        return maze

    def _center_in(self, width, height, center):
        if center:
            leftover_x = width - self.cols * self.cell_size
            leftover_y = height - self.rows * self.cell_size
            self.origin = (leftover_x // 2, leftover_y // 2)
        else:
            self.origin = (0, 0)
        # origin moved, so the finish marker needs to be recomputed
        self.finish_rect = self._cell_marker_rect(self.finish_cell)

    def _cell_marker_rect(self, cell, scale=0.5):
        """A small centered rect inside a given (row, col) cell, in world space."""
        r, c = cell
        ox, oy = self.origin
        cs = self.cell_size
        size = int(cs * scale)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (ox + c * cs + cs // 2, oy + r * cs + cs // 2)
        return rect

    def spawn_point(self, padding=8):
        """World-space (x, y) pixel position near the start cell, for placing a player."""
        r, c = self.start_cell
        ox, oy = self.origin
        return (ox + c * self.cell_size + padding, oy + r * self.cell_size + padding)

    def _neighbors(self, r, c):
        dirs = [('N', -1, 0), ('S', 1, 0), ('E', 0, 1), ('W', 0, -1)]
        self.rng.shuffle(dirs)  # seeded shuffle -> deterministic order
        for direction, dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.grid[nr][nc]['visited']:
                yield direction, nr, nc

    def _generate(self):
        stack = [(0, 0)]
        self.grid[0][0]['visited'] = True

        while stack:
            r, c = stack[-1]
            neighbor = next(self._neighbors(r, c), None)

            if neighbor:
                direction, nr, nc = neighbor
                # knock down the wall between the current cell and the chosen neighbor
                self.grid[r][c][direction] = False
                self.grid[nr][nc][self.OPPOSITE[direction]] = False
                self.grid[nr][nc]['visited'] = True
                stack.append((nr, nc))
            else:
                stack.pop()  # dead end, backtrack

    def _wall_rects(self, origin, thickness):
        """
        Build the solid rectangle for every standing wall segment.
        Shared by draw() and get_wall_rects() so what's rendered and
        what's collidable are always exactly the same shape — no
        mismatch between what you see and what blocks the player.

        Each segment is extended by `thickness` past the cell edge
        on both ends. Without that, two walls meeting at a corner
        leave a tiny diagonal gap a fast-moving player can clip
        through; the overlap closes that gap so the maze is truly
        solid, not just mostly solid.
        """
        ox, oy = origin
        cs = self.cell_size
        half = thickness // 2
        rects = []

        for r in range(self.rows):
            for c in range(self.cols):
                x = ox + c * cs
                y = oy + r * cs
                cell = self.grid[r][c]

                if cell['N']:
                    rects.append(pygame.Rect(x - half, y - half, cs + thickness, thickness))
                if cell['S']:
                    rects.append(pygame.Rect(x - half, y + cs - half, cs + thickness, thickness))
                if cell['W']:
                    rects.append(pygame.Rect(x - half, y - half, thickness, cs + thickness))
                if cell['E']:
                    rects.append(pygame.Rect(x + cs - half, y - half, thickness, cs + thickness))

        return rects

    def draw(self, surface, origin=None, color=(255, 255, 255), wall_thickness=6, camera=None):
        """
        Draw the maze walls as solid filled blocks (not thin lines).
        wall_thickness should match what you pass to get_wall_rects()
        so the visuals and the collision line up.

        If `camera` is given, wall rects are offset into screen space
        via camera.apply(), and rects fully outside the camera's
        visible area are skipped — this keeps drawing cheap even for
        a big, dense high-level maze, since only what's on screen
        actually gets rendered.
        """
        o = origin if origin is not None else self.origin
        visible = camera.visible_world_rect() if camera is not None else None

        for rect in self._wall_rects(o, wall_thickness):
            if visible is not None and not visible.colliderect(rect):
                continue
            draw_rect = camera.apply(rect) if camera is not None else rect
            pygame.draw.rect(surface, color, draw_rect)

    def draw_finish(self, surface, color=(80, 220, 120), camera=None):
        """Draw a marker over the finish cell."""
        draw_rect = camera.apply(self.finish_rect) if camera is not None else self.finish_rect
        pygame.draw.rect(surface, color, draw_rect)

    def get_wall_rects(self, origin=None, thickness=6):
        """
        Return the list of pygame.Rect for every wall segment, for
        collision detection with your Player objects. Pass this into
        Player.move(..., walls=...) to make the maze solid. Defaults
        to self.origin so it lines up with draw() automatically.
        """
        o = origin if origin is not None else self.origin
        return self._wall_rects(o, thickness)


if __name__ == "__main__":
    # Quick standalone preview: run this file directly to see a maze
    # sized to fit a fixed resolution, with a player that can't walk
    # through the walls and reaches a finish marker.
    pygame.init()

    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Maze preview — seed: {SEED}")
    clock = pygame.time.Clock()

    maze = MazeGenerator.fit_to_screen(WIDTH, HEIGHT, CELL_SIZE, seed=SEED)
    walls = maze.get_wall_rects()

    from menuManager import Player
    sx, sy = maze.spawn_point()
    player = Player(sx, sy, 4, (0, 150, 255))

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.move(1, keys)

        win.fill((20, 20, 20))
        maze.draw(win)
        maze.draw_finish(win)
        player.draw(win)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
