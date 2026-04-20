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
        self._img_off = pyglet.image.load(image_off)
        self._img_on  = pyglet.image.load(image_on)
        super(Button, self).__init__(self._img_off)
        self.type = button_type
        self.position = position
        self.anchor = (self.width / 2, 0)
        self.image_anchor = (self.width / 2, 0)
        self.onStatus = False
        self.scale = 1.0
        self.was_colliding = False
        self.is_pressed = False

    def set_status(self, is_on):
        if self.onStatus != is_on:
            self.onStatus = is_on
            self.image = self._img_on if is_on else self._img_off

    def _get_press_rect(self):
        bw = self.width * abs(getattr(self, 'scale_x', 1.0))
        bh = self.height * abs(getattr(self, 'scale_y', 1.0))
        bx, by = self.position
        press_h = max(8, bh * 0.55)
        return cocos.rect.Rect(bx - bw / 2, by, bw, press_h)

    def check_interaction(self, character):
        """Single player check — KHÔNG set_status, dùng nội bộ."""
        return self._get_press_rect().intersects(character.get_leg_collision_rect())

    def check_interaction_multi(self, players):
        colliding = []
        is_anyone_on = False
        for p in players:
            if self.get_hitbox().intersects(p.get_leg_collision_rect()):
                colliding.append(p)
                is_anyone_on = True

        self.is_pressed = is_anyone_on  # Cập nhật trạng thái tại đây
        return colliding

    def get_hitbox(self):
        """
        Trả về hình chữ nhật đại diện cho vùng va chạm của nút.
        Bạn có thể điều chỉnh kích thước tùy theo kích thước sprite thực tế.
        """
        # Trả về Rect dựa trên vị trí và kích thước sprite
        return cocos.rect.Rect(
            self.position[0] - self.width / 2,
            self.position[1],
            self.width,
            self.height
        )