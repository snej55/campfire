import pygame, math

class Anim:
    def __init__(self, animation, speed, looping=True):
        self.animation = animation
        self.speed = speed
        self.looping = looping
        self.finished = False
        self.frame = 0
        self.step = 0
        self.flip = False

    def reset(self):
        self.finished = False
        self.frame = 0
        self.step = 0

    def update(self, dt):
        self.frame += self.speed * dt
        self.step = math.floor(self.frame) % len(self.animation)
        if not self.looping:
            if self.frame >= len(self.animation):
                self.finished = True
                self.step = len(self.animation) - 1

    def draw(self, surf, scroll, pos):
        surf.blit(pygame.transform.flip(self.animation[self.step], self.flip, False), (pos[0] - scroll[0], pos[1] - scroll[1]))