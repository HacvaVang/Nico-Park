import cocos
from cocos.layer import ColorLayer
BULLET_SPEED = 400
BULLET_DAMAGE = 5
BULLET_MAX_DISTANCE = 800   # 👈 khoảng cách tối đa (tuỳ chỉnh)

class Bullet(cocos.cocosnode.CocosNode):
    def __init__(self, position, direction):
        super(Bullet, self).__init__()
        self.start_x, self.start_y = position  # 👈 lưu vị trí ban đầu
        self.position = position
        self.direction = direction
        self.damage = BULLET_DAMAGE
        self.scale = 2
        self.dead = False

        # Vẽ hình chữ nhật xanh
        w, h = 12, 6
        self.rect_visual = cocos.layer.ColorLayer(0, 150, 255, 255, width=w, height=h)
        self.rect_visual.position = (-w//2, -h//2)
        self.add(self.rect_visual)

        self.w = w
        self.h = h
        self.schedule(self.update)

    def update(self, dt):
        if self.dead:
            return

        x, y = self.position
        new_x = x + BULLET_SPEED * self.direction * dt
        self.position = (new_x, y)

        # 👇 tính khoảng cách đã bay
        distance = abs(new_x - self.start_x)

        if distance >= BULLET_MAX_DISTANCE:
            # Debug nếu muốn
            print("Bullet reached max distance -> destroyed")

            self.dead = True
            self.kill()

    def get_hitbox(self):
        x, y = self.position
        return cocos.rect.Rect(x - self.w//2, y - self.h//2, self.w, self.h)