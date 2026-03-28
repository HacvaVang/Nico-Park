from enum import Enum
import cocos
from cocos.sprite import Sprite
import pyglet.image

class Gun(Sprite):
    def __init__(self, position):
        self.animation = pyglet.image.load("assets/interactions/Gun.png")
        super(Gun, self).__init__(self.animation)
        self.position = position
        self.collected = False
        #self.anchor = (self.width / 2, 0)
        self.image_anchor = (self.height / 2, 0)
        self.scale = 1

    def get_hitbox(self):
        """Returns the scaled hitbox of the Mob."""
        w = self.width
        h = self.height
        x, y = self.position
        return cocos.rect.Rect(x - w/4, y, w/2, h)

    def collect(self):
        if self.collected:
            return
        self.collected = True
        self.kill()