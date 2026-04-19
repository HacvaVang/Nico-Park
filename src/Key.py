import cocos
from cocos.sprite import Sprite
import pyglet.image


class Key(Sprite):
    def __init__(self, position):
        image = pyglet.image.load("assets/interactions/Key.png")
        super(Key, self).__init__(image)
        self.position = position
        self.collected = False
        self.image_anchor = (self.width / 2, 0)
        self.scale = 1.0

    def get_hitbox(self):
        w = self.width * self.scale
        h = self.height * self.scale
        x, y = self.position
        return cocos.rect.Rect(x - w / 2, y, w, h)

    def collect(self):
        if self.collected:
            return
        self.collected = True
        self.kill()
