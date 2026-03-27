import cocos
from cocos.sprite import Sprite
import pyglet.window.key as key

class Character(Sprite):
    def __init__(self, image, collision_boxes = None, start_pos = None):
        super(Character, self).__init__(image)
        self.collision_boxes = collision_boxes
        
        self.velocity = [0, 0]
        self.speed = 250
        self.gravity = -400
        self.jump_speed = 300
        self.is_on_ground = False
        self.position = start_pos
        self.schedule(self.update)

    def update(self, dt):
        self.velocity[1] += self.gravity * dt
        
        x, y = self.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt
         
        # Optional: Add collision logic using self.map_manager if applicable
        if self.collision_boxes:
            w, h = self.width, self.height
            new_rect = cocos.rect.Rect(new_x - w/2, new_y - h/2, w, h)
            
            for solid in self.collision_boxes:
                if new_rect.intersects(solid):
                    # Basic floor check
                    if self.velocity[1] < 0 and self.position[1] - h/2 >= solid.y + solid.height - 10:
                        new_y = solid.y + solid.height + h/2
                        self.velocity[1] = 0
                        self.is_on_ground = True

        # Giới hạn mặt đất cơ bản (backup)
        if new_y <= 100:
            new_y = 100
            self.velocity[1] = 0
            self.is_on_ground = True
        else:
            if self.velocity[1] != 0:
                self.is_on_ground = False

        self.position = (new_x, new_y)

    def handle_key_press(self, k, modifiers):
        if k == key.A:
            self.velocity[0] = -self.speed
        elif k == key.D:
            self.velocity[0] = self.speed
        elif k == key.SPACE:
            if self.is_on_ground:
                self.velocity[1] = self.jump_speed
                self.is_on_ground = False

    def handle_key_release(self, k, modifiers):
        if k in (key.LEFT, key.RIGHT):
            self.velocity[0] = 0
