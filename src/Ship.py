import cocos
from cocos.sprite import Sprite
import pyglet
import pyglet.window.key as key


PLANE_SPEED      = 300   # px / second
SHIP_SPRITE_PATH = "assets/sprite/BlueShip1.png"


class Ship(Sprite):
    """
    A rideable plane.

    Boarding  – walk into the ship and press W.
                The character sprite changes to BlueShip1.png and flies freely.
    Controls  – WASD while mounted.
    Dismount  – press SPACE. Character sprite and normal physics are restored.
    """

    def __init__(self, position, image: str = "assets/interactions/BlueShip0.png"):
        try:
            super(Ship, self).__init__(image)
        except Exception:
            img = pyglet.image.SolidColorImagePattern((80, 140, 220, 230)).create_image(128, 48)
            super(Ship, self).__init__(img)

        self.position = position
        self.base_w = self.width
        self.base_h = self.height

        # Bottom-centre anchor (matches Character convention)
        self.image_anchor = (self.base_w / 2, 0)

        # The character currently piloting (None = empty)
        self.pilot = None

        # We cache the ship sprite image so we can restore it later if needed
        self._ship_image = pyglet.image.load(image) if self._try_load(image) else self.image

        self.schedule(self.update)

    @staticmethod
    def _try_load(path):
        try:
            pyglet.image.load(path)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Geometry / interaction
    # ------------------------------------------------------------------

    def get_hitbox(self) -> cocos.rect.Rect:
        """Full AABB of the ship (bottom-left origin)."""
        bw, bh = self.width, self.height
        bx, by = self.position
        return cocos.rect.Rect(bx - bw / 2, by - bh / 2, bw, bh)

    def check_interaction(self, character) -> bool:
        """AABB overlap test using the character's leg hitbox."""
        ship_rect = self.get_hitbox()
        return ship_rect.intersects(character.get_leg_collision_rect())

    # ------------------------------------------------------------------
    # Per-frame
    # ------------------------------------------------------------------

    def update(self, dt):
        if self.pilot is None:
            return

        # Move the character (ship follows because it IS the character now)
        cx, cy = self.pilot.position
        new_x = cx + self.pilot.velocity[0] * dt
        new_y = cy + self.pilot.velocity[1] * dt
        self.pilot.position = (new_x, new_y)

        # Face direction of travel
        if self.pilot.velocity[0] > 0:
            self.pilot.scale_x = abs(self.pilot.scale_x)
        elif self.pilot.velocity[0] < 0:
            self.pilot.scale_x = -abs(self.pilot.scale_x)

        # Sync ship position to character so check_interaction stays accurate
        self.position = self.pilot.position

    # ------------------------------------------------------------------
    # Mount / dismount
    # ------------------------------------------------------------------

    def mount(self, character):
        """Board the plane: swap character sprite for the ship sprite."""
        if self.pilot is not None:
            return   # already occupied

        self.pilot = character
        character.is_piloting = True

        # Swap sprite to BlueShip1.png
        try:
            character.image = pyglet.image.load(SHIP_SPRITE_PATH)
        except Exception as e:
            print(f"[Ship] Could not load {SHIP_SPRITE_PATH}: {e}")

        # Keep the same image_anchor convention
        character.image_anchor = (character.width / 2, 0)

        # Stop normal physics velocity
        character.velocity = [0, 0]

        # Hide the ship sprite itself (character IS the ship now)
        self.visible = False

    def dismount(self):
        """Eject pilot and restore the character's original appearance."""
        if self.pilot is None:
            return

        pilot = self.pilot
        self.pilot = None
        pilot.is_piloting = False
        pilot.velocity = [0, 0]
        pilot.is_on_ground = False

        # Restore character animation back to idle
        pilot.image = pilot.animation["idle"]
        pilot.image_anchor = (pilot.base_w / 2, 0)
        pilot.state = "idle"

        # Show ship sprite again at current position
        self.position = pilot.position
        self.visible = True

    # ------------------------------------------------------------------
    # Key events – routed here by GameScene
    # ------------------------------------------------------------------

    def handle_key_press(self, k, modifiers):
        if self.pilot is None:
            return
        if k == key.W:
            self.pilot.velocity[1] = PLANE_SPEED
        elif k == key.S:
            self.pilot.velocity[1] = -PLANE_SPEED
        elif k == key.A:
            self.pilot.velocity[0] = -PLANE_SPEED
        elif k == key.D:
            self.pilot.velocity[0] = PLANE_SPEED
        elif k == key.SPACE:
            self.dismount()

    def handle_key_release(self, k, modifiers):
        if self.pilot is None:
            return
        if k in (key.W, key.S):
            self.pilot.velocity[1] = 0
        elif k in (key.A, key.D):
            self.pilot.velocity[0] = 0
