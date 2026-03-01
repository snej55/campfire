import pygame, math, time

from .anim import Anim

class Pufferfish:
    def __init__(self, app, pos, animation):
        self.app = app
        self.origin = pygame.Vector2(pos)
        self.pos = pygame.Vector2(pos)
        self.anim = Anim(animation, 0.05)
    
    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, 16, 13)
    
    def update(self, dt, player):
        self.anim.update(dt)
        self.pos.y = self.origin.y + math.sin(time.time() * 2 + self.pos.x * 23987) * 6
    
    def draw(self, surf, scroll):
        self.anim.draw(surf, scroll, self.pos)
        