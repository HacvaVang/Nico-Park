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
from .Key import Key
from .Ship import Ship
from .Gun import Gun
from .Boss import Boss
from .GameRules import GameRules, load_rules

import pyglet
pyglet.options['audio'] = ('ffmpeg', 'openal', 'pulse', 'directsound', 'silent')
DIE_DISTANCE = -100


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

    def __init__(self, scroller, map_manager: MapManager = None, rules: GameRules = None):
        super(GameScene, self).__init__()
        if map_manager is None:
            map_manager = MapManager("assets/map.tmx")

        self.hud_layer = None
        self.scroller = scroller
        self.keys_collected = 0
        self.rules = rules or load_rules()
        self.keys_required = self.rules.keys_required
        self.door_opened = False
        self.level_cleared = False
        obstacle_pos = map_manager.get_object_position_list("Obstacle")
        boss_positions = map_manager.get_object_position_list("AngryNeko")
        self.map_manager = map_manager

        self.player = Character(map_manager.get_land_collisions(), map_manager.get_starting_position())
        self.add(self.player, z=1)

        self.buttons = list()
        status_list = [TypeButton.IncreaseSize, TypeButton.DecreaseSize,
                       TypeButton.Neutral, TypeButton.Neutral,
                       TypeButton.Neutral, TypeButton.Neutral]
        for i in range(len(status_list)):
            button = Button(map_manager.get_object_position_list("Button")[i], status_list[i])
            self.buttons.append(button)
            self.add(button, z=1)
        self.door_trigger_buttons = [self.buttons[4], self.buttons[5]]

        self.mobs = []
        for pos in map_manager.get_object_position_list("Mob"):
            mob = Mob(pos, collision_boxes=map_manager.get_land_collisions())
            mob.on_die = self.on_mob_die
            self.add(mob, z=1)
            self.mobs.append(mob)

        self.bosses = []
        for i, pos in enumerate(boss_positions):
            trigger_x = obstacle_pos[i][0] if i < len(obstacle_pos) else pos[0]
            boss = Boss(pos, self)
            boss.trigger_x = trigger_x
            self.add(boss, z=1)
            self.bosses.append(boss)

        self.keys = []
        key_positions = map_manager.get_object_position_list("Key")
        if not key_positions:
            key_positions = map_manager.get_object_position_list("Coin")
        for pos in key_positions:
            key_item = Key(pos)
            self.keys.append(key_item)
            self.add(key_item, z=1)

        if self.keys:
            self.keys_required = min(self.keys_required, len(self.keys))

        self.guns = []
        for pos in map_manager.get_object_position_list("Gun"):
            gun = Gun(pos)
            self.guns.append(gun)
            self.add(gun, z=1)
        self.bullets = []

        self.ships = []
        for pos in map_manager.get_object_position_list("Ship"):
            ship = Ship(pos)
            self.ships.append(ship)
            self.add(ship, z=1)

        obstacle_positions = map_manager.get_object_position_list("Obstacle")
        self.obstacles = []
        if obstacle_positions:
            for pos in obstacle_positions:
                obs = Obstacle(pos, self.buttons[2])
                self.obstacles.append(obs)
                self.add(obs, z=1)
        self.door = self.obstacles[0] if self.obstacles else None

        self.exit_rect = None
        if obstacle_positions:
            ox, oy = obstacle_positions[0]
            self.exit_rect = cocos.rect.Rect(ox - 60, oy, 120, 140)

        SoundManager.play_bgm('assets/sound/Hands.wav')
        self.active_ship: Ship = None
        self.schedule(self.update)

    def update(self, dt):
        if self.hud_layer and self.bosses:
            boss = self.bosses[0]
            if boss.activated:
                self.hud_layer.update_boss_hp(boss.health, boss.max_health)

        self.scroller.set_focus(self.player.position[0], self.player.position[1])
        players = self._iter_players()
        for button in self.buttons:
            button.check_interaction_multi(players)

        for player in self._iter_players():
            if player.has_gun and player.shoot_timer <= 0:
                bullet = player.shoot()
                if bullet:
                    self.add(bullet, z=2)
                    self.bullets.append(bullet)
                    player.shoot_timer = player.shoot_cooldown
        self.check_door_condition()
        # FIX: check button một lần với tất cả players
        # Button ON nếu BẤT KỲ player nào đứng trên
        players = self._iter_players()
        for button in self.buttons:
            colliding = button.check_interaction_multi(players)
            for player in colliding:
                player.apply_button_effect(button)

        self.check_bullet_mob_collision(self.mobs)

        for player in self._iter_players():
            for obs in self.obstacles:
                obs.push_character_out(player)

        for player in self._iter_players():
            if player.position[1] <= DIE_DISTANCE and not player.is_die:
                player.die()

        for player in self._iter_players():
            player.check_stomp(self.mobs)

        if self.rules.fail_if_any_player_dead:
            for player in self._iter_players():
                if player.is_die:
                    self._team_fail()
                    return

        self.check_key_collect()
        self.check_gun_collect()
        self.check_bullet_mob_collision(self.bosses)
        for player in self._iter_players():
            player.check_stomp(self.bosses)
        self.bullets = [b for b in self.bullets if not b.dead and b.parent is not None]
        self.check_bullet_wall_collision()

        if self._should_evaluate_level_clear():
            self.check_level_complete()

    def _iter_players(self):
        return [self.player]

    def _should_evaluate_level_clear(self):
        return True

    def check_bullet_wall_collision(self):
        land_rects = self.map_manager.get_land_collisions()
        for bullet in self.bullets[:]:
            if bullet.dead:
                continue
            bullet_rect = bullet.get_hitbox()
            for rect in land_rects + self.obstacles:
                if bullet_rect.intersects(rect):
                    bullet.dead = True
                    bullet.kill()
                    break

    def check_bullet_mob_collision(self, targets):
        for target in targets[:]:
            if getattr(target, 'is_die', False):
                continue
            for bullet in self.bullets[:]:
                if bullet.dead:
                    continue
                bullet_rect = bullet.get_hitbox()
                hit = False
                if isinstance(target, Boss):
                    if bullet_rect.intersects(target.get_leg_collision_rect()) or \
                            bullet_rect.intersects(target.get_head_collision_rect()):
                        hit = True
                else:
                    if bullet_rect.intersects(target.get_hitbox()):
                        hit = True
                if hit:
                    target.take_damage(bullet.damage)
                    bullet.dead = True
                    bullet.kill()

    def check_gun_collect(self):
        for player in self._iter_players():
            player_rect = player.get_leg_collision_rect()
            for gun in self.guns[:]:
                if not gun.collected and player_rect.intersects(gun.get_hitbox()):
                    gun.collect()
                    player.pick_up_gun(gun)

    def check_key_collect(self):
        for player in self._iter_players():
            leg_rect = player.get_leg_collision_rect()
            head_rect = player.get_head_collision_rect()
            for key_item in self.keys[:]:
                if key_item.collected:
                    continue
                if leg_rect.intersects(key_item.get_hitbox()) or head_rect.intersects(key_item.get_hitbox()):
                    key_item.collect()
                    self.keys_collected += 1


    def open_door(self):
        self.door_opened = True
        if self.obstacles:
            self.obstacles[0].open()
        print(f"Door opened! keys={self.keys_collected}/{self.keys_required}")

    def check_level_complete(self):
        if self.level_cleared or not self.door_opened or self.exit_rect is None:
            return
        players = [p for p in self._iter_players() if p is not None]
        alive = [p for p in players if not p.is_die]
        if not alive:
            return
        if self.rules.require_all_players_at_exit:
            ok = all(self._is_player_at_exit(p) for p in alive)
        else:
            ok = any(self._is_player_at_exit(p) for p in alive)
        if ok:
            self.on_level_cleared()

    def _is_player_at_exit(self, player):
        return self.exit_rect.intersects(player.get_leg_collision_rect())

    def on_level_cleared(self):
        if self.level_cleared:
            return
        self.level_cleared = True
        print("LEVEL CLEARED")
        label = cocos.text.Label(
            "LEVEL CLEARED!",
            font_name='Pixels',
            font_size=48,
            color=(255, 245, 170, 255),
            anchor_x='center',
            anchor_y='center'
        )
        label.position = self.player.position
        self.add(label, z=100)

    def _team_fail(self):
        print("TEAM FAILED")
        from cocos.director import director
        from .MultiplayerMenu import create_multiplayer_menu
        director.replace(create_multiplayer_menu())

    def on_key_press(self, k, modifiers):
        if self.active_ship is not None:
            self.active_ship.handle_key_press(k, modifiers)
            if self.active_ship.pilot is None:
                self.active_ship = None
        else:
            if k == key.W:
                for ship in self.ships:
                    if ship.check_interaction(self.player):
                        ship.mount(self.player)
                        self.active_ship = ship
                        return
            self.player.handle_key_press(k, modifiers)

    def on_key_release(self, k, modifiers):
        if self.active_ship is not None:
            self.active_ship.handle_key_release(k, modifiers)
        else:
            self.player.handle_key_release(k, modifiers)

    def on_mob_die(self, position):
        pass

    def spawn_mob_at(self, position, direction=1):
        mob = Mob(position, collision_boxes=self.map_manager.get_land_collisions())
        mob.on_die = self.on_mob_die
        mob.velocity[0] = mob.speed * direction
        mob.scale_x = abs(mob.scale_x) if direction > 0 else -abs(mob.scale_x)
        self.add(mob, z=1)
        self.mobs.append(mob)

    def check_door_condition(self):
        if self.door_opened or self.door is None:
            return

        # 1. Đã nhặt đủ chìa
        has_enough_keys = (self.keys_collected >= self.keys_required)

        # 2. Hai nút cửa đang được nhấn cùng lúc (sử dụng thuộc tính is_pressed từ Button.py)
        all_buttons_pressed = all(btn.is_pressed for btn in self.door_trigger_buttons)

        if has_enough_keys and all_buttons_pressed:
            self.open_door()


def create_game_scene(findpath: str = "assets/map.tmx"):
    main_scene = cocos.scene.Scene()
    main_scene.add(cocos.layer.ColorLayer(255, 255, 255, 255), z=-1)

    scroller = ScrollingManager()
    tile_map = load(findpath)
    for name, layer in tile_map.find(RectMapLayer):
        print(f"Rendering layer: {name}")
        scroller.add(layer, z=0)

    map_manager = MapManager(findpath)
    game_layer = GameScene(scroller, map_manager, rules=load_rules())
    scroller.add(game_layer, z=1)

    from .HUD import HUDLayer
    hud = HUDLayer()
    game_layer.hud_layer = hud
    main_scene.add(hud, z=2)
    main_scene.add(scroller, z=0)
    print("Audio Driver: ", pyglet.media.get_audio_driver())
    return main_scene

