"""
Simple scrolling camera for pygame.

Design: game-logic objects (player rects, maze walls, lava, the
finish line) always keep their real, fixed WORLD coordinates — the
camera never moves them. It only computes a screen-space offset that
drawing code applies at render time, via camera.apply(rect). That
keeps collision/logic code completely unaware the camera exists.
"""

import pygame


class Camera:
    def __init__(self, screen_width, screen_height, world_width, world_height, smoothing=0.12):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.smoothing = smoothing  # 0..1 — higher = snappier follow, lower = laggier/smoother

        self.x = 0.0
        self.y = 0.0

    def update(self, target_rect):
        """Center the camera on target_rect (e.g. the runner's rect), clamped to world bounds."""
        desired_x = target_rect.centerx - self.screen_width / 2
        desired_y = target_rect.centery - self.screen_height / 2

        # Clamp so the camera never shows past the edge of the world.
        # If the world is smaller than the screen on an axis, just center it.
        max_x = max(0, self.world_width - self.screen_width)
        max_y = max(0, self.world_height - self.screen_height)
        desired_x = min(max(desired_x, 0), max_x)
        desired_y = min(max(desired_y, 0), max_y)

        # Smoothly interpolate toward the desired position instead of snapping,
        # so the screen doesn't jerk around on every frame of player movement.
        self.x += (desired_x - self.x) * self.smoothing
        self.y += (desired_y - self.y) * self.smoothing

    def apply(self, rect):
        """Return a copy of rect shifted into screen space, for drawing."""
        return rect.move(-int(self.x), -int(self.y))

    def apply_pos(self, x, y):
        """Shift a raw (x, y) world coordinate into screen space."""
        return x - int(self.x), y - int(self.y)

    def visible_world_rect(self):
        """The world-space rectangle currently visible on screen (for culling draws)."""
        return pygame.Rect(int(self.x), int(self.y), self.screen_width, self.screen_height)
