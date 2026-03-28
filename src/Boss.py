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

        # Health bar
        self.health_label = cocos.text.Label(
            f"HP: {self.health}/{self.max_health}",
            font_name='Arial', font_size=10,
            x=0, y=self.base_h + 10,
            anchor_x='center', anchor_y='bottom'
        )
        self.health_label.scale_x = 1 / abs(self.scale_x)
        self.health_label.scale_y = 1 / abs(self.scale_y)
        self.add(self.health_label, z=5)

        # Bay lòng vòng
        self.fly_timer = 0
        self.fly_radius = 100
        self.fly_speed = 2.0
        self.origin_x = position[0]
        self.origin_y = position[1]

        # Spawn mob
        self.spawn_timer = 0
        self.spawn_cooldown = 4.0

        # Trigger
        self.activated = False
        self.trigger_x = position[0]
        self.visible = False

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
            if abs(px - self.trigger_x) < 200:
                self.activated = True
                self.visible = True
                print("Boss ACTIVATED!")
            return

        # Bay lòng vòng
        self.fly_timer += dt
        bx = self.origin_x + math.cos(self.fly_timer * self.fly_speed) * self.fly_radius
        by = self.origin_y + math.sin(self.fly_timer * self.fly_speed) * self.fly_radius
        self.position = (bx, by)

        # Spawn mob
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_mob()
            self.spawn_timer = self.spawn_cooldown

    def spawn_mob(self):
        direction = 1 if self.scale_x > 0 else -1
        self.game_scene.spawn_mob_at(self.position, direction)

    def update_health_bar(self):
        self.health_label.element.text = f"HP: {self.health}/{self.max_health}"

    def take_damage(self, damage):
        self.health -= damage
        self.update_health_bar()
        if self.health <= 0:
            self.die()

    def die(self):
        if self.is_die:
            return
        self.is_die = True
        self.kill()

    def get_leg_collision_rect(self):
        return self.leg_rect

    def get_head_collision_rect(self):
        return self.head_rect