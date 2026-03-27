import cocos
from cocos.sprite import Sprite
from enum import Enum

class BossState(Enum):
    IDLE = 0
    MOVE = 1
    ATTACK = 2
    DEATH = 3



class Boss(Sprite):
    """
    Template for a Boss enemy.
    Handles complex patterns, higher health, and distinct phases.
    """
    def __init__(self, position, image="assets/sprite/Blue1.png"): # Placeholder image
        super(Boss, self).__init__(image)
        self.position = position
        self.status = BossState.IDLE
        self.health = 1000
        
        # Physics / Movement (Placeholder values)
        self.velocity = [0, 0]
        self.base_w = self.width
        self.base_h = self.height
        
        # Anchor point (Bottom center recommended if using gravity like Character)
        self.anchor = (self.base_w / 2, 0)
        self.image_anchor = (self.base_w / 2, 0)

        self.schedule(self.update)

    def update(self, dt):
        """Called every frame. Implement state machine, patterns, and movement here."""
        if self.status == BossState.IDLE:
            pass
        elif self.status == BossState.ATTACK:
            pass
        
        # Update position based on velocity
        x, y = self.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt
        self.position = (new_x, new_y)

    def get_hitbox(self):
        """Returns the scaled hitbox of the boss."""
        w = self.base_w * self.scale
        h = self.base_h * self.scale
        x, y = self.position
        return cocos.rect.Rect(x - w/2, y, w, h)
