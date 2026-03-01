import pygame, math, time, random

from .anim import Anim


class Pin:
    def __init__(self, pos, surf, direction, speed, delay=0):
        self.surf = surf
        self.pos = pygame.Vector2(pos)
        self.direction = direction
        self.speed = speed
        self.kill = False
        self.timer = 0
        self.delay = delay

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.surf.get_width(), self.surf.get_height())

    def update(self, dt, tile_map):
        self.timer += dt
        if self.timer > self.delay:
            self.pos.x += math.cos(self.direction) * self.speed * dt
            if tile_map.solid_check(self.pos):
                self.kill = True
                return
            self.pos.y += math.sin(self.direction) * self.speed * dt
            if tile_map.solid_check(self.pos):
                return

        if self.timer > 1200 + self.delay:
            self.kill = True

    def draw(self, surf, scroll):
        if self.timer > self.delay:
            rot_surf = pygame.transform.rotate(self.surf, -math.degrees(self.direction))
            surf.blit(
                rot_surf,
                (
                    self.pos.x + int(self.surf.get_width() / 2) - int(rot_surf.get_width() / 2) - scroll[0],
                    self.pos.y + int(self.surf.get_height() / 2) - int(rot_surf.get_height() / 2) - scroll[1],
                ),
            )


class Pufferfish:
    def __init__(self, app, pos, animation):
        self.app = app
        self.origin = pygame.Vector2(pos)
        self.pos = pygame.Vector2(pos)
        self.anim = Anim(animation, 0.05)
        self.shot = random.random() * 210

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, 16, 13)

    def shoot(self, amount=6):
        for a in range(amount):
            angle = math.radians(360 / amount * a) + random.random() * math.pi
            self.app.pins.append(
                Pin(
                    [self.get_rect().centerx + math.cos(angle) * 8, self.get_rect().centery + math.sin(angle) * 8],
                    self.app.assets["pin"],
                    angle,
                    1,
                    a * 60 / amount,
                )
            )

    def update(self, dt, player):
        self.anim.update(dt)
        self.pos.y = self.origin.y + math.sin(time.time() * 2 + self.pos.x * 23987) * 6

        self.shot += dt
        if self.shot > 210:
            if player.water:
                self.shoot()
            self.shot = random.random() * 30

    def draw(self, surf, scroll):
        self.anim.draw(surf, scroll, self.pos)


class Shell:
    def __init__(self, pos, surf, direction, speed, delay=0):
        self.surf = surf
        self.pos = pygame.Vector2(pos)
        self.direction = direction
        self.speed = speed
        self.kill = False
        self.timer = 0
        self.delay = delay
        self.angle = 0

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.surf.get_width(), self.surf.get_height())

    def update(self, dt, tile_map):
        self.angle += dt * 10
        self.timer += dt
        if self.timer > self.delay:
            movement = [math.cos(self.angle) * self.speed, math.sin(self.angle) * self.speed]
            movement[1] = min(8, movement[1] + 0.3 * dt)
            movement[0] += (movement[0] * 0.95 - movement[0]) * dt
            self.pos.x += math.cos(self.direction) * self.speed * dt
            if tile_map.solid_check(self.pos):
                self.kill = True
                return
            self.pos.y += math.sin(self.direction) * self.speed * dt
            if tile_map.solid_check(self.pos):
                return

        if self.timer > 1200 + self.delay:
            self.kill = True

    def draw(self, surf, scroll):
        if self.timer > self.delay:
            rot_surf = pygame.transform.rotate(self.surf, self.angle)
            surf.blit(
                rot_surf,
                (
                    self.pos.x + int(self.surf.get_width() / 2) - int(rot_surf.get_width() / 2) - scroll[0],
                    self.pos.y + int(self.surf.get_height() / 2) - int(rot_surf.get_height() / 2) - scroll[1],
                ),
            )


class Nautilus:
    def __init__(self, app, pos, animation):
        self.app = app
        self.origin = pygame.Vector2(pos)
        self.pos = pygame.Vector2(pos)
        self.anim = Anim(animation, 0.05)
        self.shot = random.random() * 210

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, 16, 13)

    def shoot(self, amount=6):
        for a in range(amount):
            angle = math.radians(360 / amount * a) + random.random() * math.pi
            self.app.shells.append(
                Shell(
                    [self.get_rect().centerx + math.cos(angle) * 8, self.get_rect().centery + math.sin(angle) * 8],
                    self.app.assets["shell"],
                    angle,
                    1.5,
                    a * 60 / amount,
                )
            )
            self.app.assets["fall"].play()

    def update(self, dt, player):
        self.anim.update(dt)
        self.pos.y = self.origin.y + math.sin(time.time() * 2 + self.pos.x * 23987) * 6

        self.shot += dt
        if self.shot > 210:
            if player.water:
                self.shoot()
            self.shot = random.random() * 30

    def draw(self, surf, scroll):
        self.anim.draw(surf, scroll, self.pos)
