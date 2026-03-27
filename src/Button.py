from enum import Enum
import cocos
from cocos.sprite import Sprite
import pyglet.image

class TypeButton(Enum):
    ActivateObj = 0
    StretchVertical = 1
    StretchHorizontal = 2
    Prohibited = 3
    IncreaseSize = 4
    DecreaseSize = 5
    Neutral = 6

class Button(Sprite):
    def __init__(self, position, button_type: TypeButton = TypeButton.ActivateObj,
                 image_off: str = "assets/interactions/Button0.png",
                 image_on:  str = "assets/interactions/Button1.png"):
        # Pre-load both textures once — avoids re-reading from disk every frame
        self._img_off = pyglet.image.load(image_off)
        self._img_on  = pyglet.image.load(image_on)

        super(Button, self).__init__(self._img_off)
        self.type = button_type
        self.position = position
        self.onStatus = False
        self.scale = 1.0
        self.was_colliding = False

    def set_status(self, is_on):
        """Switch button state and update texture (only when state actually changed)."""
        if self.onStatus != is_on:
            self.onStatus = is_on
            # Swap to pre-loaded texture — no disk I/O, no flicker
            self.image = self._img_on if is_on else self._img_off

    def check_interaction(self, character):
        """AABB overlap test using the character's actual scaled, bottom-anchored hitbox."""
        bw, bh = self.width, self.height
        bx, by = self.position
        button_rect = cocos.rect.Rect(bx - bw/2, by - bh/2, bw, bh)

        # Use base dims × scale (same formula as Character.update physics)

        char_rect = character.get_leg_collision_rect()

        is_colliding = button_rect.intersects(char_rect)

        # Stay ON as long as character is inside; turn OFF when they leave
        self.set_status(is_colliding)

        self.was_colliding = is_colliding
        return is_colliding
