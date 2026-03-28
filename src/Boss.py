import cocos
from cocos.sprite import Sprite
import pyglet
from .Minion import Mob

class Boss(Sprite):
    def __init__(self, position, game_scene):
        img = pyglet.image.load("assets/AngryNeko.png")
        super(Boss, self).__init__(img)
        self.position = position[:2]
        self.game_scene = game_scene
        self.health = 200
        self.is_die = False
        self.base_w = self.width
        self.base_h = self.height
        self.spawn_timer = 0
        self.image_anchor = (self.base_w / 2, 0)
        self.spawn_cooldown = 4.0
        self.scale_x = -2
        self.scale_y = 2
        self.max_health = 200
        self.health_bar_bg = cocos.layer.ColorLayer(150, 0, 0, 255, width=60, height=8)
        self.health_bar = cocos.layer.ColorLayer(0, 200, 0, 255, width=60, height=8)
        self.health_bar_bg.position = (-30, self.base_h + 5)
        self.health_bar.position = (-30, self.base_h + 5)
        self.add(self.health_bar_bg, z=3)
        self.add(self.health_bar, z=4)


        # Vật lý
        self.gravity = -600
        self.velocity = [0, 0]
        self.is_on_ground = False

        # Boss chưa active, chờ player đi qua trigger zone
        self.activated = False
        self.trigger_x = position[0]  # vị trí X của obstacle cũ
        self.visible = False  # Ẩn cho đến khi active

        self.schedule(self.update)

    def update(self, dt):
        if self.is_die:
            return

        if not self.activated:
            px = self.game_scene.player.position[0]
            if abs(px - self.trigger_x) < 200:
                self.activated = True
                self.visible = True
                print("Boss ACTIVATED!")
            return

        # Gravity để boss đứng trên sàn
        self.velocity[1] += self.gravity * dt
        bx, by = self.position
        new_y = by + self.velocity[1] * dt

        self.is_on_ground = False
        for solid in self.game_scene.map_manager.get_land_collisions():
            solid_top = solid.y + solid.height
            boss_rect = cocos.rect.Rect(bx - self.base_w / 2, new_y, self.base_w, self.base_h * 0.3)
            if boss_rect.intersects(solid):
                overlap_y = min(new_y + self.base_h * 0.3, solid_top) - max(new_y, solid.y)
                overlap_x = min(bx + self.base_w / 2, solid.x + solid.width) - max(bx - self.base_w / 2, solid.x)
                if overlap_y <= overlap_x and self.velocity[1] <= 0:
                    new_y = solid_top
                    self.velocity[1] = 0
                    self.is_on_ground = True

        self.position = (bx, new_y)

        # Spawn mob
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_mob()
            self.spawn_timer = self.spawn_cooldown

    def spawn_mob(self):
        direction = 1 if self.scale_x > 0 else -1
        self.game_scene.spawn_mob_at(self.position, direction)

    def update_health_bar(self):
        ratio = max(0, self.health / self.max_health)
        new_width = int(60 * ratio)
        # Xóa bar cũ và tạo lại với width mới
        self.remove(self.health_bar)
        self.health_bar = cocos.layer.ColorLayer(0, 200, 0, 255, width=max(1, new_width), height=8)
        self.health_bar.position = (-30, self.base_h + 5)
        self.add(self.health_bar, z=4)

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

    def get_hitbox(self):
        w = self.base_w
        h = self.base_h
        x, y = self.position
        return cocos.rect.Rect(x - w/2, y, w, h)