import cocos
from cocos.sprite import Sprite
import pyglet.window.key as key
from enum import Enum
from .Button import TypeButton, Button

class CharacterState(Enum):
    IDLE = 0
    RUN = 1
    ON_AIR = 2
    DEATH = 3


class Character(Sprite):
    def __init__(self, image, collision_boxes = None, start_pos = None):
        super(Character, self).__init__(image=image, position=start_pos)
        self.collision_boxes = collision_boxes
        self.status = CharacterState.IDLE
        self.velocity = [0, 0]
        self.speed = 250
        self.gravity = -600
        self.jump_speed = 300
        self.is_on_ground = False
        
        self.minimum_scale = 0.5
        self.maximum_scale = 2.5

        # Store unscaled base dimensions — used for all physics/collision math
        # self.width/height return SCALED values so we must cache the originals
        self.base_w = self.width
        self.base_h = self.height

        # Smooth scale: set target_scale to animate toward instead of setting self.scale directly
        self.target_scale = 1.0
        self.scale_speed = 0.05

        self.image_anchor = (self.base_w / 2, 0)

        # Current collision rects (updated every frame in update())
        self.rect_x   = cocos.rect.Rect(0, 0, self.base_w, self.base_h)
        self.leg_rect  = cocos.rect.Rect(0, 0, self.base_w, self.base_h // 3)
        self.head_rect = cocos.rect.Rect(0, 0, self.base_w, self.base_h * 2 // 3)

        self.schedule(self.update)

    def update(self, dt):
        self.velocity[1] += self.gravity * dt
        
        x, y = self.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt
         
        # Hitbox dimensions scale with the character visual size.
        # We multiply base dims by self.scale so the hitbox grows/shrinks together with
        # the sprite while the base dims remain constant for stable ratio calculations.
        w = self.base_w * self.scale
        h = self.base_h * self.scale

        if self.collision_boxes:
            
            leg_h  = h * (1 - 64 / 96)   # lower half
            leg_w  = w * 32 / 80
            head_h = h * (64 / 96)   # upper half

            # --- X-axis collision (full body width, full height) ---
            self.rect_x = cocos.rect.Rect(new_x - w/2, y, w, h)
            # for solid in self.collision_boxes:
            #     if self.rect_x.intersects(solid):
            #         if self.velocity[0] > 0:
            #             new_x = solid.x - w/2
            #             self.rect_x.x = new_x - w/2
            #         elif self.velocity[0] < 0:
            #             new_x = solid.x + solid.width + w/2
            #             self.rect_x.x = new_x - w/2

            # --- Y-axis: Leg box (lower portion) — floor detection ---
            # Anchor is BOTTOM: sprite goes from new_y (bottom) to new_y+h (top)
            self.leg_rect = cocos.rect.Rect(new_x - leg_w/2, new_y, leg_w, leg_h)
            self.is_on_ground = False
            for solid in self.collision_boxes:
                if self.leg_rect.intersects(solid):
                    if self.velocity[1] <= 0:
                        # Place character bottom exactly on top of the solid
                        new_y = solid.y + solid.height
                        self.velocity[1] = 0
                        self.is_on_ground = True
                        self.leg_rect.y = new_y

            # --- Y-axis: Head box (upper portion) — ceiling detection ---
            # Head starts at leg_h above the bottom, extends to the top
            self.head_rect = cocos.rect.Rect(new_x - w/2, new_y + leg_h, w, head_h)
            for solid in self.collision_boxes:
                if self.head_rect.intersects(solid):
                    if self.velocity[1] > 0:
                        # Place character so its top is at the solid's bottom
                        new_y = solid.y - h
                        self.velocity[1] = 0
                        self.head_rect.y = new_y + leg_h
                    if self.is_on_ground:
                        if self.velocity[0] > 0:
                            new_x = solid.x - w/2
                            self.head_rect.x = new_x - w/2
                        elif self.velocity[0] < 0:
                            new_x = solid.x + solid.width + w/2
                        self.head_rect.x = new_x - w/2
        else:
            if self.velocity[1] != 0:
                self.is_on_ground = False

        self.position = (new_x, new_y)

        # Smoothly lerp scale toward target each frame
        self.update_scale()

    def update_scale(self):
        """Smoothly lerp self.scale toward self.target_scale each frame."""
        diff = self.target_scale - self.scale
        if abs(diff) <= self.scale_speed:
            self.scale = self.target_scale  # snap when close enough
        elif diff > 0:
            self.scale += self.scale_speed
        else:
            self.scale -= self.scale_speed
        
        if self.scale < self.minimum_scale:
            self.scale = self.minimum_scale
        elif self.scale > self.maximum_scale:
            self.scale = self.maximum_scale

    def apply_button_effect(self, button: Button):
        button_type = button.type
        if button_type == TypeButton.ActivateObj:
            pass
        elif button_type == TypeButton.StretchVertical:
            pass
        elif button_type == TypeButton.StretchHorizontal:
            pass
        elif button_type == TypeButton.Prohibited:
            pass
        elif button_type == TypeButton.IncreaseSize:
            self.target_scale += 0.005   # set target, not scale directly
        elif button_type == TypeButton.DecreaseSize:
            self.target_scale -= 0.005
        elif button_type == TypeButton.Neutral:
            self.target_scale = 1.0      # snap back to normal over time
            


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
        if k in (key.A, key.D):
            self.velocity[0] = 0

    def get_leg_collision_rect(self):
        return self.leg_rect
    
    def get_head_collision_rect(self):
        return self.head_rect
    
    def get_full_collision_rect(self):
        return self.rect_x
