import cocos
from cocos.layer import Layer
from cocos.sprite import Sprite
from cocos.tiles import load
from cocos.director import director
import pyglet.window.key as key

class GameScene(Layer):
    # Trong Python, chúng ta thường dùng phím thông qua pyglet
    is_event_handler = True # Tự động đăng ký listener cho bàn phím

    def __init__(self):
        super(GameScene, self).__init__()
        
        # 1. Load TileMap (Sử dụng thư viện tiles của cocos)
        # Lưu ý: map.tmx phải nằm trong cùng thư mục hoặc đúng đường dẫn
        try:
            self.tile_map = load("assets/map.tmx")
            self.add(self.tile_map['Map'], z=0)
        except Exception as e:
            print(f"Lỗi load map: {e}")

        # 2. Tạo Player
        self.player = Sprite("assets/sprite/Blue1.png")
        self.player.position = (100, 100)
        self.add(self.player, z=1)

        # 3. Quản lý vận tốc (Vì cocos-python không có PhysicsBody mặc định)
        self.velocity = [0, 0]
        self.speed = 200
        self.gravity = -500
        self.jump_speed = 300
        
        # Schedule update
        self.schedule(self.update)

    def update(self, dt):
        # Logic vật lý cơ bản (Thay cho PhysicsWorld)
        self.velocity[1] += self.gravity * dt
        
        # Cập nhật vị trí
        x, y = self.player.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt
        
        # Giới hạn mặt đất (Giả lập va chạm đơn giản)
        if new_y < 100:
            new_y = 100
            self.velocity[1] = 0

        self.player.position = (new_x, new_y)

        # 4. Camera follow (Sử dụng set_view)
        # Lưu ý: Trong cocos-python, ta thường di chuyển Layer hoặc dùng scrolling manager
        win_w, win_h = director.get_window_size()
        self.position = (win_w/2 - new_x, win_h/2 - new_y)

    def on_key_press(self, k, modifiers):
        if k == key.LEFT:
            self.velocity[0] = -self.speed
        elif k == key.RIGHT:
            self.velocity[0] = self.speed
        elif k == key.SPACE:
            if self.velocity[1] == 0: # Chỉ nhảy khi đang ở trên đất
                self.velocity[1] = self.jump_speed

    def on_key_release(self, k, modifiers):
        if k in (key.LEFT, key.RIGHT):
            self.velocity[0] = 0