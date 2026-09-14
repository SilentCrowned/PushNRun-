import pygame
from config import BLACK, GRAY, BLUE, RED

class Player:
    def __init__(self, x, y, speed, color, font):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x,y,30,30)
        self.color = color
        self.skins = []
        self.current_skin_index = 0 
        self.speed = speed
        self.font = font

    def move(self, controls, keys, walls=None):
        if controls == 1:
            dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.speed
            dy = (keys[pygame.K_s] - keys[pygame.K_w]) * self.speed
        elif controls == 2:
            dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
            dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.speed
        else:
            raise Exception("No Control Type Selected")
        

        # Move and resolve X and Y separately so the player can slide
        # along a wall instead of getting fully stopped on contact
        # (e.g. still able to move up/down while pressed against a
        # wall to the side).
        self.rect.x += dx
        if walls:
            for wall in walls:
                if self.rect.colliderect(wall):
                    if dx > 0:
                        self.rect.right = wall.left
                    elif dx < 0:
                        self.rect.left = wall.right

        self.rect.y += dy
        if walls:
            for wall in walls:
                if self.rect.colliderect(wall):
                    if dy > 0:
                        self.rect.bottom = wall.top
                    elif dy < 0:
                        self.rect.top = wall.bottom

    def draw(self, screen, camera=None):
        rect = camera.apply(self.rect) if camera is not None else self.rect
        if self.skins:
            skin_path = f"PushNRun!/assets/players/{self.skins[self.current_skin_index]}.png"
            sprite = pygame.image.load(skin_path).convert_alpha()
            sprite = pygame.transform.scale(sprite, (30, 30))
            screen.blit(sprite, self.rect)
        else:
            pygame.draw.rect(screen, self.color, rect)
        
        
    
    # Character Customization
    def draw_static(self, screen, x, y):
        temp_rect = pygame.Rect(x, y, 50, 50)
        if self.skins:
            skin_path = f"PushNRun!/assets/players/{self.skins[self.current_skin_index]}.png"
            sprite = pygame.image.load(skin_path).convert_alpha()
            sprite = pygame.transform.scale(sprite, (50, 50))
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
    def __init__(self, x, y, width, height, text, player=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.player
    
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
        