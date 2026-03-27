import cocos

class HUDLayer(cocos.layer.Layer):
    def __init__(self):
        super(HUDLayer, self).__init__()
        
        # We need the window size to position it at the top
        win_w, win_h = cocos.director.director.get_window_size()
        
        # Simple HUD text
        self.score_text = cocos.text.Label(
            'Score: 0',
            font_name='Arial',
            font_size=24,
            anchor_x='left', anchor_y='top'
        )
        
        self.score_text.position = (20, win_h - 20)
        self.add(self.score_text)
