"""
Seeded maze generator for pygame.

Uses recursive backtracking (randomized depth-first search) on a
grid of cells, then optionally "braids" the result by knocking down
some extra walls to add loops/alternate routes. The same seed always
produces the exact same maze (and the same braiding, obstacle
placement, and modifier), so you can tie a seed to a level number, a
daily challenge, etc.
"""

import random
import pygame
from menuManager import Player
from config import *


class MazeGenerator:
    OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
    FINISH_SCALE = 0.85  # finish marker covers most of its cell, so two players can both stand in it

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
        self.finish_rect = self._cell_marker_rect(self.finish_cell, self.FINISH_SCALE)

        # Populated by generate_features(); empty until then.
        self.box_spawns = []
        self.trap_spawns = []
        self.gate_specs = []

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
                        min_cell_size=40, shrink_per_level=4, center=True, braid_probability=None):
        """
        Build a maze for a given difficulty `level`, sized to fill a
        world_width x world_height area (e.g. WIDTH*WORLD_SCALE,
        HEIGHT*WORLD_SCALE from config).

        Difficulty scaling: cell_size shrinks by `shrink_per_level`
        pixels per level (down to `min_cell_size`), while the world's
        pixel dimensions stay constant. A smaller cell_size packs more
        cells into the same area — more turns, more decisions — i.e. a
        harder maze, without changing how big the level looks/scrolls.

        After generation, this braids in extra loops (see _braid) so
        the maze has many openings/alternate routes rather than a
        single forced path, then procedurally places boxes, traps, and
        lever/gate pairs, with counts that scale up with `level` (via
        config's BOXES_BASE/BOXES_PER_LEVEL etc).

        Each level gets a distinct-but-deterministic layout: the seed
        is combined with the level number, so the same (seed, level)
        pair always reproduces the same maze/obstacles/modifier.
        """
        cell_size = max(min_cell_size, base_cell_size - (level - 1) * shrink_per_level)
        cols = max(2, world_width // cell_size)
        rows = max(2, world_height // cell_size)

        level_seed = f"{seed}-L{level}" if seed is not None else None
        maze = cls(cols, rows, cell_size, seed=level_seed, level=level)
        maze._center_in(world_width, world_height, center)

        maze._braid(braid_probability if braid_probability is not None else BRAID_PROBABILITY)

        num_boxes = BOXES_BASE + (level - 1) * BOXES_PER_LEVEL
        num_traps = TRAPS_BASE + (level - 1) * TRAPS_PER_LEVEL
        num_levers = LEVERS_BASE + (level - 1) * LEVERS_PER_LEVEL
        maze.generate_features(num_boxes, num_traps, num_levers)

        return maze

    def _center_in(self, width, height, center):
        if center:
            leftover_x = width - self.cols * self.cell_size
            leftover_y = height - self.rows * self.cell_size
            self.origin = (leftover_x // 2, leftover_y // 2)
        else:
            self.origin = (0, 0)
        # origin moved, so the finish marker needs to be recomputed
        self.finish_rect = self._cell_marker_rect(self.finish_cell, self.FINISH_SCALE)

    def _cell_marker_rect(self, cell, scale=0.5):
        """A small centered rect inside a given (row, col) cell, in world space."""
        r, c = cell
        ox, oy = self.origin
        cs = self.cell_size
        size = int(cs * scale)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (ox + c * cs + cs // 2, oy + r * cs + cs // 2)
        return rect

    def cell_center(self, cell):
        """World-space pixel center of a (row, col) cell."""
        r, c = cell
        ox, oy = self.origin
        cs = self.cell_size
        return (ox + c * cs + cs // 2, oy + r * cs + cs // 2)

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

    def _braid(self, probability):
        """
        After the perfect maze is generated, add loops by randomly
        knocking down some of the *remaining* walls between adjacent
        cells. A recursive-backtracker maze has exactly one path
        between any two cells; braiding adds extra connections, which
        is what turns it into a maze with "many openings" rather than
        one single forced corridor.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                for direction, dr, dc in (('N', -1, 0), ('S', 1, 0), ('E', 0, 1), ('W', 0, -1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                        continue
                    if self.grid[r][c][direction] and self.rng.random() < probability:
                        self.grid[r][c][direction] = False
                        self.grid[nr][nc][self.OPPOSITE[direction]] = False

    def generate_features(self, num_boxes, num_traps, num_levers, wall_thickness=None):
        """
        Populate self.box_spawns / self.trap_spawns / self.gate_specs
        with world-space placements, using this maze's own seeded RNG
        so the same (seed, level) always gets the same layout.

        gate_specs is a list of (segment_rect, lever_center) pairs:
        lever_center is where to put a Lever, and segment_rect is an
        existing *open* passage next to it that gets turned into a
        Gate — so the gate sits at a real chokepoint rather than an
        arbitrary spot.

        This is a best-effort placement, not a guaranteed-solvable
        puzzle generator: with braiding adding loops, closing one
        gated passage usually still leaves another route around,
        which is fine for a "many openings" maze but means a given
        gate isn't always strictly mandatory to reach the finish.
        """
        wall_thickness = wall_thickness if wall_thickness is not None else WALL_THICKNESS

        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if (r, c) not in (self.start_cell, self.finish_cell)]
        self.rng.shuffle(all_cells)

        box_cells = all_cells[:num_boxes]
        trap_cells = all_cells[num_boxes:num_boxes + num_traps]
        lever_cells = all_cells[num_boxes + num_traps:num_boxes + num_traps + num_levers]

        self.box_spawns = [self.cell_center(cell) for cell in box_cells]
        self.trap_spawns = [self.cell_center(cell) for cell in trap_cells]

        self.gate_specs = []
        for cell in lever_cells:
            r, c = cell
            open_dirs = [d for d in ('N', 'S', 'E', 'W') if not self.grid[r][c][d]]
            if not open_dirs:
                continue
            direction = self.rng.choice(open_dirs)
            segment_rect = self._wall_segment_rect(self.origin, r, c, direction, wall_thickness)
            self.gate_specs.append((segment_rect, self.cell_center(cell)))

        return self.box_spawns, self.trap_spawns, self.gate_specs

    def _wall_segment_rect(self, origin, r, c, direction, thickness):
        """
        The solid rectangle for one wall segment (one cell, one side).
        Extended by `thickness` past the cell edge on both ends so
        two walls meeting at a corner don't leave a tiny diagonal gap
        a fast-moving player could clip through.
        """
        ox, oy = origin
        cs = self.cell_size
        half = thickness // 2
        x = ox + c * cs
        y = oy + r * cs

        if direction == 'N':
            return pygame.Rect(x - half, y - half, cs + thickness, thickness)
        if direction == 'S':
            return pygame.Rect(x - half, y + cs - half, cs + thickness, thickness)
        if direction == 'W':
            return pygame.Rect(x - half, y - half, thickness, cs + thickness)
        if direction == 'E':
            return pygame.Rect(x + cs - half, y - half, thickness, cs + thickness)
        raise ValueError(f"unknown wall direction: {direction!r}")

    def _wall_rects(self, origin, thickness):
        """Every standing wall segment, as solid rects. Shared by draw() and get_wall_rects()."""
        rects = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                for direction in ('N', 'S', 'E', 'W'):
                    if cell[direction]:
                        rects.append(self._wall_segment_rect(origin, r, c, direction, thickness))
        return rects

    def draw(self, surface, origin=None, color=(255, 255, 255), wall_thickness=6, camera=None):
        """
        Draw the maze walls as solid filled blocks (not thin lines).
        wall_thickness should match what you pass to get_wall_rects()
        so the visuals and the collision line up.

        If `camera` is given, wall rects are offset into screen space
        via camera.apply(), and rects fully outside the camera's
        visible area are skipped — keeps drawing cheap even for a
        big, dense high-level maze.
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
    # Quick standalone preview: run this file directly to see the maze
    # at its true, accurate scale — built with generate_level(), the
    # same method the real game uses, not the smaller screen-fitted
    # fit_to_screen() — with a player that can't walk through the
    # walls and reaches a finish marker.
    #
    # The real maze is much bigger than a normal window, so the whole
    # preview is scaled down to fit inside (WIDTH, HEIGHT) while
    # keeping its aspect ratio and staying centered. Walls are drawn
    # thin here (not the in-game WALL_THICKNESS) so a shrunk-down maze
    # doesn't turn into a solid white blob.
    pygame.init()

    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Maze preview — seed: {SEED}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    PREVIEW_WALL_THICKNESS = 2  # thin, regardless of the in-game WALL_THICKNESS

    world_width, world_height = WIDTH * WORLD_SCALE, HEIGHT * WORLD_SCALE
    maze = MazeGenerator.generate_level(
        world_width, world_height, CELL_SIZE,
        level=1, seed=SEED,
        min_cell_size=MIN_CELL_SIZE, shrink_per_level=SHRINK_PER_LEVEL,
    )
    walls = maze.get_wall_rects(thickness=PREVIEW_WALL_THICKNESS)

    # Scale everything down to fit the window if the true map is bigger
    # than it; stays 1.0 (no shrinking) if it already fits.
    scale = min(1.0, WIDTH / world_width, HEIGHT / world_height)
    scaled_w, scaled_h = int(world_width * scale), int(world_height * scale)
    offset_x, offset_y = (WIDTH - scaled_w) // 2, (HEIGHT - scaled_h) // 2

    def to_preview(rect):
        """Map a world-space rect onto the scaled, centered preview window."""
        return pygame.Rect(
            offset_x + int(rect.x * scale),
            offset_y + int(rect.y * scale),
            max(1, int(rect.width * scale)),
            max(1, int(rect.height * scale)),
        )

    sx, sy = maze.spawn_point()
    player = Player(sx, sy, 10, (0, 150, 255), font)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.move(1, keys, walls=walls)

        win.fill((20, 20, 20))
        for wall in walls:
            pygame.draw.rect(win, (255, 255, 255), to_preview(wall))
        pygame.draw.rect(win, (80, 220, 120), to_preview(maze.finish_rect))
        pygame.draw.rect(win, player.color, to_preview(player.rect))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()