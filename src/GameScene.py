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
from .Minion import Mob
from .Coin import Coin
from .Ship import Ship
from .Gun import Gun
from .Boss import Boss

import pyglet
pyglet.options['audio'] = ('ffmpeg', 'openal', 'pulse', 'directsound', 'silent')
DIE_DISTANCE =  -100




class SoundManager:
    player = None
    current_bgm_path = None

    @classmethod
    def get_player(cls):
        if cls.player is None:
            cls.player = pyglet.media.Player()
        return cls.player

    @classmethod
    def play_bgm(cls, path):
        try:
            if cls.current_bgm_path == path:
                return
            
            if cls.player is not None:
                cls.player.pause()
                cls.player.delete()
            
            cls.player = pyglet.media.Player()
            cls.current_bgm_path = path

            music = pyglet.media.load(path, streaming=True)
            cls.player.queue(music)
            cls.player.loop = True
            cls.player.play()
        except Exception as e:
            print(f"BGM Error: {e}")

    @classmethod
    def play_sfx(cls, path):
        try:
            effect = pyglet.media.load(path, streaming=False)
            effect.play()
        except Exception as e:
            pass

class GameScene(ScrollableLayer):
    is_event_handler = True

    def __init__(self, scroller, map_manager: MapManager = None):
        super(GameScene, self).__init__()
        self.scroller = scroller
        self.coins_collected = 0
        self.coins_required = 3
        self.door_opened = False
        obstacle_pos = map_manager.get_object_position_list("Obstacle")
        boss_positions = map_manager.get_object_position_list("AngryNeko")

        # Allow map_manager to be injected (avoids double-loading in create_game_scene)
        if map_manager is None:
            map_manager = MapManager("assets/map.tmx")
        self.map_manager = map_manager

        # Tạo Player
        self.player = Character(map_manager.get_land_collisions(), map_manager.get_starting_position())
        self.add(self.player, z=1)
        
        # Tạo Button
        self.buttons = list()
        status_list = [TypeButton.IncreaseSize, TypeButton.DecreaseSize, TypeButton.Neutral, TypeButton.Neutral, TypeButton.Prohibited, TypeButton.Prohibited]
        for i in range(len(status_list)):
            button = Button(map_manager.get_object_position_list("Button")[i], status_list[i])
            self.buttons.append(button)
            self.add(button, z=1)


        # Tạo Mob
        self.mobs = []
        for pos in map_manager.get_object_position_list("Mob"):
            mob = Mob(pos, collision_boxes=map_manager.get_land_collisions())
            mob.on_die = self.on_mob_die
            self.add(mob, z=1)
            self.mobs.append(mob)

        self.bosses = []
        for i, pos in enumerate(boss_positions):
            # Lấy trigger_x từ obstacle tương ứng nếu có
            trigger_x = obstacle_pos[i][0] if i < len(obstacle_pos) else pos[0]
            boss = Boss(pos, self)
            boss.trigger_x = trigger_x
            self.add(boss, z=1)
            self.bosses.append(boss)

        self.coins = []
        for pos in map_manager.get_object_position_list("Coin"):
            coin = Coin(pos)
            self.coins.append(coin)
            self.add(coin, z=1)

        self.guns = []
        for pos in map_manager.get_object_position_list("Gun"):
            gun = Gun(pos)
            self.guns.append(gun)
            self.add(gun, z=1)
        self.bullets = []
        # Spawn Ships from map
        self.ships = []
        for pos in map_manager.get_object_position_list("Ship"):
            ship = Ship(pos)
            self.ships.append(ship)
            self.add(ship, z=1)

        # Tạo Obstacle (Door) — linked to buttons[2], reacts to its state each frame
        obstacle_positions = map_manager.get_object_position_list("Obstacle")
        self.obstacles = []
        if obstacle_positions:
            for pos in obstacle_positions:
                obs = Obstacle(pos, self.buttons[2])
                self.obstacles.append(obs)
                self.add(obs, z=1)

        # Debug overlay (child of this layer — shares our coordinate space exactly)
        self.debug_layer = DebugLayer(map_manager, self)
        self.add(self.debug_layer, z=100)

        # Background music
        SoundManager.play_bgm('assets/sound/Hands.wav')

        # Currently piloted ship (None when on foot)
        self.active_ship: Ship = None

        self.schedule(self.update)

    def update(self, dt):
        # Camera follow
        self.scroller.set_focus(self.player.position[0], self.player.position[1])
        if self.player.has_gun and self.player.shoot_timer <= 0:
            bullet = self.player.shoot()
            if bullet:
                self.add(bullet, z=2)
                self.bullets.append(bullet)
                self.player.shoot_timer = self.player.shoot_cooldown
        # Kiểm tra va chạm với button
        for button in self.buttons:
            if button.check_interaction(self.player):
                self.player.apply_button_effect(button)

        self.check_bullet_mob_collision(self.mobs)

        # Đẩy character ra khỏi obstacle nếu đang va chạm
        for obs in self.obstacles:
            obs.push_character_out(self.player)
        if self.y >= DIE_DISTANCE and not self.player.is_die:
            self.player.die()
        self.player.check_stomp(self.mobs)
        self.mobs = [m for m in self.mobs if not m.is_die]
        self.check_coin_collect()
        self.coins = [c for c in self.coins if c.parent is not None]
        self.check_gun_collect()
        self.guns = [c for c in self.guns if c.parent is not None]
        self.bosses = [b for b in self.bosses if not b.is_die]

    def check_bullet_mob_collision(self, mobs):
        for mob in mobs[:]:
            for bullet in self.bullets[:]:
                if bullet.get_hitbox().intersects(mob.get_hitbox()):
                    bullet.dead = True
                    mob.take_damage(bullet.damage)


    def check_gun_collect(self):
        player_rect = self.player.get_leg_collision_rect()
        for gun in self.guns[:]:
            if not gun.collected and player_rect.intersects(gun.get_hitbox()):
                gun.collect()
                self.player.pick_up_gun(gun)
        player_rect = self.player.get_leg_collision_rect()
        for gun in self.guns[:]:
            if not gun.collected and player_rect.intersects(gun.get_hitbox()):
                gun.collect()
                self.player.pick_up_gun(gun)

    def check_coin_collect(self):
        player_rect = self.player.get_leg_collision_rect()
        for coin in self.coins[:]:
            if not coin.collected and player_rect.intersects(coin.get_hitbox()):
                coin.collect()
                self.coins_collected += 1

        player_rect = self.player.get_head_collision_rect()
        for coin in self.coins[:]:
            if not coin.collected and player_rect.intersects(coin.get_hitbox()):
                coin.collect()
                self.coins_collected += 1

        if not self.door_opened and self.coins_collected >= self.coins_required:
            self.open_door()

    def open_door(self):
        self.door_opened = True
        if self.obstacles:
            self.obstacles[0].open()  # Chỉ mở obstacle đầu tiên
        print(f"Door opened! {self.coins_collected}/{self.coins_required}")


    def on_key_press(self, k, modifiers):
        if self.active_ship is not None:
            # In-plane: all keys go to the ship; SPACE dismounts inside Ship
            self.active_ship.handle_key_press(k, modifiers)
            # SPACE clears pilot; sync active_ship here
            if self.active_ship.pilot is None:
                self.active_ship = None
        else:
            # On foot: W while overlapping a ship → board it
            if k == key.W:
                for ship in self.ships:
                    if ship.check_interaction(self.player):
                        ship.mount(self.player)
                        self.active_ship = ship
                        return   # swallow the W key
            self.player.handle_key_press(k, modifiers)

    def on_key_release(self, k, modifiers):
        if self.active_ship is not None:
            self.active_ship.handle_key_release(k, modifiers)
        else:
            self.player.handle_key_release(k, modifiers)

    def on_mob_die(self, position):
        coin = Coin(position)
        self.add(coin, z=1)
        self.coins.append(coin)

    def spawn_mob_at(self, position, direction=1):
        mob = Mob(position, collision_boxes=self.map_manager.get_land_collisions())
        mob.on_die = self.on_mob_die
        mob.velocity[0] = mob.speed * direction
        mob.scale_x = abs(mob.scale_x) if direction > 0 else -abs(mob.scale_x)
        self.add(mob, z=1)
        self.mobs.append(mob)

def create_game_scene(findpath : str = "assets/map.tmx"):


    # Create Color layer for background
    main_scene = cocos.scene.Scene()
    bg_color = (255, 255, 255, 255)
    static_bg = cocos.layer.ColorLayer(*bg_color)
    main_scene.add(static_bg, z=-1)


    scroller = ScrollingManager()

    tile_map = load(findpath)
    for name, layer in tile_map.find(RectMapLayer):
        print(f"Rendering layer: {name}")
        scroller.add(layer, z=0)



    # Single MapManager shared between GameScene and DebugLayer
    map_manager = MapManager(findpath)
    game_layer  = GameScene(scroller, map_manager)

    scroller.add(game_layer, z=1)

    main_scene.add(scroller, z=0)
    print("Audio Driver: ", pyglet.media.get_audio_driver())
    return main_scene