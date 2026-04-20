# MultiplayerMenu.py
"""
Menu chọn chế độ chơi:
  - Single Player  → game bình thường
  - Host Game      → chạy server + game
  - Join Game      → nhập IP, kết nối tới host
"""

import cocos
from cocos.menu import Menu, MenuItem, zoom_in, zoom_out, CENTER
from cocos.scene import Scene
from cocos.director import director
from cocos.layer import ColorLayer
import cocos.text
import pyglet.window.key as key

from .GameScene import SoundManager


# ---------------------------------------------------------------------------
# IP INPUT LAYER (cho Join Game)
# ---------------------------------------------------------------------------

class IPInputLayer(cocos.layer.Layer):
    """Layer nhập địa chỉ IP của host."""
    is_event_handler = True

    def __init__(self):
        super().__init__()
        w, h = director.get_window_size()

        self.ip_text = "192.168.1."  # gợi ý mặc định
        self._on_confirm = None

        # Background mờ
        bg = ColorLayer(0, 0, 0, 180)
        self.add(bg, z=0)

        # Box nền
        box = ColorLayer(20, 40, 60, 240, width=500, height=200)
        box.position = (w // 2 - 250, h // 2 - 100)
        self.add(box, z=1)

        # Label tiêu đề
        self.title_label = cocos.text.Label(
            "Nhập IP của Host:",
            font_name='Pixels',
            font_size=28,
            color=(255, 255, 255, 255),
            anchor_x='center', anchor_y='center'
        )
        self.title_label.position = (w // 2, h // 2 + 40)
        self.add(self.title_label, z=2)

        # Label IP đang nhập
        self.ip_label = cocos.text.Label(
            self.ip_text + "|",
            font_name='Pixels',
            font_size=32,
            color=(100, 220, 255, 255),
            anchor_x='center', anchor_y='center'
        )
        self.ip_label.position = (w // 2, h // 2 - 10)
        self.add(self.ip_label, z=2)

        # Hint
        hint = cocos.text.Label(
            "Enter để kết nối  |  Esc để quay lại",
            font_name='Pixels',
            font_size=16,
            color=(160, 160, 160, 255),
            anchor_x='center', anchor_y='center'
        )
        hint.position = (w // 2, h // 2 - 60)
        self.add(hint, z=2)

    def on_key_press(self, k, modifiers):
        if k == key.BACKSPACE:
            self.ip_text = self.ip_text[:-1]
        elif k == key.RETURN or k == key.ENTER:
            ip = self.ip_text.strip()
            if ip and self._on_confirm:
                self._on_confirm(ip)
            return True
        elif k == key.ESCAPE:
            director.pop()
            return True
        self._refresh()
        return True

    def on_text(self, text):
        allowed = '0123456789.'
        for ch in text:
            if ch in allowed:
                self.ip_text += ch
        self._refresh()

    def _refresh(self):
        self.ip_label.element.text = self.ip_text + "|"


# ---------------------------------------------------------------------------
# MULTIPLAYER MENU
# ---------------------------------------------------------------------------

class MultiplayerMenu(Menu):
    def __init__(self):
        super().__init__("Nico Park")

        self.font_title['font_name'] = 'Pixels'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)

        self.font_item['font_name'] = 'Pixels'
        self.font_item['color'] = (200, 200, 200, 255)
        self.font_item['font_size'] = 32

        self.font_item_selected['font_name'] = 'Pixels'
        self.font_item_selected['color'] = (255, 255, 255, 255)
        self.font_item_selected['font_size'] = 46

        self.is_action_taken = False

        items = [
            MenuItem('Single Player', self.on_single_player),
            MenuItem('Host Game',     self.on_host_game),
            MenuItem('Join Game',     self.on_join_game),
            MenuItem('Exit',          self.on_exit),
        ]

        self.create_menu(items, zoom_in(), zoom_out())
        self.menu_valign = CENTER
        self.menu_halign = CENTER
        SoundManager.play_bgm('assets/sound/Bounds.wav')

    def on_enter(self):
        super().on_enter()
        self.is_action_taken = False

    def on_single_player(self):
        if self.is_action_taken: return
        self.is_action_taken = True
        from .GameScene import create_game_scene
        director.replace(create_game_scene())

    def on_host_game(self):
        if self.is_action_taken: return
        self.is_action_taken = True
        print("[Menu] Khởi động chế độ Host...")
        from .MultiplayerGameScene import create_host_scene
        director.replace(create_host_scene())

    def on_join_game(self):
        if self.is_action_taken: return
        self.is_action_taken = True

        # Hiện màn hình nhập IP
        ip_scene = Scene()
        ip_scene.add(ColorLayer(20, 40, 60, 255), z=0)

        input_layer = IPInputLayer()

        def do_connect(ip: str):
            print(f"[Menu] Kết nối tới {ip}...")
            from .MultiplayerGameScene import create_client_scene
            director.replace(create_client_scene(ip))

        input_layer._on_confirm = do_connect
        ip_scene.add(input_layer, z=1)
        director.push(ip_scene)

    def on_exit(self):
        if self.is_action_taken: return
        self.is_action_taken = True
        import sys
        director.window.close()
        sys.exit(0)


def create_multiplayer_menu() -> Scene:
    """Thay thế create_main_menu() trong AppDelegate."""
    scene = Scene()
    scene.add(ColorLayer(20, 40, 60, 255), z=0)
    scene.add(MultiplayerMenu(), z=1)
    return scene
