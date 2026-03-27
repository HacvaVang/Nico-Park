import cocos
from cocos.layer import ColorLayer

BULLET_SPEED = 400
BULLET_DAMAGE = 5

class Bullet(cocos.cocosnode.CocosNode):
    def __init__(self, position, direction):
        super(Bullet, self).__init__()
        self.position = position
        self.direction = direction
        self.damage = BULLET_DAMAGE
        self.dead = False

        # Vẽ hình chữ nhật xanh
        self.rect_visual = cocos.draw.Canvas()
        w, h = 12, 6
        self.rect_visual = cocos.layer.ColorLayer(0, 150, 255, 255, width=w, height=h)
        self.rect_visual.position = (-w//2, -h//2)
        self.add(self.rect_visual)

        self.w = w
        self.h = h
        self.schedule(self.update)

    def update(self, dt):
        x, y = self.position
        self.position = (x + BULLET_SPEED * self.direction * dt, y)

    def get_hitbox(self):
        x, y = self.position
        return cocos.rect.Rect(x - self.w//2, y - self.h//2, self.w, self.h)