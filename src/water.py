import pygame, math

class WaterSpring:
    def __init__(self, x, y, target_y, tension):
        self.x = x
        self.y = y
        self.target_y = target_y
        self.tension = tension
        self.vel = 0
    
    def update(self, others, dt):
        dh = self.target_y - ((self.y - others[0].y) + (self.y - others[1].y)) / 2 - self.y
        if abs(dh) < 0.01:
            self.y = self.target_y
        self.vel += (dh - self.vel) * dt * self.tension * 1.1
        self.y += self.vel / 2 * dt
    
    def draw(self, surf, scroll):
        surf.set_at((int(self.x - scroll[0]), int(self.y - scroll[1])), (255, 255, 255))


class Water:
    def __init__(self, x, y, dimensions, spacing):
        self.x = x
        self.y = y
        self.dimensions, self.spacing = list(dimensions), spacing
        self.springs = [WaterSpring(self.x + x * spacing, self.y, self.y, 0.2) for x in range(math.ceil(dimensions[0] / spacing) + 1)]
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.dimensions[0], self.dimensions[1])
    
    def update(self, surf, player, scroll, dt):
        points = []
        for i, spring in enumerate(self.springs):
            if player.rect().collidepoint((spring.x, spring.y)):    
                spring.vel += max(-3, min(3, player.movement[1] + -abs(player.movement[0]))) * dt * (abs(spring.target_y - spring.y) < 1.5)
            spring.update([self.springs[max(0, i - 1)], self.springs[min(i + 1, len(self.springs) - 1)]], dt)
            points.append((spring.x - scroll[0] - (i == len(self.springs) - 1), spring.y - scroll[1]))
        water_surf = pygame.Surface(surf.get_size())
        line = points.copy()
        points.append((self.x + self.dimensions[0] - scroll[0] - 1, self.y + self.dimensions[1] - scroll[1] - 1))
        points.append((self.x - scroll[0], self.y + self.dimensions[1] - scroll[1] - 1))
        pygame.draw.polygon(water_surf, (138, 184, 172), points)
        pygame.draw.lines(water_surf, (230, 215, 204), False, line, width=1)
        water_surf.convert()
        water_surf.set_colorkey((0, 0, 0))
        water_surf.set_alpha(150)
        surf.blit(water_surf, (0, 0))
        if player.rect().colliderect(self.get_rect()):
            player.falling = 0
