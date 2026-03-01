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
WIDTH, HEIGHT = 640, 480
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
            "player/run": load_animation("player/run.png", 8, 8, 10),
            "player/idle_1": load_animation("player/idle_1.png", 8, 8, 5),
            "player/idle_2": load_animation("player/idle_2.png", 8, 8, 8),
            "player/idle_3": load_animation("player/idle_3.png", 8, 8, 5),
            "player/idle_4": load_animation("player/idle_4.png", 8, 8, 8),
            "player/jump": load_animation("player/jump.png", 8, 8, 8),
            "player/land": load_animation("player/jump.png", 8, 8, 3),
        }

        self.scroll = [0, 0]

        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/0.json")

        self.player = Player(self, [6, 7], [20, 15])

    # put all the game stuff here
    def update(self):
        # update delta time
        self.dt = (time.time() - self.last_time) * 60
        self.dt = min(self.dt, 3)
        self.last_time = time.time()

        self.player.update(self.dt, self.tile_map)

        self.scroll[0] += (self.player.get_rect().centerx - self.screen.get_width() * 0.5 - self.scroll[0]) / 30 * self.dt
        self.scroll[1] += (self.player.get_rect().centery - self.screen.get_height() * 0.5 - self.scroll[1]) / 30 * self.dt

        # do the rendering
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        self.screen.fill((0, 0, 0))

        self.player.draw(self.screen, render_scroll)
        self.tile_map.draw(self.screen, render_scroll)

        if self.active:
            for water in self.tile_map.water:
                water.update(self.screen, self.player, render_scroll, self.dt)

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
