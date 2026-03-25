import cocos
from cocos.director import director
from .GameScene import GameScene

class AppDelegate:
    def __init__(self):
        # Tương đương applicationDidFinishLaunching
        self.application_did_finish_launching()

    def application_did_finish_launching(self):
        director.init(
            width=960, 
            height=640, 
            caption="Nico Park",
            resizable=False
        )

        director.show_FPS = True

        import cocos.scene
        scene = cocos.scene.Scene(GameScene()) 
        
        director.run(scene)