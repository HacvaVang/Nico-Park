from enum import Enum
import cocos
from cocos.sprite import Sprite
import pyglet.image

class Coin(Sprite):
    def __init__(self, position):
        self.animation = self.load_animation_from_strip("./assets/interactions/gold.blink.png", 32,32, 14, 0.3)
        super(Coin, self).__init__(self.animation)
        self.position = position
        self.collected = False
        #self.anchor = (self.width / 2, 0)
        self.image_anchor = (self.height / 2, 0)
        self.scale = 2

    def load_animation_from_strip(self, image_path, frame_width, frame_height, num_frames, duration=0.1, loop=True):
        strip = pyglet.image.load(image_path)
        image_grid = pyglet.image.ImageGrid(strip, 1, num_frames,
                                            item_width=frame_width,
                                            item_height=frame_height)
        frames = [
            pyglet.image.AnimationFrame(image_grid[i], duration)
            for i in range(num_frames)
        ]
        for frame in frames:
            img = frame.image
            img.anchor_x = img.width // 2
            img.anchor_y = 0

        return pyglet.image.Animation(frames)

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