# MultiplayerGameScene.py
"""
Mở rộng GameScene để hỗ trợ multiplayer co-op.

HOST:
  - Chạy toàn bộ game logic như bình thường
  - Spawn thêm Player 2 (ghost) khi client kết nối
  - Áp dụng input của Player 2 vào character tương ứng
  - Gửi state snapshot mỗi TICK_RATE lần/giây

CLIENT:
  - Chạy GameScene tối giản (render-only)
  - Điều khiển Player 2 cục bộ, gửi input lên host
  - Nhận state từ host và cập nhật vị trí tất cả entities
  - Player 1 (host) hiển thị như ghost
"""

import cocos
from cocos.layer import ScrollingManager
from cocos.tiles import load, RectMapLayer
import pyglet.window.key as key

from .GameScene import GameScene, SoundManager
from .Character import Character
from .MapManager import MapManager
from .NetworkManager import GameServer, GameClient
from .GameStateSerializer import serialize_state, apply_state_to_client
from .GameRules import load_rules

# Tốc độ gửi state (giây)
STATE_SEND_INTERVAL = 1.0 / 30   # 30Hz


# ---------------------------------------------------------------------------
# GHOST SPRITE (hiển thị player kia, không có collision logic)
# ---------------------------------------------------------------------------

class GhostPlayer(cocos.sprite.Sprite):
    """
    Sprite đơn giản hiển thị vị trí player của người chơi kia.
    Không có physics, chỉ dùng để render.
    """
    def __init__(self, image_path='assets/sprite/Blue1.png', tint=(255, 180, 180, 220)):
        try:
            super().__init__(image_path)
        except Exception:
            # Fallback nếu ảnh không tìm thấy
            super().__init__('assets/AngryNeko.png')
        # Character thật dùng bottom anchor (x=center, y=0),
        # nên ghost cũng phải dùng anchor tương tự để không bị lún/nổi.
        self.image_anchor = (self.width / 2, 0)
        self.scale = 1.0
        self.color = tint[:3]
        self.opacity = tint[3]


# ---------------------------------------------------------------------------
# HOST GAME SCENE
# ---------------------------------------------------------------------------

class HostGameScene(GameScene):
    """
    GameScene cho Host. Quản lý server và player 2.
    """

    def __init__(self, scroller, map_manager: MapManager = None):
        super().__init__(scroller, map_manager, rules=load_rules())

        # Player 2 character (spawn khi client kết nối)
        self.player2: Character = None
        self.p2_connected = False
        self.p2_active_ship = None

        # State send timer
        self._state_timer = 0.0
        self._p2_held_keys: set[str] = set()

        # Khởi động server
        self.server = GameServer()
        self.server.on_connect(self._on_client_connect)
        self.server.on_disconnect(self._on_client_disconnect)
        self.server.start()

        print("[Host] Server khởi động. Chờ player 2 kết nối...")

    def _on_client_connect(self):
        """Gọi từ network thread khi client kết nối."""
        print("[Host] Player 2 đã kết nối! Spawn character...")
        self.p2_connected = True
        # Spawn sẽ thực hiện ở update loop (main thread)

    def _on_client_disconnect(self):
        """Gọi từ network thread khi client ngắt kết nối."""
        print("[Host] Player 2 ngắt kết nối.")
        self.p2_connected = False
        try:
            self.server._pending_inputs.clear()
        except Exception:
            pass
        self._p2_held_keys.clear()
        self.p2_active_ship = None
        if self.player2 and self.player2.parent:
            self.remove(self.player2)
            self.player2 = None

    def _spawn_player2(self):
        """Tạo Player 2 tại vị trí bắt đầu (gọi từ main thread)."""
        start_pos = self.map_manager.get_starting_position()
        # Offset nhỏ để không chồng lên player 1
        offset_pos = (start_pos[0] + 60, start_pos[1])
        self.player2 = Character(
            self.map_manager.get_land_collisions(),
            offset_pos
        )
        # Tô màu xanh nhạt để phân biệt
        self.player2.color = (150, 200, 255)
        self.add(self.player2, z=1)
        print(f"[Host] Player 2 spawn tại {offset_pos}")

    def update(self, dt):
        # Spawn player 2 nếu cần (main thread safe)
        if self.p2_connected and self.player2 is None:
            self._spawn_player2()

        # Áp dụng input của player 2
        if self.player2 and not self.player2.is_die:
            self._apply_p2_inputs()

        # Game logic bình thường cho player 1
        super().update(dt)

        # Gửi state định kỳ
        if self.p2_connected:
            self._state_timer += dt
            if self._state_timer >= STATE_SEND_INTERVAL:
                self._state_timer = 0
                self._send_state()

    def _apply_p2_inputs(self):
        """Lấy input từ server và áp dụng vào player 2."""
        inputs = self.server.pop_inputs()
        for inp in inputs:
            held = inp.get("held")
            if held is not None:
                new_held = set(held)
                for k in sorted(new_held - self._p2_held_keys):
                    self._handle_p2_key(k, press=True)
                for k in sorted(self._p2_held_keys - new_held):
                    self._handle_p2_key(k, press=False)
                self._p2_held_keys = new_held

            for k in inp.get("keys", []):
                self._handle_p2_key(k, press=True)
            for k in inp.get("release", []):
                self._handle_p2_key(k, press=False)

    def _iter_players(self):
        players = [self.player]
        if self.player2:
            players.append(self.player2)
        return players

    def _send_state(self):
        player_map = {self.player: 1}
        if self.player2:
            player_map[self.player2] = 2
        state = serialize_state(self, player_map)
        self.server.broadcast_state(state)

    def on_key_press(self, k, modifiers):
        """Chỉ player 1 (host) điều khiển từ bàn phím cục bộ."""
        super().on_key_press(k, modifiers)

    def on_key_release(self, k, modifiers):
        super().on_key_release(k, modifiers)

    def _handle_p2_key(self, key_name: str, press: bool):
        k = _key_name_to_sym(key_name)
        if k is None or self.player2 is None:
            return

        # Nếu đang lái ship, điều khiển ship trước
        if self.p2_active_ship is not None:
            if press:
                self.p2_active_ship.handle_key_press(k, 0)
                if self.p2_active_ship.pilot is None:
                    self.p2_active_ship = None
            else:
                self.p2_active_ship.handle_key_release(k, 0)
            return

        # On-foot: W để lên tàu tương tự player 1
        if press and k == key.W:
            for ship in self.ships:
                if ship.check_interaction(self.player2):
                    ship.mount(self.player2)
                    self.p2_active_ship = ship
                    return

        if press:
            self.player2.handle_key_press(k, 0)
        else:
            self.player2.handle_key_release(k, 0)

    def on_level_cleared(self):
        if self.level_cleared:
            return
        super().on_level_cleared()

    def on_exit(self):
        try:
            self.server.stop()
        except Exception:
            pass
        super().on_exit()


# ---------------------------------------------------------------------------
# CLIENT GAME SCENE
# ---------------------------------------------------------------------------

class ClientGameScene(GameScene):
    """
    GameScene cho Client. Render-only với local player 2 control.
    """

    def __init__(self, scroller, map_manager: MapManager, server_ip: str):
        super().__init__(scroller, map_manager, rules=load_rules())
        self.player.color = (150, 200, 255)

        # Ghost players: {player_id: GhostPlayer}
        self.ghost_players: dict[int, GhostPlayer] = {}

        # Tạo ghost cho player 1 (host)
        ghost1 = GhostPlayer()
        ghost1.position = self.player.position
        self.add(ghost1, z=1)
        self.ghost_players[1] = ghost1

        # Client replica: tắt AI/update tự thân của entities để tránh lệch host.
        for mob in self.mobs:
            try:
                mob.unschedule(mob.update)
            except Exception:
                pass
        for boss in self.bosses:
            try:
                boss.unschedule(boss.update)
            except Exception:
                pass
        for obs in self.obstacles:
            try:
                obs.unschedule(obs.update)
            except Exception:
                pass

        # Input tracking
        self._keys_pressed: set[str] = set()
        self._input_sync_timer = 0.0

        # Kết nối tới server
        self.client = GameClient(server_ip)
        self.client.on_connect(self._on_connected)
        self.client.on_disconnect(self._on_disconnected)
        self.client.start()

        print(f"[Client] Đang kết nối tới {server_ip}...")

    def _on_connected(self):
        print("[Client] Kết nối thành công!")

    def _on_disconnected(self):
        print("[Client] Mất kết nối với host.")

    def update(self, dt):
        # Nhận và áp dụng state từ server
        state = self.client.get_latest_state()
        if state:
            apply_state_to_client(state, self, local_player_id=2)

        # Client không chạy full world logic để tránh lệch state với host.
        # Character.update vẫn tự chạy (được schedule trong Character),
        # nên prediction di chuyển local vẫn mượt.
        self.scroller.set_focus(self.player.position[0], self.player.position[1])

        self._input_sync_timer += dt
        if self._input_sync_timer >= 0.1:
            self._input_sync_timer = 0.0
            self.client.send_input([], [], list(self._keys_pressed))

    def _should_evaluate_level_clear(self):
        # Client nhận trạng thái hoàn thành màn từ host authoritative
        return False

    def on_level_cleared(self):
        if self.level_cleared:
            return
        super().on_level_cleared()

    def on_exit(self):
        try:
            # Nhả toàn bộ phím đang giữ trước khi ngắt kết nối để tránh kẹt input trên host
            if self._keys_pressed:
                self.client.send_input([], list(self._keys_pressed), [])
                self._keys_pressed.clear()
            self.client.stop()
        except Exception:
            pass
        super().on_exit()

    def on_key_press(self, k, modifiers):
        key_name = _key_sym_to_name(k)
        if key_name:
            self._keys_pressed.add(key_name)
            self.client.send_input([key_name], [], list(self._keys_pressed))
        # Điều khiển player 2 cục bộ (client-side prediction)
        super().on_key_press(k, modifiers)

    def on_key_release(self, k, modifiers):
        key_name = _key_sym_to_name(k)
        if key_name:
            if key_name in self._keys_pressed:
                self._keys_pressed.discard(key_name)
            self.client.send_input([], [key_name], list(self._keys_pressed))
        super().on_key_release(k, modifiers)

    def on_deactivate(self):
        if self._keys_pressed:
            released = list(self._keys_pressed)
            self._keys_pressed.clear()
            self.client.send_input([], released, [])
        return True


# ---------------------------------------------------------------------------
# KEY MAPPING HELPERS
# ---------------------------------------------------------------------------

_KEY_MAP = {
    'LEFT':  key.LEFT,
    'RIGHT': key.RIGHT,
    'UP':    key.UP,
    'DOWN':  key.DOWN,
    'SPACE': key.SPACE,
    'Z':     key.Z,
    'X':     key.X,
    'W':     key.W,
    'S':     key.S,
    'A':     key.A,
    'D':     key.D,
}
_REV_KEY_MAP = {v: k for k, v in _KEY_MAP.items()}


def _key_sym_to_name(sym: int) -> str | None:
    return _REV_KEY_MAP.get(sym)


def _key_name_to_sym(name: str) -> int | None:
    return _KEY_MAP.get(name.upper())


# ---------------------------------------------------------------------------
# FACTORY FUNCTIONS
# ---------------------------------------------------------------------------

def create_host_scene(map_path: str = "assets/map.tmx") -> cocos.scene.Scene:
    """Tạo scene cho Host (chạy server + game)."""
    main_scene = cocos.scene.Scene()
    bg_color = (255, 255, 255, 255)
    main_scene.add(cocos.layer.ColorLayer(*bg_color), z=-1)

    scroller = ScrollingManager()
    tile_map = load(map_path)
    for name, layer in tile_map.find(RectMapLayer):
        scroller.add(layer, z=0)

    map_manager = MapManager(map_path)
    game_layer = HostGameScene(scroller, map_manager)
    scroller.add(game_layer, z=1)

    from .HUD import HUDLayer
    hud = HUDLayer()
    game_layer.hud_layer = hud
    main_scene.add(hud, z=2)
    main_scene.add(scroller, z=0)

    SoundManager.play_bgm('assets/sound/Hands.wav')
    return main_scene


def create_client_scene(server_ip: str, map_path: str = "assets/map.tmx") -> cocos.scene.Scene:
    """Tạo scene cho Client (kết nối tới host)."""
    main_scene = cocos.scene.Scene()
    bg_color = (255, 255, 255, 255)
    main_scene.add(cocos.layer.ColorLayer(*bg_color), z=-1)

    scroller = ScrollingManager()
    tile_map = load(map_path)
    for name, layer in tile_map.find(RectMapLayer):
        scroller.add(layer, z=0)

    map_manager = MapManager(map_path)
    game_layer = ClientGameScene(scroller, map_manager, server_ip)
    scroller.add(game_layer, z=1)

    from .HUD import HUDLayer
    hud = HUDLayer()
    game_layer.hud_layer = hud
    main_scene.add(hud, z=2)
    main_scene.add(scroller, z=0)

    SoundManager.play_bgm('assets/sound/Hands.wav')
    return main_scene
