# AppDelegate.py
import cocos
from cocos.director import director
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
        director.show_FPS = True

        scene = create_game_scene()
        director.run(scene)