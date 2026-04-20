# NetworkManager.py
"""
Quản lý kết nối mạng cho Nico Park Multiplayer.
Host chạy server + game; Client kết nối và gửi input.

Protocol: JSON over TCP, mỗi message kết thúc bằng '\n'
Message types:
    Client → Server: {"type": "input",  "data": {"keys": [...], "release": [...], "held": [...]}}
  Server → Client: {"type": "state",  "data": <GameState>}
  Server → Client: {"type": "assign", "data": {"player_id": 1|2}}
  Either way:      {"type": "ping"} / {"type": "pong"}
"""

import socket
import threading
import json
import time
from typing import Callable, Optional

PORT = 9999
TICK_RATE = 30          # trạng thái gửi 30 lần/giây
BUFFER_SIZE = 65536


class NetworkManager:
    """Base class dùng chung cho cả Server và Client."""

    def __init__(self):
        self.running = False
        self._recv_callbacks: list[Callable[[dict], None]] = []
        self._connect_callbacks: list[Callable[[], None]] = []
        self._disconnect_callbacks: list[Callable[[], None]] = []

    def on_message(self, callback: Callable[[dict], None]):
        """Đăng ký callback nhận message. Gọi từ main thread."""
        self._recv_callbacks.append(callback)

    def on_connect(self, callback: Callable[[], None]):
        self._connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable[[], None]):
        self._disconnect_callbacks.append(callback)

    def _fire(self, callbacks, *args):
        for cb in callbacks:
            try:
                cb(*args)
            except Exception as e:
                print(f"[Net] callback error: {e}")

    @staticmethod
    def _send_msg(sock: socket.socket, msg: dict):
        try:
            data = (json.dumps(msg) + '\n').encode('utf-8')
            sock.sendall(data)
        except (BrokenPipeError, OSError):
            pass

    @staticmethod
    def _recv_lines(sock: socket.socket):
        """Generator: yield từng JSON line nhận được từ socket."""
        buf = b''
        while True:
            try:
                chunk = sock.recv(BUFFER_SIZE)
                if not chunk:
                    break
                buf += chunk
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    if line:
                        try:
                            yield json.loads(line.decode('utf-8'))
                        except json.JSONDecodeError:
                            pass
            except OSError:
                break


# ---------------------------------------------------------------------------
# SERVER SIDE
# ---------------------------------------------------------------------------

class GameServer(NetworkManager):
    """
    Chạy trên Host. Lắng nghe 1 client kết nối.
    Thread-safe: nhận input từ network thread, gửi state từ main thread.
    """

    def __init__(self, host='0.0.0.0', port=PORT):
        super().__init__()
        self.host = host
        self.port = port
        self._server_sock: Optional[socket.socket] = None
        self._client_sock: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self.client_connected = False

        # Input queue từ network → game logic
        self._pending_inputs: list[dict] = []

    def start(self):
        """Bắt đầu lắng nghe. Non-blocking (chạy trong thread riêng)."""
        self.running = True
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(1)
        print(f"[Server] Đang lắng nghe trên port {self.port}...")
        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()

    def _accept_loop(self):
        try:
            conn, addr = self._server_sock.accept()
            print(f"[Server] Client kết nối từ {addr}")
            with self._lock:
                self._client_sock = conn
                self.client_connected = True
            # Gán player_id cho client
            self._send_msg(conn, {"type": "assign", "data": {"player_id": 2}})
            self._fire(self._connect_callbacks)
            self._recv_loop(conn)
        except OSError:
            pass
        finally:
            self.client_connected = False
            self._fire(self._disconnect_callbacks)
            print("[Server] Client ngắt kết nối.")

    def _recv_loop(self, conn: socket.socket):
        for msg in self._recv_lines(conn):
            if msg.get("type") == "input":
                with self._lock:
                    self._pending_inputs.append(msg["data"])
            elif msg.get("type") == "ping":
                self._send_msg(conn, {"type": "pong"})
            self._fire(self._recv_callbacks, msg)

    def pop_inputs(self) -> list[dict]:
        """Lấy và xoá tất cả input đang chờ (gọi từ game update loop)."""
        with self._lock:
            inputs = self._pending_inputs[:]
            self._pending_inputs.clear()
        return inputs

    def broadcast_state(self, state: dict):
        """Gửi game state đến client (gọi từ game update loop)."""
        with self._lock:
            sock = self._client_sock
        if sock and self.client_connected:
            self._send_msg(sock, {"type": "state", "data": state})

    def stop(self):
        self.running = False
        if self._client_sock:
            try: self._client_sock.close()
            except: pass
        if self._server_sock:
            try: self._server_sock.close()
            except: pass


# ---------------------------------------------------------------------------
# CLIENT SIDE
# ---------------------------------------------------------------------------

class GameClient(NetworkManager):
    """
    Chạy trên Client PC. Kết nối tới Host.
    """

    def __init__(self, host: str, port=PORT):
        super().__init__()
        self.host = host
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self.connected = False
        self.player_id: int = 2  # default, sẽ được assign từ server

        # State mới nhất nhận từ server
        self._latest_state: Optional[dict] = None

    def connect(self):
        """Kết nối tới server. Non-blocking."""
        t = threading.Thread(target=self._connect_loop, daemon=True)
        t.start()

    def _connect_loop(self):
        print(f"[Client] Đang kết nối tới {self.host}:{self.port}...")
        while self.running is not False:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.host, self.port))
                sock.settimeout(None)
                with self._lock:
                    self._sock = sock
                    self.connected = True
                print(f"[Client] Đã kết nối tới server!")
                self._fire(self._connect_callbacks)
                self._recv_loop(sock)
                break
            except (ConnectionRefusedError, socket.timeout) as e:
                print(f"[Client] Không kết nối được: {e}. Thử lại sau 2 giây...")
                time.sleep(2)
        self.connected = False
        self._fire(self._disconnect_callbacks)

    def _recv_loop(self, sock: socket.socket):
        for msg in self._recv_lines(sock):
            if msg.get("type") == "assign":
                self.player_id = msg["data"]["player_id"]
                print(f"[Client] Được gán player_id={self.player_id}")
            elif msg.get("type") == "state":
                with self._lock:
                    self._latest_state = msg["data"]
            elif msg.get("type") == "pong":
                pass
            self._fire(self._recv_callbacks, msg)

    def get_latest_state(self) -> Optional[dict]:
        """Lấy state mới nhất (gọi từ game update loop). Thread-safe."""
        with self._lock:
            return self._latest_state

    def send_input(self, keys_pressed: list[str], keys_released: list[str], held_keys: Optional[list[str]] = None):
        """Gửi input lên server."""
        with self._lock:
            sock = self._sock
        if sock and self.connected:
            payload = {"keys": keys_pressed, "release": keys_released}
            if held_keys is not None:
                payload["held"] = held_keys
            self._send_msg(sock, {
                "type": "input",
                "data": payload
            })

    def start(self):
        self.running = True
        self.connect()

    def stop(self):
        self.running = False
        if self._sock:
            try: self._sock.close()
            except: pass
