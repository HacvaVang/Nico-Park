import cocos
from cocos.sprite import Sprite
from enum import Enum

class ItemType(Enum):
    COIN = 0
    HEALTH_POTION = 1
    KEY = 2

class Item(Sprite):
    """
    Template for a generic collectable Item.
    """
    def __init__(self, position, item_type: ItemType = ItemType.COIN, image="assets/sprite/Blue1.png"): # Placeholder image
        super(Item, self).__init__(image)
        self.position = position
        self.item_type = item_type
        
        # Items are usually centered
        self.base_w = self.width
        self.base_h = self.height
        self.anchor = (self.base_w / 2, self.base_h / 2)
        self.image_anchor = (self.base_w / 2, self.base_h / 2)

        self.schedule(self.update)

    def update(self, dt):
        """Implement idle animations (bobbing up and down, spinning) here."""
        pass

    def get_hitbox(self):
        """Returns the interaction bounds of the item."""
        w = self.base_w * self.scale
        h = self.base_h * self.scale
        x, y = self.position
        # Adjusted for Center Anchor
        return cocos.rect.Rect(x - w/2, y - h/2, w, h)
        
    def on_collect(self, character):
        """Triggered when the character acts over the item."""
        if self.item_type == ItemType.COIN:
            print("Coin collected!")
        elif self.item_type == ItemType.HEALTH_POTION:
            print("Healed!")
            
        # Remove item from the scene once collected
        self.kill()
