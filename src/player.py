import pygame


class Player:
    def __init__(self, app, dimensions, start_pos):
        self.app = app
        self.dimensions = pygame.Vector2(dimensions)
        self.start_pos = start_pos
        self.pos = pygame.Vector2(start_pos)

        self.falling = 30
        self.jumping = 30

        self.controls = {"up": False, "down": False, "right": False, "left": False}

        self.movement = pygame.Vector2(0, 0)

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)

    def update(self, dt, tile_map):
        self.falling += dt
        self.jumping += dt

        speed = 1.6
        if self.controls["right"]:
            self.movement.x += speed * dt
        if self.controls["left"]:
            self.movement.x -= speed * dt
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

    def draw(self, surf, scroll):
        pygame.draw.rect(surf, (255, 0, 0), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))
