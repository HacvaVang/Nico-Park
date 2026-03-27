import cocos
from cocos.sprite import Sprite
from enum import Enum
import pyglet
class MobState(Enum):
    PATROL = 0
    DEATH = 2

WALK_ANIM = ["Mob0.png", "Mob1.png"]    

class Mob(Sprite):
    """
    Template for a standard Mob enemy.
    Usually has simple behaviors like patrolling and chasing.
    """
    def __init__(self, position):
        self.animation = self.load_animation()
        super(Mob, self).__init__(self.animation["walk"])
        self.position = position
        self.status = MobState.PATROL
        self.health = 100
        self.scale = 0.5
        # Physics / Movement
        self.speed = 50
        self.velocity = [self.speed, 0]
        self.start_x = position[0]
        self.patrol_distance = 150
        
        self.base_w = self.width
        self.base_h = self.height

        # Bottom-center anchoring for consistency with physics
        self.anchor = (self.base_w / 2, 0)
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
        """Called every frame. Implement patrol/chase AI here."""
        if self.status == MobState.PATROL:
            x, y = self.position
            if x > self.start_x + self.patrol_distance:
                self.velocity[0] = -self.speed
                self.scale_x = -abs(self.scale_x)
            elif x < self.start_x - self.patrol_distance:
                self.velocity[0] = self.speed
                self.scale_x = abs(self.scale_x)
        elif self.status == MobState.CHASE:
            pass
        
        x, y = self.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt
        self.position = (new_x, new_y)

    def get_hitbox(self):
        """Returns the scaled hitbox of the Mob."""
        w = self.base_w * self.scale
        h = self.base_h * self.scale
        x, y = self.position
        return cocos.rect.Rect(x - w/2, y, w, h)
