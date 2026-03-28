import cocos
from cocos.sprite import Sprite
from enum import Enum
import pyglet

class MobState(Enum):
    PATROL = 0
    DEATH = 2

WALK_ANIM = ["Mob0.png", "Mob1.png"]

class Mob(Sprite):
    def __init__(self, position, collision_boxes=None):
        self.animation = self.load_animation()
        super(Mob, self).__init__(self.animation["walk"])
        self.position = position[:2]
        self.status = MobState.PATROL
        self.health = 10
        self.scale = 0.75
        self.speed = 50
        self.velocity = [self.speed, 0]
        self.gravity = -600
        self.start_x = position[0]
        self.patrol_distance = 150
        self.on_die = None
        self.is_die = False
        self.is_on_ground = False
        self.collision_boxes = collision_boxes or []

        self.base_w = self.width
        self.base_h = self.height
        self.image_anchor = (self.base_w / 2, 0)

        self.schedule(self.update)

    def load_animation(self):
        dict_animation = {}
        walk = []
        for i in WALK_ANIM:
            walk.append(pyglet.image.load(f'assets/mob/{i}'))
        dict_animation["walk"] = pyglet.image.Animation.from_image_sequence(walk, 0.2, loop=True)
        return dict_animation

    def update(self, dt):
        if self.is_die:
            return

        # Patrol logic
        if self.status == MobState.PATROL:
            x, y = self.position
            if x > self.start_x + self.patrol_distance:
                self.velocity[0] = -self.speed
                self.scale_x = -abs(self.scale_x)
            elif x < self.start_x - self.patrol_distance:
                self.velocity[0] = self.speed
                self.scale_x = abs(self.scale_x)

        # Gravity
        self.velocity[1] += self.gravity * dt

        x, y = self.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt

        # Floor collision
        self.is_on_ground = False
        for solid in self.collision_boxes:
            mob_rect = cocos.rect.Rect(new_x - self.base_w * self.scale / 2, new_y,
                                       self.base_w * self.scale, self.base_h * self.scale * 0.3)
            if mob_rect.intersects(solid):
                solid_top = solid.y + solid.height
                overlap_y = min(new_y + self.base_h * self.scale * 0.3, solid_top) - max(new_y, solid.y)
                overlap_x = min(new_x + self.base_w * self.scale / 2, solid.x + solid.width) - max(new_x - self.base_w * self.scale / 2, solid.x)
                if overlap_y <= overlap_x:
                    if self.velocity[1] <= 0:
                        new_y = solid_top
                        self.velocity[1] = 0
                        self.is_on_ground = True
                else:
                    # Chạm tường → đổi hướng
                    self.velocity[0] *= -1
                    self.scale_x *= -1
                    new_x = x

        self.position = (new_x, new_y)

    def get_hitbox(self):
        w = self.base_w * self.scale
        h = self.base_h * self.scale
        x, y = self.position
        return cocos.rect.Rect(x - w/2, y, w, h)

    def die(self):
        if self.is_die:
            return
        self.is_die = True
        if self.on_die:
            self.on_die(self.position)
        self.kill()

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.die()