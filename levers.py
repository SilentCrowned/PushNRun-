"""
Lever + Gate pairs, Fireboy & Watergirl style: a Gate blocks a
passage in the maze until a player stands on its linked Lever. The
gate only stays open while someone is actually standing on the
lever — a pressure plate, not a one-time switch — so getting both
players through it generally means one holds the lever while the
other walks through, then they swap. That hold-to-open behavior is
what forces the two players to actually coordinate, rather than
each just soloing their own half of the maze.
"""

import pygame


class Lever:
    def __init__(self, x, y, size=26, color=(200, 200, 60)):
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (x, y)
        self.color = color
        self.active = False

    def update(self, player_rects):
        self.active = any(self.rect.colliderect(r) for r in player_rects)

    def draw(self, surface, camera=None):
        rect = camera.apply(self.rect) if camera is not None else self.rect
        color = (255, 230, 80) if self.active else self.color
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (60, 60, 20), rect, 2)


class Gate:
    """A wall segment that only blocks movement while its linked lever is inactive."""

    def __init__(self, rect, color=(140, 90, 200)):
        self.rect = rect
        self.color = color
        self.closed = True

    def update(self, lever):
        self.closed = not lever.active

    def draw(self, surface, camera=None):
        if not self.closed:
            return
        rect = camera.apply(self.rect) if camera is not None else self.rect
        pygame.draw.rect(surface, self.color, rect)
