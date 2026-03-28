import cocos
from cocos.sprite import Sprite
import pyglet
import math
from .Minion import Mob

class Boss(Sprite):
    def __init__(self, position, game_scene):
        img = pyglet.image.load("assets/AngryNeko.png")
        super(Boss, self).__init__(img)
        self.position = position[:2]
        self.game_scene = game_scene
        self.health = 70
        self.max_health = 70
        self.is_die = False
        self.base_w = self.width
        self.base_h = self.height
        self.image_anchor = (self.base_w / 2, 0)
        self.scale_x = -2
        self.scale_y = 2
        self.leg_rect = cocos.rect.Rect(0, 0, self.base_w, self.base_h // 3)
        self.head_rect = cocos.rect.Rect(0, 0, self.base_w, self.base_h * 2 // 3)

        # Bay lòng vòng
        self.fly_timer = 0
        self.fly_radius = 120
        self.fly_speed = 1.5
        self.origin_x = position[0]
        self.origin_y = position[1]

        # Spawn mob
        self.spawn_timer = 0
        self.spawn_cooldown = 4.0

        # Trigger
        self.activated = False
        self.trigger_x = position[0]
        self.visible = False
        self.warning_distance = 300
        self.activation_distance = 20
        self.warning_shown = False
        self.warning_label = None

        self.schedule(self.update)

    def update_hitbox(self):
        w = self.base_w * abs(self.scale_x)
        h = self.base_h * abs(self.scale_y)

        leg_h = h * (1 - 64 / 96)
        leg_w = w * 32 / 80
        head_h = h * (64 / 96)

        x, y = self.position

        # Chân (dưới)
        self.leg_rect = cocos.rect.Rect(x - leg_w / 2, y, leg_w, leg_h)

        # Đầu (trên)
        self.head_rect = cocos.rect.Rect(x - w / 2, y + leg_h, w, head_h)

    def update(self, dt):
        self.update_hitbox()
        if self.is_die:
            return

        if not self.activated:
            px = self.game_scene.player.position[0]
            dist_x = abs(px - self.trigger_x)
            
            if dist_x < self.warning_distance and not self.warning_shown:
                self.warning_shown = True
                import cocos.actions as ac
                # Warning sign positioned between player and boss
                wx = self.trigger_x - 300 if px < self.trigger_x else self.trigger_x + 300
                self.warning_label = cocos.text.Label(
                    "WARNING: BOSS NEARBY!",
                    font_name='Pixels',
                    font_size=36,
                    color=(255, 0, 0, 255),
                    x=wx,
                    y=self.position[1] + 200,
                    anchor_x='center',
                    anchor_y='center'
                )
                self.game_scene.add(self.warning_label, z=100)
                self.warning_label.do(ac.Repeat(ac.FadeOut(0.5) + ac.FadeIn(0.5)))

            if dist_x < self.activation_distance:
                self.activated = True
                self.visible = True
                print("Boss ACTIVATED!")
                if self.warning_label:
                    self.warning_label.kill()
                    self.warning_label = None
            return

        px, py = self.game_scene.player.position

        # Chase player
        chase_speed = 80 * dt
        dx = px - self.origin_x
        dy = (py + 100) - self.origin_y  # Target point is slightly above player
        
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.origin_x += (dx / dist) * chase_speed
            self.origin_y += (dy / dist) * chase_speed

        # Bay lòng vòng
        self.fly_timer += dt
        bx = self.origin_x + math.cos(self.fly_timer * self.fly_speed) * self.fly_radius
        by = self.origin_y + math.sin(self.fly_timer * self.fly_speed) * self.fly_radius
        self.position = (bx, by)

        # Facing direction
        if px < self.position[0]:
            self.scale_x = -abs(self.scale_x)
        else:
            self.scale_x = abs(self.scale_x)

        # Spawn mob
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_mob()
            self.spawn_timer = self.spawn_cooldown

    def spawn_mob(self):
        direction = 1 if self.scale_x > 0 else -1
        self.game_scene.spawn_mob_at(self.position, direction)

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.die()

    def die(self):
        if self.is_die:
            return
        self.is_die = True
        
        # Display victory text
        import cocos.actions as ac
        win_label = cocos.text.Label(
            "BOSS CLEARED!",
            font_name='Pixels',
            font_size=60,
            color=(255, 133, 76, 255),
            x=self.position[0],
            y=self.position[1] + 50,
            anchor_x='center',
            anchor_y='center'
        )
        self.game_scene.add(win_label, z=100)
        win_label.do(ac.MoveBy((0, 150), duration=2) | ac.FadeOut(duration=2))
        
        self.kill()

        try:
            from .GameScene import SoundManager
            SoundManager.play_sfx('assets/sound/die.wav')
        except Exception as e:
            print(f"Could not play win sound: {e}")

        # Schedule ending the game
        pyglet.clock.schedule_once(self.end_game, 2.0)

    def end_game(self, dt=0):
        from cocos.director import director
        from .MainMenu import create_main_menu
        director.replace(create_main_menu())

    def get_leg_collision_rect(self):
        return self.leg_rect

    def get_head_collision_rect(self):
        return self.head_rect