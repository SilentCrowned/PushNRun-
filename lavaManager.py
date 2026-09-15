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
        self.level_y = -float(self.rise_amount)
        self._timer = 0.0

    def toggle(self):
        self.enabled = not self.enabled

    def reset(self):
        """Reset lava above the top of the world."""
        self.level_y = -float(self.rise_amount)
        self._timer = 0.0

    def update(self, dt):
        """Move the lava line downward over time."""
        if not self.enabled:
            return

        self._timer += dt

        if self._timer >= self.rise_interval:
            self._timer -= self.rise_interval
            self.level_y = min(float(self.world_height), self.level_y + self.rise_amount)

    @property
    def rect(self):
        y = int(self.level_y)
        return pygame.Rect(
            0,
            0,
            self.world_width,
            max(0, y)
        )

    def collides_with(self, rect):
        """True when the player enters the lava above the line."""
        return self.enabled and rect.colliderect(self.rect)

    def draw(self, surface, camera=None):
        if not self.enabled:
            return

        # Determine the top and bottom of the lava area
        top = 0
        bottom = int(self.level_y)

        # Create a rect that covers the entire area from top to the lava level
        lava_rect = pygame.Rect(
            0,
            top,
            self.world_width,
            bottom
        )

        # Apply camera if provided
        draw_rect = (
            camera.apply(lava_rect)
            if camera is not None
            else lava_rect
        )

        # Draw the lava covering the area from the top to level_y
        pygame.draw.rect(surface, self.color, draw_rect)