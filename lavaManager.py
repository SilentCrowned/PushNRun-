"""
Rising lava hazard.

The lava is a horizontal band that starts below the bottom of the
world (invisible) and, once enabled, climbs upward by `rise_amount`
pixels every `rise_interval` seconds. It occupies everything from its
current edge down to the bottom of the world, so as it rises it
eats up more and more of the maze — forcing the player to reach the
finish line before it catches them.

Fully toggleable at runtime via `.toggle()` / `.enabled`, and per the
brief, "off" means it neither rises nor blocks/damages the player.
"""

import pygame


class Lava:
    def __init__(self, world_width, world_height, enabled=True,
                 rise_interval=20.0, rise_amount=80, color=(255, 90, 0)):
        self.world_width = world_width
        self.world_height = world_height
        self.enabled = enabled
        self.rise_interval = rise_interval
        self.rise_amount = rise_amount
        self.color = color

        self.level_y = float(world_height)  # top edge of the lava; starts just past the bottom
        self._timer = 0.0

    def toggle(self):
        self.enabled = not self.enabled

    def reset(self):
        """Call this whenever a new maze/level starts, to push the lava back down."""
        self.level_y = float(self.world_height)
        self._timer = 0.0

    def update(self, dt):
        """dt is elapsed time in seconds since the last frame."""
        if not self.enabled:
            return
        self._timer += dt
        if self._timer >= self.rise_interval:
            self._timer -= self.rise_interval
            self.level_y = max(0.0, self.level_y - self.rise_amount)

    @property
    def rect(self):
        """World-space rect covering the area at/below the current lava edge."""
        y = int(self.level_y)
        return pygame.Rect(0, y, self.world_width, max(0, self.world_height - y))

    def collides_with(self, rect):
        """True only if lava is enabled AND actually overlapping rect."""
        return self.enabled and rect.colliderect(self.rect)

    def draw(self, surface, camera=None):
        if not self.enabled:
            return
        draw_rect = camera.apply(self.rect) if camera is not None else self.rect
        pygame.draw.rect(surface, self.color, draw_rect)
