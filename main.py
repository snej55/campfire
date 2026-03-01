# Basic pygame template that runs on the web using pygbag (also still works on desktop).
# Setup:
# pip install pygame-ce pygbag
#
# Running (from root directory):
# pygbag .

import asyncio, pygame, time, sys, platform

from src.util import *
from src.tilemap import *
from src.player import *
from src.enemies import *
from src.smoke import *
from src.sparks import *

pygame.init()
pygame.mixer.init()

# ----------- GLOBALS ----------- #
# check if python is running through emscripten
WEB_PLATFORM = sys.platform == "emscripten"
if WEB_PLATFORM:
    # for document/canvas interaction
    import js  # type: ignore

    # keep pixelated look for pygbag
    platform.window.canvas.style.imageRendering = "pixelated"

# window dimensions and scaling
WIDTH, HEIGHT = 768, 768
SCALE = 4


class App:
    def __init__(self):
        # no need for separate scaling, pygbag scales canvas automatically
        self.display = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH // SCALE, HEIGHT // SCALE))
        self.active = True  # if tab is focused when running through web

        self.clock = pygame.time.Clock()

        # delta time
        self.dt = 1
        self.last_time = time.time() - 1 / 60

        self.assets = {
            "tiles/grass": load_tile_imgs("tiles/final_grass.png", TILE_SIZE),
            "tiles/underwater_grass": load_tile_imgs("tiles/underwater_grass.png", TILE_SIZE),
            "tiles/purple": load_tile_imgs("tiles/purple.png", TILE_SIZE),
            "tiles/large_decor": load_animation("tiles/large_decor.png", 48, 48, 7),
            "tiles/spikes": load_animation("tiles/spikes.png", 12, 12, 4),
            "player/run": load_animation("player/run.png", 8, 8, 10),
            "player/idle_1": load_animation("player/idle_1.png", 8, 8, 5),
            "player/idle_2": load_animation("player/idle_2.png", 8, 8, 8),
            "player/idle_3": load_animation("player/idle_3.png", 8, 8, 5),
            "player/idle_4": load_animation("player/idle_4.png", 8, 8, 8),
            "player/jump": load_animation("player/jump.png", 8, 8, 8),
            "player/land": load_animation("player/jump.png", 8, 8, 3),
            "background": load_image("background.png"),
            "player/bubble": load_animation("player/bubble.png", 12, 13, 2),
            "pufferfish": load_animation("pufferfish.png", 16, 13, 3),
            "nautilus": load_animation("nautilus.png", 28, 17, 6),
            "pin": load_image("pin.png"),
            "shell": load_image("shell.png"),
            "fire": load_animation("fire.png", 5, 5, 9),
            "light": load_image("light.png"),
        }

        self.kickup_palette = load_palette(self.assets["pin"])
        self.kickup_palette.extend(load_palette(self.assets["shell"]))
        self.player_palette = load_palette(self.assets["player/run"][0])

        surf = pygame.Surface(self.assets["background"].get_size())
        surf.fill((0, 0, 0))
        surf.set_alpha(100)
        self.assets["background"].blit(surf, (0, 0))

        self.scroll = [0, 0]

        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/0.json")

        self.pufferfish = []
        for loc in self.tile_map.tile_map.copy():
            if self.tile_map.tile_map[loc]["type"] == "pufferfish":
                self.pufferfish.append(
                    Pufferfish(
                        self,
                        [self.tile_map.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map.tile_map[loc]["pos"][1] * TILE_SIZE],
                        self.assets["pufferfish"],
                    )
                )
                del self.tile_map.tile_map[loc]
        self.pins = []

        self.nautilus = []
        for loc in self.tile_map.tile_map.copy():
            if self.tile_map.tile_map[loc]["type"] == "nautilus":
                self.nautilus.append(
                    Nautilus(
                        self,
                        [self.tile_map.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map.tile_map[loc]["pos"][1] * TILE_SIZE],
                        self.assets["nautilus"],
                    )
                )
                del self.tile_map.tile_map[loc]
        self.shells = []
        self.light = self.assets["light"]

        self.kickup = []
        self.sparks = []
        self.smoke = []
        self.fire = []
        self.shockwaves = []

        self.player = Player(self, [6, 7], [20, 15])
        self.screen_shake = 0

    def update_fire(self, render_scroll):
        # [pos, frame]
        for i, f in sorted(enumerate(self.fire), reverse=True):
            f[2] -= 1 * self.dt
            if f[2] < 0:
                f[0][1] -= 4 * self.dt
                f[1] += 0.9 * self.dt
                if f[1] >= len(self.assets["fire"]):
                    self.fire.pop(i)
                else:
                    self.screen.blit(
                        self.assets["fire"][math.floor(f[1])], (f[0][0] - render_scroll[0] - 2.5, f[0][1] - render_scroll[1] - 2.5)
                    )

    def update_kickup(self, render_scroll):
        # particle: [pos, vel, size, color]
        for i, p in sorted(enumerate(self.kickup), reverse=True):
            p[0][0] += p[1][0] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[0][0] -= p[1][0] * self.dt
                p[1][0] *= -0.4
                p[1][1] *= 0.999

            p[1][1] += 0.1 * self.dt
            p[0][1] += p[1][1] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[0][1] -= p[1][1] * self.dt
                p[1][1] *= -0.4
                p[1][0] *= 0.999

            p[2] -= 0.1 * self.dt
            if p[2] <= 0:
                self.kickup.pop(i)
            else:
                color = pygame.Color(p[3][0], p[3][1], p[3][2], int(p[2] / 100 * 255))
                self.screen.set_at((int(p[0][0] - render_scroll[0]), int(p[0][1] - render_scroll[1])), color)

    def update_sparks(self, render_scroll):
        for i, spark in sorted(enumerate(self.sparks), reverse=True):
            spark.update(self.dt)
            if spark.speed >= 0:
                spark.draw(self.screen, render_scroll)
            else:
                self.sparks.pop(i)

    # put all the game stuff here
    def update(self):
        # update delta time
        self.dt = (time.time() - self.last_time) * 60
        self.dt = min(self.dt, 3)
        self.last_time = time.time()

        self.player.update(self.dt, self.tile_map)

        if self.player.ad > self.player.death_time:
            self.scroll[0] += (self.player.get_rect().centerx - self.screen.get_width() * 0.5 - self.scroll[0]) / 30 * self.dt
            self.scroll[1] += (self.player.get_rect().centery - self.screen.get_height() * 0.5 - self.scroll[1]) / 30 * self.dt

        for fish in self.pufferfish:
            fish.update(self.dt, self.player)
        for fish in self.nautilus:
            fish.update(self.dt, self.player)

        # do the rendering
        screen_shake_offset = (
            random.random() * self.screen_shake - self.screen_shake / 2,
            random.random() * self.screen_shake - self.screen_shake / 2,
        )
        render_scroll = (int(self.scroll[0] + screen_shake_offset[0]), int(self.scroll[1] + screen_shake_offset[1]))
        self.screen_shake = max(0, self.screen_shake - 1 * self.dt)
        self.screen.blit(pygame.transform.scale(self.assets["background"], self.screen.get_size()), (0, 0))
        for i, pin in sorted(enumerate(self.pins), reverse=True):
            pin.update(self.dt, self.tile_map)
            if pin.get_rect().colliderect(self.player.get_rect()):
                self.player.die()
                pin.kill = True
            if pin.kill:
                for _ in range(random.randint(5, 10)):
                    speed = random.random()
                    angle = math.pi * 2 * random.random()
                    self.kickup.append(
                        [
                            [pin.pos[0], pin.pos[1]],
                            [math.cos(angle) * speed, math.sin(angle) * speed],
                            random.random() + 9,
                            [255, 255, 255, 100],
                        ]
                    )
                for _ in range(random.randint(5, 10)):
                    speed = random.random() + 1
                    angle = pin.direction + math.pi + random.random() - 0.5
                    self.sparks.append(Spark(pin.pos.copy(), angle, speed, [255, 255, 255]))
                self.pins.pop(i)
            else:
                pin.draw(self.screen, render_scroll)
        for i, shell in sorted(enumerate(self.shells), reverse=True):
            shell.update(self.dt, self.tile_map)
            if shell.get_rect().colliderect(self.player.get_rect()):
                self.player.die()
                shell.kill = True
            if shell.kill:
                self.shells.pop(i)
            else:
                shell.draw(self.screen, render_scroll)

        self.tile_map.draw_decor(self.screen, render_scroll)
        if self.player.ad > self.player.death_time:
            self.player.draw(self.screen, render_scroll)
            # self.screen.blit(self.light, (self.player.get_rect().centerx - self.light.get_width() * 0.5 - render_scroll[0], self.player.get_rect().centery - self.light.get_height() * 0.5 - render_scroll[1]), area=None, special_flags=pygame.BLEND_RGBA_SUB)
        for fish in self.pufferfish:
            if fish.get_rect().colliderect(self.player.get_rect()):
                self.player.die()
            fish.draw(self.screen, render_scroll)
        for fish in self.nautilus:
            if fish.get_rect().colliderect(self.player.get_rect()):
                self.player.die()
            fish.draw(self.screen, render_scroll)
        self.tile_map.draw(self.screen, render_scroll)

        self.update_kickup(render_scroll)
        self.update_sparks(render_scroll)
        for shockwave in self.shockwaves.copy():
            pygame.draw.circle(
                self.screen,
                shockwave[2],
                (shockwave[0][0] - render_scroll[0], shockwave[0][1] - render_scroll[1]),
                min(shockwave[4] * 1.5, shockwave[1] * 1.5),
                int(math.ceil(max(1, shockwave[4] - shockwave[1]) / 4)),
            )
            if shockwave[1] - 1 > shockwave[4]:
                if type(shockwave[2]) == tuple:
                    shockwave[2] = list(shockwave[2])
                shockwave[2][0] = max(shockwave[2][0] - 50 * self.dt, 0)
                shockwave[2][1] = max(shockwave[2][1] - 50 * self.dt, 0)
                shockwave[2][2] = max(shockwave[2][2] - 50 * self.dt, 0)
                if shockwave[2][2] == 0 and shockwave[2][1] == 0 and shockwave[2][0] == 0:
                    self.shockwaves.remove(shockwave)
            else:
                shockwave[1] += (
                    max(0, min(20, 150 * (shockwave[4] * 0.01) / max(0.0001, shockwave[1] * 2))) * self.dt * shockwave[3]
                )
        for i, bit in sorted(enumerate(self.smoke), reverse=True):
            bit.update(self.dt)
            if bit.timer > SMOKE_DELAY // FADE:
                self.smoke.pop(i)
            bit.draw(self.screen, render_scroll)
        self.update_fire(render_scroll)

        self.player.water = False
        if self.active:
            for water in self.tile_map.water:
                water.update(self.screen, self.player, render_scroll, self.dt)
                if water.get_rect().colliderect(self.player.get_rect()):
                    self.player.water = True

    # asynchronous main loop to run in browser
    async def run(self):
        while True:
            # update event loop
            for event in pygame.event.get():
                # just return to quit
                if event.type == pygame.QUIT:
                    return
                # handle window resizing on desktop
                if event.type == pygame.WINDOWRESIZED:
                    self.screen = pygame.Surface((self.display.get_width() // SCALE, self.display.get_height() // SCALE))
                    # self.alpha = pygame.Surface(self.screen.get_size())
                    # self.alpha.fill((0, 0, 0))
                if event.type == pygame.KEYDOWN:
                    if event.key in {pygame.K_UP, pygame.K_w, pygame.K_SPACE}:
                        self.player.controls["up"] = True
                        self.player.jumping = 0
                    elif event.key in {pygame.K_DOWN, pygame.K_s}:
                        self.player.controls["down"] = True
                    elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                        self.player.controls["right"] = True
                    elif event.key in {pygame.K_LEFT, pygame.K_a}:
                        self.player.controls["left"] = True
                if event.type == pygame.KEYUP:
                    if event.key in {pygame.K_UP, pygame.K_w, pygame.K_SPACE}:
                        self.player.controls["up"] = False
                    elif event.key in {pygame.K_DOWN, pygame.K_s}:
                        self.player.controls["down"] = False
                    elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                        self.player.controls["right"] = False
                    elif event.key in {pygame.K_LEFT, pygame.K_a}:
                        self.player.controls["left"] = False
            # update game
            self.update()

            # check if tab is focused if running through web (avoid messing up dt and stuff)
            if WEB_PLATFORM:
                self.active = not js.document.hidden

            # check if page is active
            if self.active:
                # don't render screen dimensions if on web
                if WEB_PLATFORM:
                    pygame.display.set_caption(f"FPS: {self.clock.get_fps() :.1f}")
                else:
                    pygame.display.set_caption(
                        f"FPS: {self.clock.get_fps() :.1f} Display: {self.screen.get_width()} * {self.screen.get_height()}"
                    )

                # scale display (don't use scale2x, which uses pixel nearest algorithm and ruins pixel art)
                self.display.blit(pygame.transform.scale(self.screen, self.display.get_size()), (0, 0))
                pygame.display.flip()
            else:
                # if browser tab isn't focused, don't update the display and just change the caption to 'IDLE'
                pygame.display.set_caption("IDLE")

            await asyncio.sleep(0)  # IMPORTANT: keep this for pygbag to work!
            self.clock.tick(60)  # don't really need more than 60 fps


# run App() asynchronously so it works with pygbag
async def main():
    app = App()
    await app.run()


# start
asyncio.run(main())
