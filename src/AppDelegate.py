# AppDelegate.py
import cocos
from cocos.director import director
from .MainMenu import create_main_menu
from .GameScene import create_game_scene


class AppDelegate:
    def __init__(self):
        self.application_did_finish_launching()

    def application_did_finish_launching(self):
        director.init(
            width=960,
            height=640,
            caption="Nico Park",
            resizable=False
        )
        menu = False

        scene = create_main_menu() if menu else create_game_scene()
        director.run(scene)