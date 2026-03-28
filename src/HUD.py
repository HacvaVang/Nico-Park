import cocos

class HUDLayer(cocos.layer.Layer):
    def __init__(self):
        super(HUDLayer, self).__init__()
        
        self.win_w, self.win_h = cocos.director.director.get_window_size()
        
        # Simple HUD text
        self.score_text = cocos.text.Label(
            'Score: 0',
            font_name='Arial',
            font_size=24,
            anchor_x='left', anchor_y='top'
        )
        
        self.score_text.position = (20, self.win_h - 20)
        self.add(self.score_text)

        # Boss HP bar background
        self.boss_hp_bg = cocos.layer.ColorLayer(50, 50, 50, 255, width=400, height=20)
        self.boss_hp_bg.position = (self.win_w // 2 - 200, self.win_h - 40)
        self.boss_hp_bg.visible = False
        self.add(self.boss_hp_bg, z=0)

        # Boss HP bar foreground
        self.boss_hp_bar = cocos.layer.ColorLayer(255, 0, 0, 255, width=400, height=20)
        self.boss_hp_bar.position = (self.win_w // 2 - 200, self.win_h - 40)
        self.boss_hp_bar.visible = False
        self.add(self.boss_hp_bar, z=1)

        # Boss HP text
        self.boss_hp_label = cocos.text.Label(
            "BOSS",
            font_name='Pixels', # Same font as other game texts
            font_size=24,
            color=(255, 255, 255, 255),
            anchor_x='center', anchor_y='center'
        )
        self.boss_hp_label.position = (self.win_w // 2, self.win_h - 30)
        self.boss_hp_label.visible = False
        self.add(self.boss_hp_label, z=2)

    def update_boss_hp(self, health, max_health):
        if not self.boss_hp_bar.visible and health > 0:
            self.boss_hp_bg.visible = True
            self.boss_hp_bar.visible = True
            self.boss_hp_label.visible = True

        if health <= 0:
            self.boss_hp_bg.visible = False
            self.boss_hp_bar.visible = False
            self.boss_hp_label.visible = False
            return

        ratio = max(0, health / max_health)
        self.boss_hp_bar.scale_x = ratio
