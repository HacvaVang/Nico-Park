import cocos
from cocos.sprite import Sprite
from enum import Enum

class MinionState(Enum):
    PATROL = 0
    CHASE = 1
    DEATH = 2

class Minion(Sprite):
    """
    Template for a standard Minion enemy.
    Usually has simple behaviors like patrolling and chasing.
    """
    def __init__(self, position, image="assets/sprite/Blue1.png"): # Placeholder image
        super(Minion, self).__init__(image)
        self.position = position
        self.status = MinionState.PATROL
        self.health = 100
        
        # Physics / Movement
        self.velocity = [0, 0]
        self.base_w = self.width
        self.base_h = self.height

        # Bottom-center anchoring for consistency with physics
        self.anchor = (self.base_w / 2, 0)
        self.image_anchor = (self.base_w / 2, 0)

        self.schedule(self.update)

    def update(self, dt):
        """Called every frame. Implement patrol/chase AI here."""
        if self.status == MinionState.PATROL:
            # Add simple back-and-forth movement
            pass
        elif self.status == MinionState.CHASE:
            pass
        
        x, y = self.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt
        self.position = (new_x, new_y)

    def get_hitbox(self):
        """Returns the scaled hitbox of the minion."""
        w = self.base_w * self.scale
        h = self.base_h * self.scale
        x, y = self.position
        return cocos.rect.Rect(x - w/2, y, w, h)
