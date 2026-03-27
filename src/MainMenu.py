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

class SoundManager:
    _instance = None
    player = None

    @classmethod
    def get_player(cls):
        if cls.player is None:
            cls.player = media.Player()
        return cls.player

    @classmethod
    def play_bgm(cls, path):
        try:
            player = cls.get_player()
            if player.source: # Don't restart if already playing
                return
            
            music = media.load(path, streaming=True)
            looper = media.SourceGroup(music.audio_format, None)
            looper.loop = True
            looper.queue(music)
            
            player.queue(looper)
            player.play()
        except Exception as e:
            print(f"Audio Error: {e}")

# 2. UPDATED MAIN MENU
class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__("Nico Park")
        
        # UI Styles
        self.font_title.update({'font_name': 'Pixels', 'font_size': 72})
        self.font_item.update({'font_name': 'Pixels', 'font_size': 32})
        self.font_item_selected.update({'font_name': 'Pixels', 'font_size': 46})

        items = [
            MenuItem('New Game', self.on_new_game),
            MenuItem('Options', self.on_options),
            MenuItem('About', self.on_about),
            MenuItem('Exit', self.on_exit)
        ]

        self.create_menu(items, zoom_in(), zoom_out())
        
        # Start music safely via SoundManager
        SoundManager.play_bgm('assets/sound/Bounds.wav')

    def on_new_game(self):
        # Stop music before heavy scene loading
        if SoundManager.player:
            SoundManager.player.pause() 
        director.push(create_game_scene())

    def on_options(self):
        # Use push with a tiny delay to let OpenGL breathe
        clock.schedule_once(lambda dt: director.push(Scene(OptionsMenu())), 0.01)

    def on_about(self):
        clock.schedule_once(lambda dt: director.push(Scene(AboutMenu())), 0.01)

    def on_exit(self):
        print("exit")
        director.terminate_app = True



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

        self.create_menu(items, zoom_in(), zoom_out())

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
        items.append(MenuItem('Game nhái Pico Park', self.on_dummy))
        items.append(MenuItem('Version 1.0', self.on_dummy))
        items.append(MenuItem('Back', self.on_back))

        self.create_menu(items, zoom_in(), zoom_out())

    def on_dummy(self):
        pass

    def on_back(self):
        director.pop()

def create_main_menu():
    scene = Scene()
    # Adding a simple colored background
    background = cocos.layer.ColorLayer(20, 40, 60, 255)
    scene.add(background, z=0)
    
    menu = MainMenu()
    scene.add(menu, z=1)
    return scene