# MultiplayerGameScene.py
import cocos
from cocos.layer import ScrollingManager
from cocos.tiles import load, RectMapLayer

from .GameScene import GameScene, SoundManager
from .Character import Character
from .MapManager import MapManager
from .GameRules import load_rules
from .NetworkManager import GameServer, GameClient
from .GameStateSerializer import serialize_state, apply_state_to_client
import pyglet.window.key as key

STATE_SEND_INTERVAL = 1.0 / 30

# Thời gian buffer jump: nếu nhận SPACE trong khoảng này trước khi chạm đất
# thì vẫn nhảy được (bù cho network lag)
JUMP_BUFFER_TIME = 0.15


class GhostPlayer(cocos.sprite.Sprite):
    """Hiển thị vị trí player kia, không có physics."""
    def __init__(self, image_path='assets/sprite/Blue1.png'):
        try:
            super().__init__(image_path)
        except Exception:
            super().__init__('assets/AngryNeko.png')
        # Anchor đáy giữa — giống Character
        self.image_anchor = (self.width / 2, 0)
        self.color = (150, 200, 255)
        self.opacity = 200


# ── HOST ──────────────────────────────────────────────────────────────────────

class HostGameScene(GameScene):

    def __init__(self, scroller, map_manager=None, rules=None):
        super().__init__(scroller, map_manager, rules)

        self.player2: Character = None
        self.p2_connected = False
        self._state_timer = 0.0

        # Jump buffer cho player 2: thời gian còn lại của jump request chưa thực hiện
        self._p2_jump_buffer = 0.0

        self.server = GameServer()
        self.server.on_connect(self._on_client_connect)
        self.server.on_disconnect(self._on_client_disconnect)
        self.server.start()
        print("[Host] Chờ player 2 kết nối...")

    def _iter_players(self):
        players = [self.player]
        if self.player2:
            players.append(self.player2)
        return players

    def _on_client_connect(self):
        self.p2_connected = True

    def _on_client_disconnect(self):
        self.p2_connected = False
        if self.player2 and self.player2.parent:
            self.remove(self.player2)
        self.player2 = None
        print("[Host] Player 2 ngắt kết nối.")

    def _spawn_player2(self):
        start = self.map_manager.get_starting_position()
        # Loại bỏ việc cộng 60 pixel
        pos = (start[0], start[1])
        self.player2 = Character(self.map_manager.get_land_collisions(), pos)
        self.player2.color = (150, 200, 255)
        self.add(self.player2, z=1)
        print(f"[Host] Player 2 spawn tại {pos}")

    def update(self, dt):
        if self.p2_connected and self.player2 is None:
            self._spawn_player2()

        # Áp input từ client vào player 2
        if self.player2 and not self.player2.is_die:
            for inp in self.server.pop_inputs():
                for k in inp.get("keys", []):
                    sym = _name_to_sym(k)
                    if sym is None:
                        continue
                    if sym == key.SPACE:
                        # FIX jump: set buffer thay vì gọi handle_key_press ngay
                        # Nếu đang on_ground thì nhảy luôn, không thì buffer lại
                        if self.player2.is_on_ground:
                            self.player2.handle_key_press(sym, 0)
                        else:
                            self._p2_jump_buffer = JUMP_BUFFER_TIME
                    else:
                        self.player2.handle_key_press(sym, 0)
                for k in inp.get("release", []):
                    sym = _name_to_sym(k)
                    if sym is not None:
                        self.player2.handle_key_release(sym, 0)

        # Drain jump buffer: nếu player 2 vừa chạm đất thì nhảy
        if self.player2 and self._p2_jump_buffer > 0:
            self._p2_jump_buffer -= dt
            if self.player2.is_on_ground and not self.player2.is_die:
                self.player2.handle_key_press(key.SPACE, 0)
                self._p2_jump_buffer = 0.0

        # super().update() xử lý toàn bộ logic (gộp p2 qua _iter_players)
        super().update(dt)

        # Gửi state
        if self.p2_connected:
            self._state_timer += dt
            if self._state_timer >= STATE_SEND_INTERVAL:
                self._state_timer = 0.0
                player_map = {self.player: 1}
                if self.player2:
                    player_map[self.player2] = 2
                self.server.broadcast_state(serialize_state(self, player_map))


# ── CLIENT ────────────────────────────────────────────────────────────────────

class ClientGameScene(GameScene):

    def __init__(self, scroller, map_manager, server_ip: str, rules=None):
        super().__init__(scroller, map_manager, rules)

        self.ghost_players: dict[int, GhostPlayer] = {}
        ghost1 = GhostPlayer()
        ghost1.position = self.player.position
        self.add(ghost1, z=1)
        self.ghost_players[1] = ghost1

        self._keys_pressed: set[str] = set()

        self.client = GameClient(server_ip)
        self.client.on_connect(lambda: print("[Client] Đã kết nối!"))
        self.client.on_disconnect(lambda: print("[Client] Mất kết nối."))
        self.client.start()

    def update(self, dt):
        state = self.client.get_latest_state()
        if state:
            apply_state_to_client(state, self, local_player_id=2)
        super().update(dt)

    def on_key_press(self, k, modifiers):
        name = _sym_to_name(k)
        if name:
            self._keys_pressed.add(name)
            self.client.send_input([name], [])
        super().on_key_press(k, modifiers)

    def on_key_release(self, k, modifiers):
        name = _sym_to_name(k)
        if name and name in self._keys_pressed:
            self._keys_pressed.discard(name)
            self.client.send_input([], [name])
        super().on_key_release(k, modifiers)


# ── Key helpers ───────────────────────────────────────────────────────────────

_KEY_MAP = {
    'LEFT': key.LEFT, 'RIGHT': key.RIGHT,
    'UP': key.UP, 'DOWN': key.DOWN,
    'SPACE': key.SPACE,
    'Z': key.Z, 'X': key.X,
    'W': key.W, 'A': key.A, 'D': key.D,
}
_REV = {v: k for k, v in _KEY_MAP.items()}

def _sym_to_name(sym):  return _REV.get(sym)
def _name_to_sym(name): return _KEY_MAP.get(name.upper())


# ── Factory functions ─────────────────────────────────────────────────────────

def create_host_scene(map_path: str = "assets/map.tmx") -> cocos.scene.Scene:
    main_scene = cocos.scene.Scene()
    main_scene.add(cocos.layer.ColorLayer(255, 255, 255, 255), z=-1)
    scroller = ScrollingManager()
    for name, layer in load(map_path).find(RectMapLayer):
        scroller.add(layer, z=0)
    map_manager = MapManager(map_path)
    game_layer = HostGameScene(scroller, map_manager, rules=load_rules())
    scroller.add(game_layer, z=1)
    from .HUD import HUDLayer
    hud = HUDLayer()
    game_layer.hud_layer = hud
    main_scene.add(hud, z=2)
    main_scene.add(scroller, z=0)
    SoundManager.play_bgm('assets/sound/Hands.wav')
    return main_scene


def create_client_scene(server_ip: str, map_path: str = "assets/map.tmx") -> cocos.scene.Scene:
    main_scene = cocos.scene.Scene()
    main_scene.add(cocos.layer.ColorLayer(255, 255, 255, 255), z=-1)
    scroller = ScrollingManager()
    for name, layer in load(map_path).find(RectMapLayer):
        scroller.add(layer, z=0)
    map_manager = MapManager(map_path)
    game_layer = ClientGameScene(scroller, map_manager, server_ip, rules=load_rules())
    scroller.add(game_layer, z=1)
    from .HUD import HUDLayer
    hud = HUDLayer()
    game_layer.hud_layer = hud
    main_scene.add(hud, z=2)
    main_scene.add(scroller, z=0)
    SoundManager.play_bgm('assets/sound/Hands.wav')
    return main_scene