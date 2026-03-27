import cocos
from cocos.menu import Menu, MenuItem, zoom_in, zoom_out
from cocos.scene import Scene
from cocos.director import director
import sys

from .GameScene import create_game_scene

class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__("Nico Park")
        
        # You can override the font that cocos uses:
        self.font_title['font_name'] = 'Arial'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)
        
        self.font_item['font_name'] = 'Arial'
        self.font_item['color'] = (200, 200, 200, 255)
        self.font_item['font_size'] = 32
        
        self.font_item_selected['font_name'] = 'Arial'
        self.font_item_selected['color'] = (255, 255, 255, 255)
        self.font_item_selected['font_size'] = 46

        # Item Definitions
        items = []
        items.append(MenuItem('New Game', self.on_new_game))
        items.append(MenuItem('Options', self.on_options))
        items.append(MenuItem('About', self.on_about))
        items.append(MenuItem('Exit', self.on_exit))

        # Add items to the menu
        self.create_menu(items, zoom_in(), zoom_out())

    def on_new_game(self):
        # Start the game scene
        game_scene = create_game_scene()
        director.replace(game_scene)

    def on_options(self):
        print("Options clicked")
        # In the future, transition to an OptionsScene

    def on_about(self):
        print("About clicked")
        # In the future, transition to an AboutScene

    def on_exit(self):
        # Exit the application properly
        director.window.close()
        sys.exit(0)

def create_main_menu():
    scene = Scene()
    # Adding a simple colored background
    background = cocos.layer.ColorLayer(20, 40, 60, 255)
    scene.add(background, z=0)
    
    menu = MainMenu()
    scene.add(menu, z=1)
    return scene
