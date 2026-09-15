import pygame
from config import BLACK, GRAY, BLUE, RED, SPRINT_MULTIPLIER, SPRINT_DURATION, SPRINT_COOLDOWN


class Player:
    def __init__(self, x, y, speed, color, font, skin_dir="PushNRun!/assets/players",
                 can_push=False, can_sprint=False):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 30, 30)
        self.color = color
        self.skins = []
        self.current_skin_index = 0
        self.base_speed = speed   # unmodified speed; self.speed can be scaled by modifiers
        self.speed = speed
        self.font = font
        self.skin_dir = skin_dir
        self._sprite_cache = {}  # avoids re-reading the image file from disk every frame

        self.can_push = can_push
        self.can_sprint = can_sprint

        # Velocity-based movement: at slide_factor=1.0 (default) velocity
        # snaps straight to the input direction every frame, identical to
        # the old direct dx/dy movement. Lower values (set by the
        # "Slippery" modifier) blend toward it instead, giving an icy feel.
        self.velocity = pygame.Vector2(0, 0)
        self.slide_factor = 1.0

        # Sprint state (runner only; no-ops for a player with can_sprint=False)
        self.sprint_multiplier = SPRINT_MULTIPLIER
        self.sprinting = False
        self._sprint_timer = 0.0
        self._sprint_cooldown_timer = 0.0

    def update(self, dt):
        """Per-frame timer bookkeeping — call once per frame regardless of movement."""
        if self.sprinting:
            self._sprint_timer -= dt
            if self._sprint_timer <= 0:
                self.sprinting = False
                self._sprint_cooldown_timer = SPRINT_COOLDOWN
        elif self._sprint_cooldown_timer > 0:
            self._sprint_cooldown_timer -= dt

    def try_sprint(self):
        if self.can_sprint and not self.sprinting and self._sprint_cooldown_timer <= 0:
            self.sprinting = True
            self._sprint_timer = SPRINT_DURATION

    def move(self, controls, keys, walls=None, boxes=None):
        walls = walls or []
        boxes = boxes or []

        if controls == 1:
            input_dx = keys[pygame.K_d] - keys[pygame.K_a]
            input_dy = keys[pygame.K_s] - keys[pygame.K_w]
        elif controls == 2:
            input_dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            input_dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        else:
            raise Exception("No Control Type Selected")

        speed = self.speed * (self.sprint_multiplier if self.sprinting else 1.0)
        target_vx, target_vy = input_dx * speed, input_dy * speed

        # Blend current velocity toward the target instead of snapping to it.
        self.velocity.x += (target_vx - self.velocity.x) * self.slide_factor
        self.velocity.y += (target_vy - self.velocity.y) * self.slide_factor
        dx, dy = round(self.velocity.x), round(self.velocity.y)

        # Boxes are solid obstacles to anyone who can't push them; only a
        # can_push player gets the special push-resolution logic below.
        static_blockers = list(walls)
        if not self.can_push:
            static_blockers += [box.rect for box in boxes]

        # --- X axis ---
        self.rect.x += dx
        if self.can_push:
            for box in boxes:
                if self.rect.colliderect(box.rect):
                    box.rect.x += dx
                    box_blocked = any(box.rect.colliderect(w) for w in walls) or any(
                        other is not box and box.rect.colliderect(other.rect) for other in boxes
                    )
                    if box_blocked:
                        box.rect.x -= dx
                        self.rect.x -= dx
        for blocker in static_blockers:
            if self.rect.colliderect(blocker):
                if dx > 0:
                    self.rect.right = blocker.left
                elif dx < 0:
                    self.rect.left = blocker.right

        # --- Y axis ---
        self.rect.y += dy
        if self.can_push:
            for box in boxes:
                if self.rect.colliderect(box.rect):
                    box.rect.y += dy
                    box_blocked = any(box.rect.colliderect(w) for w in walls) or any(
                        other is not box and box.rect.colliderect(other.rect) for other in boxes
                    )
                    if box_blocked:
                        box.rect.y -= dy
                        self.rect.y -= dy
        for blocker in static_blockers:
            if self.rect.colliderect(blocker):
                if dy > 0:
                    self.rect.bottom = blocker.top
                elif dy < 0:
                    self.rect.top = blocker.bottom

    def _load_sprite(self, skin_name, size):
        """
        Loads and caches a skin image the first time it's needed. A
        missing or unreadable file falls back to None (draw() then
        just uses the plain color rect) instead of crashing the game.
        """
        cache_key = (skin_name, size)
        if cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]

        path = f"{self.skin_dir}/{skin_name}.png"
        try:
            sprite = pygame.image.load(path).convert_alpha()
            sprite = pygame.transform.scale(sprite, size)
        except (pygame.error, FileNotFoundError):
            print(f"[Player] couldn't load skin '{skin_name}' from {path}; using color fallback.")
            sprite = None

        self._sprite_cache[cache_key] = sprite
        return sprite

    def _current_sprite(self, size):
        if not self.skins:
            return None
        return self._load_sprite(self.skins[self.current_skin_index], size)

    def draw(self, screen, camera=None):
        rect = camera.apply(self.rect) if camera is not None else self.rect
        sprite = self._current_sprite((30, 30))
        if sprite is not None:
            screen.blit(sprite, rect)
        else:
            pygame.draw.rect(screen, self.color, rect)
            if self.sprinting:
                pygame.draw.rect(screen, (255, 255, 255), rect, 2)  # quick visual sprint indicator

    # Character Customization
    def draw_static(self, screen, x, y):
        """Draw this player's current skin at an arbitrary (x, y), e.g. on a menu screen."""
        temp_rect = pygame.Rect(x, y, 50, 50)
        sprite = self._current_sprite((50, 50))
        if sprite is not None:
            screen.blit(sprite, temp_rect)
        else:
            pygame.draw.rect(screen, self.color, temp_rect)

    def draw_nametag(self, screen):
        name = "Runner" if self.color == BLUE else "Pusher"
        text = self.font.render(name, True, (BLUE if name == "Runner" else RED))
        text_rect = text.get_rect(center=(self.rect.centerx, self.rect.top - 10))
        screen.blit(text, text_rect)

    def next_skin(self):
        if self.skins:
            self.current_skin_index = (self.current_skin_index + 1) % len(self.skins)

    def previous_skin(self):
        if self.skins:
            self.current_skin_index = (self.current_skin_index - 1) % len(self.skins)


class Button:
    def __init__(self, x, y, width, height, text, font, player=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.player = player

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

        if self.player and self.player.skins:
            display_text = f"{self.text}: {self.player.skins[self.player.current_skin_index]}"
        else:
            display_text = self.text

        text_surf = self.font.render(display_text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
