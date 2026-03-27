# GameScene.py
import cocos
from cocos.layer import ScrollingManager, ScrollableLayer
from cocos.sprite import Sprite
from cocos.tiles import load, RectMapLayer, TmxObjectLayer
from cocos.scene import Scene
import pyglet.window.key as key
from .Character import Character
from .Button import TypeButton, Button
from .MapManager import MapManager
from .Obstacle import Obstacle
from .DebugLayer import DebugLayer



class GameScene(ScrollableLayer):
    is_event_handler = True

    def __init__(self, scroller, map_manager: MapManager = None):
        super(GameScene, self).__init__()

        self.scroller = scroller

        # Allow map_manager to be injected (avoids double-loading in create_game_scene)
        if map_manager is None:
            map_manager = MapManager("assets/map.tmx")
        self.map_manager = map_manager

        # Tạo Player
        self.player = Character("assets/sprite/Blue1.png", map_manager.get_land_collisions(), map_manager.get_starting_position())
        self.add(self.player, z=1)
        
        # Tạo Button
        self.buttons = list()
        self.buttons.append(Button(map_manager.get_object_position_list("Button")[0], TypeButton.IncreaseSize))
        self.buttons.append(Button(map_manager.get_object_position_list("Button")[1], TypeButton.DecreaseSize))
        self.buttons.append(Button(map_manager.get_object_position_list("Button")[2], TypeButton.Neutral))
        self.buttons.append(Button(map_manager.get_object_position_list("Button")[3], TypeButton.Neutral))

        self.add(self.buttons[0], z=1)
        self.add(self.buttons[1], z=1)
        self.add(self.buttons[2], z=1)
        self.add(self.buttons[3], z=1)

        # Tạo Obstacle (Door) — linked to buttons[2], reacts to its state each frame
        obstacle_positions = map_manager.get_object_position_list("Obstacle")
        self.obstacles = []
        if obstacle_positions:
            for pos in obstacle_positions:
                obs = Obstacle("assets/map_object/Door0.png", pos, self.buttons[2])
                self.obstacles.append(obs)
                self.add(obs, z=1)

        # Debug overlay (child of this layer — shares our coordinate space exactly)
        self.debug_layer = DebugLayer(map_manager, self)
        self.add(self.debug_layer, z=100)

        self.schedule(self.update)

    def update(self, dt):
        # Camera follow
        self.scroller.set_focus(self.player.position[0], self.player.position[1])
        
        # Kiểm tra va chạm với button
        for button in self.buttons:
            if button.check_interaction(self.player):
                self.player.apply_button_effect(button)

        # Đẩy character ra khỏi obstacle nếu đang va chạm
        for obs in self.obstacles:
            obs.push_character_out(self.player)

    def on_key_press(self, k, modifiers):
        self.player.handle_key_press(k, modifiers)

    def on_key_release(self, k, modifiers):
        self.player.handle_key_release(k, modifiers)



def create_game_scene(findpath : str = "assets/map.tmx"):
    scroller = ScrollingManager()

    tile_map = load(findpath)
    for name, layer in tile_map.find(RectMapLayer):
        print(f"Rendering layer: {name}")
        scroller.add(layer, z=0)

    # Single MapManager shared between GameScene and DebugLayer
    map_manager = MapManager(findpath)
    game_layer  = GameScene(scroller, map_manager)
    scroller.add(game_layer, z=1)

    return Scene(scroller)