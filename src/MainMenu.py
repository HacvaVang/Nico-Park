import cocos
from cocos.menu import Menu, MenuItem, zoom_in, zoom_out, BOTTOM, CENTER
from cocos.scene import Scene
from cocos.director import director
import sys

from .GameScene import create_game_scene

from pyglet import *
try:
    font_loaded = font.add_font('assets/font/BoldsPixels.ttf')
except Exception as e:
    print(f"Could not load font: {e}")

class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__("Nico Park")
        
        # You can override the font that cocos uses:
        self.font_title['font_name'] = 'Pixels'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)
        
        self.font_item['font_name'] = 'Pixels'
        self.font_item['color'] = (200, 200, 200, 255)
        self.font_item['font_size'] = 32
        
        self.font_item_selected['font_name'] = 'Pixels'
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
        self.menu_valign = CENTER
        self.menu_halign = CENTER

        try:
            bg_music = media.load('assets/sound/Bounds.wav', streaming=True)            
            looper = media.SourceGroup(bg_music.audio_format, None)
            looper.loop = True
            looper.queue(bg_music)

            self.bg_player = media.Player()
            self.bg_player.queue(looper)
            self.bg_player.play()


        except Exception as e:
            print(f"Could not load background music: {e}")

    def on_new_game(self):
        # Start the game scene
        print("New Game clicked")
        if hasattr(self, 'bg_player'):
            self.bg_player.pause()
            self.bg_player.delete()        
        game_scene = create_game_scene()
        director.replace(game_scene)
        
    def on_options(self):
        print("Options clicked")
        options_scene = Scene()
        options_scene.add(cocos.layer.ColorLayer(20, 40, 60, 255), z=0)
        options_scene.add(OptionsMenu(), z=1)
        director.push(options_scene)

    def on_about(self):
        print("About clicked")
        about_scene = Scene()
        about_scene.add(cocos.layer.ColorLayer(20, 40, 60, 255), z=0)
        about_scene.add(AboutMenu(), z=1)
        director.push(about_scene)

    def on_exit(self):
        # Exit the application properly
        director.window.close()
        sys.exit(0)

    def on_menu_key_press(self, symbol, modifiers):
        # Phát tiếng 'ting' nhẹ khi đổi item
        # pygame.mixer.Sound("assets/sfx/select.wav").play()
        super(MainMenu, self).on_menu_key_press(symbol, modifiers)

def create_main_menu():
    scene = Scene()
    # Adding a simple colored background
    background = cocos.layer.ColorLayer(20, 40, 60, 255)
    scene.add(background, z=0)
    
    menu = MainMenu()
    scene.add(menu, z=1)
    return scene

class OptionsMenu(Menu):
    def __init__(self):
        super(OptionsMenu, self).__init__("Options")
        
        self.font_title['font_name'] = 'Pixels'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)
        
        self.font_item['font_name'] = 'Pixels'
        self.font_item['color'] = (200, 200, 200, 255)
        self.font_item['font_size'] = 32
        
        self.font_item_selected['font_name'] = 'Pixels'
        self.font_item_selected['color'] = (255, 255, 255, 255)
        self.font_item_selected['font_size'] = 46

        items = []
        items.append(MenuItem('Volume: 100%', self.on_dummy))
        items.append(MenuItem('Fullscreen: Off', self.on_dummy))
        items.append(MenuItem('Back', self.on_back))

        self.create_menu(items, shake(), shake_back())

    def on_dummy(self):
        pass

    def on_back(self):
        director.pop()


class AboutMenu(Menu):
    def __init__(self):
        super(AboutMenu, self).__init__("About")
        
        self.font_title['font_name'] = 'Pixels'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)
        
        self.font_item['font_name'] = 'Pixels'
        self.font_item['color'] = (200, 200, 200, 255)
        self.font_item['font_size'] = 32
        
        self.font_item_selected['font_name'] = 'Pixels'
        self.font_item_selected['color'] = (255, 255, 255, 255)
        self.font_item_selected['font_size'] = 46

        items = []
        items.append(MenuItem('Created by Nico Park Team', self.on_dummy))
        items.append(MenuItem('Version 1.0', self.on_dummy))
        items.append(MenuItem('Back', self.on_back))

        self.create_menu(items, shake(), shake_back())

    def on_dummy(self):
        pass

    def on_back(self):
        director.pop()
