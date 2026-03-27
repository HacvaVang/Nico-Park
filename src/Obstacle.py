import cocos
from cocos.sprite import Sprite
from enum import Enum
from .Button import Button, TypeButton


class ObstacleState(Enum):
    ACTIVE   = 0   # solid, visible, blocking
    INACTIVE = 1   # transparent, no collision


class Obstacle(Sprite):
    """A game obstacle that has a hitbox and reacts to a linked Button's state."""

    def __init__(self, image, position, linked_button: Button = None):
        super(Obstacle, self).__init__(image)
        self.position = position
        self.linked_button = linked_button

        # Cache base (unscaled) dimensions for stable hitbox math
        self.base_w = self.width
        self.base_h = self.height

        # Start active by default; the button toggles this
        self.state = ObstacleState.ACTIVE
        self._apply_state()

        self.schedule(self.update)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self.state == ObstacleState.ACTIVE

    def get_hitbox(self) -> cocos.rect.Rect:
        """Return the current AABB hitbox (bottom-left origin, unscaled dims)."""
        w, h = self.base_w, self.base_h
        x, y = self.position
        return cocos.rect.Rect(x - w / 2, y - h / 2, w, h)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        """React to the linked button's state every frame."""
        if self.linked_button is None:
            return

        btn_on = self.linked_button.onStatus
        btn_type = self.linked_button.type

        if btn_type == TypeButton.ActivateObj:
            # Button ON  → obstacle ACTIVE (solid)
            # Button OFF → obstacle INACTIVE (passthrough)
            new_state = ObstacleState.ACTIVE if btn_on else ObstacleState.INACTIVE
            if new_state != self.state:
                self.state = new_state
                self._apply_state()

        elif btn_type == TypeButton.StretchVertical:
            if btn_on:
                self.scale_y = min(self.scale_y + 0.02, 3.0)
            else:
                self.scale_y = max(self.scale_y - 0.02, 1.0)

        elif btn_type == TypeButton.StretchHorizontal:
            if btn_on:
                self.scale_x = min(self.scale_x + 0.02, 3.0)
            else:
                self.scale_x = max(self.scale_x - 0.02, 1.0)

        elif btn_type == TypeButton.IncreaseSize:
            if btn_on:
                self.scale = min(self.scale + 0.005, 3.0)

        elif btn_type == TypeButton.DecreaseSize:
            if btn_on:
                self.scale = max(self.scale - 0.005, 0.2)

        elif btn_type == TypeButton.Neutral:
            # Smoothly return to scale 1.0
            if self.scale > 1.0:
                self.scale = max(self.scale - 0.02, 1.0)
            elif self.scale < 1.0:
                self.scale = min(self.scale + 0.02, 1.0)

    # ------------------------------------------------------------------
    # Collision
    # ------------------------------------------------------------------

    def check_character_collision(self, character) -> bool:
        """Return True if character overlaps this obstacle's hitbox (only when active)."""
        if not self.is_active:
            return False
        return self.get_hitbox().intersects(_char_rect(character))

    def push_character_out(self, character):
        """Simple AABB push-out: separate character from this obstacle."""
        if not self.is_active:
            return

        ob = self.get_hitbox()
        ch = _char_rect(character)

        if not ob.intersects(ch):
            return

        # Overlap amounts on each axis
        dx_right = ob.x + ob.width  - ch.x           # push char right
        dx_left  = ch.x + ch.width  - ob.x           # push char left
        dy_top   = ob.y + ob.height - ch.y            # push char up
        dy_bottom= ch.y + ch.height - ob.y            # push char down

        min_dx = dx_right if dx_right < dx_left  else -dx_left
        min_dy = dy_top   if dy_top   < dy_bottom else -dy_bottom

        cx, cy = character.position
        if abs(min_dx) < abs(min_dy):
            character.position = (cx + min_dx, cy)
            character.velocity[0] = 0
        else:
            character.position = (cx, cy + min_dy)
            if min_dy > 0:
                character.velocity[1] = 0
                character.is_on_ground = True
            else:
                character.velocity[1] = 0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _apply_state(self):
        """Sync visual opacity to current state."""
        if self.state == ObstacleState.ACTIVE:
            self.opacity = 255
        else:
            self.opacity = 80   # semi-transparent when inactive/passthrough


def _char_rect(character) -> cocos.rect.Rect:
    """Build the character's AABB using its base (unscaled) dimensions."""
    w = getattr(character, "base_w", character.width)
    h = getattr(character, "base_h", character.height)
    cx, cy = character.position
    return cocos.rect.Rect(cx - w / 2, cy, w, h)  # bottom-anchor
