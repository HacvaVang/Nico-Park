from enum import Enum
import cocos
from cocos.sprite import Sprite

class TypeButton(Enum):
    ActivateObj = 0
    StretchVertical = 1
    StretchHorizontal = 2
    Prohibited = 3
    
class Button(Sprite):
    def __init__(self, image, position, button_type: TypeButton = TypeButton.ActivateObj):
        super(Button, self).__init__(image)
        self.type = button_type
        self.position = position
        self.onStatus = True
        self.scale = 1.0
        
    def activate(self):
        """Called when the button is activated/pressed."""
        self.onStatus = not self.onStatus
        # Toggle visual state if needed
        if self.onStatus:
            self.color = (255, 255, 255) # Default
        else:
            self.color = (150, 150, 150) # Pressed/Deactivated
            
    def check_interaction(self, character):
        """Check if character is interacting with this button"""
        # Simple distance-based interaction check
        cx, cy = character.position
        bx, by = self.position
        dist_sq = (cx - bx)**2 + (cy - by)**2
        
        # If character is within 50 pixels
        if dist_sq < 2500:
            self.activate()
            return True
        return False
