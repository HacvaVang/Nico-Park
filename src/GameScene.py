# GameScene.py
import cocos
from cocos.layer import ScrollingManager, ScrollableLayer
from cocos.sprite import Sprite
from cocos.tiles import load, RectMapLayer
from cocos.scene import Scene
import pyglet.window.key as key


class GameScene(ScrollableLayer):
    is_event_handler = True

    def __init__(self, scroller):
        super(GameScene, self).__init__()

        self.scroller = scroller  # nhận scroller qua constructor

        # Physics
        self.velocity = [0, 0]
        self.speed = 200
        self.gravity = -500
        self.jump_speed = 300
        self.on_ground = False

        # Tạo Player
        self.player = Sprite("assets/sprite/Blue1.png")
        self.player.position = (100, 100)
        self.add(self.player, z=1)

        self.schedule(self.update)

    def update(self, dt):
        self.velocity[1] += self.gravity * dt

        x, y = self.player.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt

        if new_y <= 100:
            new_y = 100
            self.velocity[1] = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self.player.position = (new_x, new_y)

        # Camera follow
        self.scroller.set_focus(new_x, new_y)

    def on_key_press(self, k, modifiers):
        if k == key.LEFT:
            self.velocity[0] = -self.speed
        elif k == key.RIGHT:
            self.velocity[0] = self.speed
        elif k == key.SPACE:
            if self.on_ground:
                self.velocity[1] = self.jump_speed

    def on_key_release(self, k, modifiers):
        if k in (key.LEFT, key.RIGHT):
            self.velocity[0] = 0


    # Trong update(self, dt)
    def update(self, dt):
        self.velocity[1] += self.gravity * dt
        x, y = self.player.position

        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt

        # Tạm thời bỏ giới hạn 100 để xem nhân vật rơi đi đâu
        # Nếu y quá thấp so với map (576), bạn sẽ không thấy map
        if new_y < 0:
            new_y = 0
            self.velocity[1] = 0

        self.player.position = (new_x, new_y)

        # Ép camera nhìn vào vị trí nhân vật
        self.scroller.set_focus(new_x, new_y)


def create_game_scene():
    scroller = ScrollingManager()

    # Load map
    tile_map = load("assets/map.tmx")

    # Thêm TẤT CẢ các layer tìm thấy
    for name, layer in tile_map.find(RectMapLayer):
        print(f"Rendering layer: {name}")
        scroller.add(layer, z=0)

    game_layer = GameScene(scroller)
    # Thử đặt nhân vật ở giữa bản đồ để dễ tìm camera
    game_layer.player.position = (400, 1000)

    scroller.add(game_layer, z=1)
    return Scene(scroller)