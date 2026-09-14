import pygame


class Player:
    def __init__(self, x, y, speed, color):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x,y,30,30)
        self.color = color
        self.skins = []
        self.current_skin_index = 0 
        self.speed = speed

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
        pygame.draw.rect(screen, self.color, rect)
    
    # Character Customization
    def draw_static(self):
        pass
    
    def draw_nametag(self):
        pass
    
    def next_skin(self):
        pass
    
    def previous_skin(self):
        pass
    
class Button:
    def __init__(self, x, y, width, height, text, player=None):
        pass