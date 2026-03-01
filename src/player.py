import pygame, math, random

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

class Player:
    def __init__(self, app, dimensions, start_pos):
        self.app = app
        self.dimensions = pygame.Vector2(dimensions)
        self.start_pos = start_pos
        self.pos = pygame.Vector2(start_pos)

        self.falling = 30
        self.grounded = 0
        self.jumping = 30

        self.controls = {"up": False, "down": False, "right": False, "left": False}

        self.movement = pygame.Vector2(0, 0)

        self.run = Anim(self.app.assets["player/run"], 0.2)
        self.idles = [Anim(self.app.assets["player/idle_1"], 0.15, False), Anim(self.app.assets["player/idle_1"], 0.15, False), Anim(self.app.assets["player/idle_2"], 0.15, False), Anim(self.app.assets["player/idle_3"], 0.15, False), Anim(self.app.assets["player/idle_4"], 0.15, False)]
        self.idle_index = 0
        self.jump = Anim(self.app.assets["player/jump"], 0.2, False)
        self.land = Anim(self.app.assets["player/land"], 0.2, False)
        self.anim = None
        self.flip = False

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)

    def update(self, dt, tile_map):
        self.falling += dt
        self.jumping += dt
        self.grounded += dt

        speed = 1.6
        if self.controls["right"]:
            self.movement.x += speed * dt
            self.flip = False
        if self.controls["left"]:
            self.movement.x -= speed * dt
            self.flip = True
        self.movement.x += (self.movement.x * 0.6 - self.movement.x) * dt

        self.movement.y += 0.3 * dt

        if self.falling < 5:
            if self.jumping < 15:
                self.movement.y = -4
                self.falling = 6
                self.jumping = 30

        fm = pygame.Vector2(self.movement.x * dt, self.movement.y * dt)

        self.pos.x += fm.x
        r = self.get_rect()
        for rect in tile_map.physics_rects_around(r.center):
            if r.colliderect(rect):
                if fm.x > 0:
                    r.right = rect.left
                if fm.x < 0:
                    r.left = rect.right
                self.pos.x = r.x
                self.movement.x = 0

        self.pos.y += fm.y
        r = self.get_rect()
        for rect in tile_map.physics_rects_around(r.center):
            if r.colliderect(rect):
                if fm.y >= 0:
                    r.bottom = rect.top
                    self.falling = 0
                elif fm.y < 0:
                    r.top = rect.bottom
                self.movement.y = 0
                self.pos.y = r.y
        
        self.handle_animation(dt)
    
    def handle_animation(self, dt):
        if self.falling > 5:
            self.grounded = 0
            self.jump.update(dt)
            self.idles[self.idle_index].reset()
            self.run.reset()
            self.land.reset()
        elif self.grounded < len(self.land.animation) / self.land.speed:
            self.land.update(dt)
            self.jump.reset()
            self.run.reset()
            self.idles[self.idle_index].reset()
        elif self.controls["left"] or self.controls["right"]:
            self.run.update(dt)
            self.idles[self.idle_index].reset()
        else:
            self.idles[self.idle_index].update(dt)
            if self.idles[self.idle_index].finished:
                self.idles[self.idle_index].reset()
                self.idle_index = random.randint(0, len(self.idles) - 1)

    def draw(self, surf, scroll):
        anim = None
        if self.falling > 5:
            anim = self.jump
        elif self.grounded < len(self.land.animation) / self.land.speed:
            anim = self.land
        elif self.controls["left"] or self.controls["right"]:
            anim = self.run
        else:
            anim = self.idles[self.idle_index]
        anim.flip = self.flip
        anim.draw(surf, scroll, (self.pos.x - 1, self.pos.y - 1))
