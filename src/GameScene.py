# GameScene.py
import cocos
from cocos.layer import ScrollingManager, ScrollableLayer
from cocos.sprite import Sprite
from cocos.tiles import load, RectMapLayer, TmxObjectLayer
from cocos.scene import Scene
import pyglet.window.key as key
from .Character import Character



class GameScene(ScrollableLayer):
    is_event_handler = True

    def __init__(self, scroller):
        super(GameScene, self).__init__()

        self.scroller = scroller  # nhận scroller qua constructor

        # Tạo Player
        self.player = Character("assets/sprite/Blue1.png", create_collision_box(), get_starting_position())
        self.add(self.player, z=1)

        self.schedule(self.update)

    def update(self, dt):
        # Camera follow
        self.scroller.set_focus(self.player.position[0], self.player.position[1])

    def on_key_press(self, k, modifiers):
        self.player.handle_key_press(k, modifiers)

    def on_key_release(self, k, modifiers):
        self.player.handle_key_release(k, modifiers)

def create_collision_box(findpath : str = "assets/map.tmx"):
    collision_boxes = list()

    tile_map = load(findpath)
    for _, obj_layer in tile_map.find(TmxObjectLayer):
        if (getattr(obj_layer, "name", "") or "").lower() == "land collision":
            for obj in getattr(obj_layer, "objects", []):
                x = getattr(obj, "x", 0)
                y = getattr(obj, "y", 0)
                w = getattr(obj, "width", 0)
                h = getattr(obj, "height", 0)
                collision_boxes.append(cocos.rect.Rect(x, y, w, h))
    return collision_boxes

def get_starting_position(findpath : str = "assets/map.tmx"):
    tile_map = load(findpath)
    for _, obj_layer in tile_map.find(TmxObjectLayer):
        if (getattr(obj_layer, "name", "") or "").lower() == "starting position":
            for obj in getattr(obj_layer, "objects", []):
                print(obj.x, obj.y)
                return obj.x, obj.y
    return 0, 0

def create_game_scene(findpath : str = "assets/map.tmx"):
    scroller = ScrollingManager()

    tile_map = load(findpath)

    for name, layer in tile_map.find(RectMapLayer):
        print(f"Rendering layer: {name}")
        scroller.add(layer, z=0)
    

    game_layer = GameScene(scroller)
    game_layer.player.position = (400, 1000)

    scroller.add(game_layer, z=1)
    return Scene(scroller)