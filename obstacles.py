"""
Pushable boxes and timed floor traps.

Boxes: only a player with can_push=True (the pusher) can move these;
everyone else collides with them like a wall. The actual push
resolution happens in Player.move() (menuManager.py) since it needs
walls and boxes together to correctly block a box against a wall or
another box — these classes just hold the box's state and draw it.

Traps: cycle between a safe phase and an armed (deadly) phase on a
timer. Touching one while armed sends that player back to the maze's
spawn point — same "reset on contact" behavior as the lava, just
localized to one tile and on a much faster, harder-to-predict clock.
Each trap gets a random phase offset so they don't all sync up,
which is what actually creates the "not fast enough" timing pressure.
"""

import pygame


class PushableBox:
    def __init__(self, x, y, size, color=(200, 140, 60)):
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (x, y)
        self.color = color

    def draw(self, surface, camera=None):
        rect = camera.apply(self.rect) if camera is not None else self.rect
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, (90, 60, 20), rect, 3)  # border so it reads as an object, not a wall


class Trap:
    def __init__(self, x, y, size, armed_seconds, safe_seconds, phase_offset=0.0,
                 armed_color=(230, 40, 40), safe_color=(80, 220, 120)):
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (x, y)
        self.armed_seconds = armed_seconds
        self.safe_seconds = safe_seconds
        self.armed_color = armed_color
        self.safe_color = safe_color
        self._timer = phase_offset % (armed_seconds + safe_seconds)

    def update(self, dt):
        cycle = self.armed_seconds + self.safe_seconds
        self._timer = (self._timer + dt) % cycle

    @property
    def armed(self):
        return self._timer < self.armed_seconds

    def catches(self, rect):
        return self.armed and self.rect.colliderect(rect)

    def draw(self, surface, camera=None):
        rect = camera.apply(self.rect) if camera is not None else self.rect
        color = self.armed_color if self.armed else self.safe_color
        pygame.draw.rect(surface, color, rect)
