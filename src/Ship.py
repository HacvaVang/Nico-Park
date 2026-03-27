import cocos
from cocos.sprite import Sprite

class Ship(Sprite):
    """
    Template for a Ship or vehicle.
    Could act as a platform, a rideable entity, or an interactive background element.
    """
    def __init__(self, position, image="assets/sprite/Blue1.png"): # Placeholder image
        super(Ship, self).__init__(image)
        self.position = position
        
        # Define base dimensions for collision/interaction
        self.base_w = self.width
        self.base_h = self.height
        
        # Anchor
        self.anchor = (self.base_w / 2, 0)
        self.image_anchor = (self.base_w / 2, 0)

        self.schedule(self.update)

    def update(self, dt):
        """Implement floating mechanics, flying, or player-mounting logic here."""
        pass

    def get_hitbox(self):
        w = self.base_w * self.scale
        h = self.base_h * self.scale
        x, y = self.position
        return cocos.rect.Rect(x - w/2, y, w, h)
