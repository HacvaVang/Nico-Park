import cocos
from cocos.sprite import Sprite
import pyglet.window.key as key
from enum import Enum
from .Button import TypeButton, Button
import pyglet

class CharacterState(Enum):
    IDLE = 0
    RUN = 1
    ON_AIR = 2
    DEATH = 3

WALK_ANIM = ["Blue3.png", "Blue4.png", "Blue5.png"]
JUMP_ANIM = ["Blue6.png"]
IDLE_ANIM = ["Blue1.png", "Blue11.png"]


class Character(Sprite):
    def __init__(self, collision_boxes = None, start_pos = None):
        self.animation = self.load_animation()
        super(Character, self).__init__(image = self.animation["idle"],position=start_pos)
        self.checkpoint = start_pos or (0, 0)
        self.collision_boxes = collision_boxes
        self.velocity = [0, 0]
        self.speed = 250
        self.gravity = -600
        self.jump_speed = 350
        self.is_on_ground = False
        self.minimum_scale = 0.5
        self.maximum_scale = 2.5
        self.state = "idle"
        self.is_die = False
        self.is_piloting = False   # True while riding the Ship
        self.has_gun = False
        self.gun_sprite = None
        self.shoot_cooldown = 0.3
        self.shoot_timer = 0

        # Store unscaled base dimensions — used for all physics/collision math
        # self.width/height return SCALED values so we must cache the originals
        self.base_w = self.width
        self.base_h = self.height

        # Smooth scale: set target_scale to animate toward instead of setting self.scale directly
        self.target_scale = 1.0
        self.scale_speed = 0.05

        #self.anchor = (self.base_w / 2, 0)
        self.image_anchor = (self.base_w / 2, 0)

        # Current collision rects (updated every frame in update())
        self.rect_x   = cocos.rect.Rect(0, 0, self.base_w, self.base_h)
        self.leg_rect  = cocos.rect.Rect(0, 0, self.base_w, self.base_h // 3)
        self.head_rect = cocos.rect.Rect(0, 0, self.base_w, self.base_h * 2 // 3)

        self.sound = self.load_sound()

        self.schedule(self.update)

    def load_sound(self):
        return_dict = {}
        die_sound = pyglet.media.load('assets/sound/die.wav', streaming=False)
        return_dict["die"] = die_sound
        return return_dict


    def load_animation(self):
        dict_animation = {}
        #load jump
        jump = []
        for i in JUMP_ANIM:
            jump.append(pyglet.image.load(f'assets/sprite/{i}'))
        idle = []

        for i in IDLE_ANIM:
            idle.append(pyglet.image.load(f'assets/sprite/{i}'))
        walk = []

        for i in WALK_ANIM:
            walk.append(pyglet.image.load(f'assets/sprite/{i}'))

        die = [pyglet.image.load(f'assets/sprite/Blue2.png')]

        dict_animation["jump"] = pyglet.image.Animation.from_image_sequence(jump, 0.1, loop=False)
        dict_animation["walk"] = pyglet.image.Animation.from_image_sequence(walk, 0.1, loop=True)
        dict_animation["idle"] = pyglet.image.Animation.from_image_sequence(idle, 0.8, loop=True)
        dict_animation["die"] = pyglet.image.Animation.from_image_sequence(die, 1, loop=False)
        return dict_animation

    def update(self, dt):
        # While piloting a Ship, physics and animation are handled by the Ship
        if self.is_piloting:
            return

        self.velocity[1] += self.gravity * dt

        x, y = self.position
        new_x = x + self.velocity[0] * dt
        new_y = y + self.velocity[1] * dt

        # Hitbox dimensions scale with the character visual size.
        # We multiply base dims by self.scale so the hitbox grows/shrinks together with
        # the sprite while the base dims remain constant for stable ratio calculations.
        w = self.base_w * self.scale
        h = self.base_h * self.scale

        if self.collision_boxes and not self.is_die:

            leg_h = h * (1 - 64 / 96)  # lower half
            leg_w = w * 32 / 80
            
            head_h = h * (64 / 96)  # upper half

            # --- X-axis collision (full body width, full height) ---
            #self.rect_x = cocos.rect.Rect(new_x - w / 2, y, w, h)
            # for solid in self.collision_boxes:
            #     if self.rect_x.intersects(solid):
            #         if self.velocity[0] > 0:
            #             new_x = solid.x - w/2
            #             self.rect_x.x = new_x - w/2
            #         elif self.velocity[0] < 0:
            #             new_x = solid.x + solid.width + w/2
            #             self.rect_x.x = new_x - w/2

            # --- Y-axis: Leg box (lower portion) — floor detection ---
            self.leg_rect = cocos.rect.Rect(new_x - leg_w / 2, new_y, leg_w, leg_h)
            self.is_on_ground = False
            for solid in self.collision_boxes:
                if self.leg_rect.intersects(solid):
                    # Tính penetration depth theo từng trục
                    leg_top = new_y + leg_h
                    leg_bottom = new_y
                    solid_top = solid.y + solid.height
                    solid_bottom = solid.y

                    overlap_y = min(leg_top, solid_top) - max(leg_bottom, solid_bottom)

                    leg_left = new_x - leg_w / 2
                    leg_right = new_x + leg_w / 2
                    overlap_x = min(leg_right, solid.x + solid.width) - max(leg_left, solid.x)

                    if overlap_y <= overlap_x:
                        # Va chạm dọc (mặt trên) → snap floor
                        if self.velocity[1] <= 0:
                            new_y = solid_top
                            self.velocity[1] = 0
                            self.is_on_ground = True
                            self.leg_rect.y = new_y
                    else:
                        # Va chạm ngang → block X
                        if self.velocity[0] > 0:
                            new_x = solid.x - leg_w / 2
                        elif self.velocity[0] < 0:
                            new_x = solid.x + solid.width + leg_w / 2
                        self.velocity[0] = 0
                        self.leg_rect.x = new_x - leg_w / 2

            # --- Y-axis: Head box (upper portion) — ceiling detection ---
            self.head_rect = cocos.rect.Rect(new_x - w / 2, new_y + leg_h, w, head_h)
            for solid in self.collision_boxes:
                if self.head_rect.intersects(solid):
                    head_top = new_y + h
                    head_bottom = new_y + leg_h
                    solid_top = solid.y + solid.height
                    solid_bottom = solid.y

                    # Tính penetration depth theo từng trục
                    overlap_y = min(head_top, solid_top) - max(head_bottom, solid_bottom)

                    head_left = new_x - w / 2
                    head_right = new_x + w / 2
                    overlap_x = min(head_right, solid.x + solid.width) - max(head_left, solid.x)

                    if overlap_y < overlap_x:
                        # Va chạm dọc (penetration Y nhỏ hơn → mặt trên/dưới)
                        if self.velocity[1] > 0:  # Cộc đầu
                            new_y = solid_bottom - h
                            self.velocity[1] = 0
                        elif self.velocity[1] < 0:  # Chạm sàn bằng head_rect
                            new_y = solid_top - leg_h
                            self.velocity[1] = 0
                            self.is_on_ground = True
                    else:
                        # Va chạm ngang (penetration X nhỏ hơn → mặt bên)
                        if self.velocity[0] > 0:
                            new_x = solid.x - w / 2
                        elif self.velocity[0] < 0:
                            new_x = solid.x + solid.width + w / 2
                        self.velocity[0] = 0

                    self.head_rect.x = new_x - w / 2
                    self.head_rect.y = new_y + leg_h

        self.position = (new_x, new_y)

        # Smoothly lerp scale toward target each frame
        self.update_scale()
        self.update_animation()
        if self.has_gun:
            self.shoot_timer -= dt
            # Cập nhật vị trí súng theo hướng nhân vật
            if self.gun_sprite:
                # Chia cho scale_x để compensate flip của parent
                offset_x = 20  # scale_x âm → tự đổi dấu
                self.gun_sprite.position = (offset_x, 30)
                # Child đã bị flip theo parent, không cần flip thêm

    def update_animation(self):
        if self.is_die:
            return
        if not self.is_on_ground:
            new_state = "jump"
        elif self.velocity[0] != 0:
            new_state = "walk"
        else:
            new_state = "idle"

        if self.state != new_state:
            self.state = new_state
            self.image = self.animation[self.state]

    def update_scale(self):
        """Smoothly lerp self.scale toward self.target_scale each frame."""
        diff = self.target_scale - self.scale
        if abs(diff) <= self.scale_speed:
            self.scale = self.target_scale  # snap when close enough
        elif diff > 0:
            self.scale += self.scale_speed
        else:
            self.scale -= self.scale_speed
        
        if self.scale < self.minimum_scale:
            self.scale = self.minimum_scale
        elif self.scale > self.maximum_scale:
            self.scale = self.maximum_scale

    def apply_button_effect(self, button: Button):
        button_type = button.type
        if button_type == TypeButton.ActivateObj:
            pass
        elif button_type == TypeButton.StretchVertical:
            pass
        elif button_type == TypeButton.StretchHorizontal:
            pass
        elif button_type == TypeButton.Prohibited:  
            self.die()
        elif button_type == TypeButton.IncreaseSize:
            self.target_scale += 0.005   # set target, not scale directly
        elif button_type == TypeButton.DecreaseSize:
            self.target_scale -= 0.005
        elif button_type == TypeButton.Neutral:
            self.target_scale = 1.0      # snap back to normal over time
            


    def handle_key_press(self, k, modifiers):
        if self.is_die:
            return
        if k == key.A:
            self.velocity[0] = -self.speed
            self.scale_x = -abs(self.scale_x)
        elif k == key.D:
            self.velocity[0] = self.speed
            self.scale_x = abs(self.scale_x)
        elif k == key.SPACE:
            if self.is_on_ground:
                self.velocity[1] = self.jump_speed
                self.is_on_ground = False


    def handle_key_release(self, k, modifiers):
        if self.is_die:
            return
        if k in (key.A, key.D):
            self.velocity[0] = 0

    def get_leg_collision_rect(self):
        return self.leg_rect
    
    def get_head_collision_rect(self):
        return self.head_rect
    
    def get_full_collision_rect(self):
        return self.rect_x

    def die(self):
        if self.is_die:
            return
        self.is_die = True
        self.state = "die"
        self.image = self.animation[self.state]
        self.sound["die"].play()
        
        # Stop horizontal movement, jump up and fall through floor
        self.velocity[0] = 0
        self.velocity[1] = 400
        
        # Schedule respawn after 1.5 seconds
        pyglet.clock.schedule_once(self.respawn, 2)

    def respawn(self, dt=0):
        self.is_die = False
        self.velocity = [0, 0]
        if hasattr(self, 'checkpoint'):
            self.position = self.checkpoint
        self.state = "idle"
        self.scale = self.target_scale = 1
        self.update_animation()
        self.update_collision_box()

    def update_collision_box(self):
        w = self.base_w * self.scale
        h = self.base_h * self.scale

        leg_h = h * (1 - 64 / 96)
        leg_w = w * 32 / 80
        head_h = h * (64 / 96)

        new_x, new_y = self.position

        self.leg_rect = cocos.rect.Rect(new_x - leg_w / 2, new_y, leg_w, leg_h)
        self.head_rect = cocos.rect.Rect(new_x - w / 2, new_y + leg_h, w, head_h)
        self.rect_x = cocos.rect.Rect(new_x - w / 2, new_y, w, h)

    def check_stomp(self, mobs):
        if self.is_die:
            return

        px, py = self.position
        for mob in mobs[:]:
            if getattr(mob, 'is_die', False):
                continue

            mx, my = mob.position
            mw = mob.base_w * mob.scale
            mh = mob.base_h * mob.scale

            # Construct mob hitbox (centered at X, growing upwards from Y)
            mob_rect = cocos.rect.Rect(mx - mw / 2, my, mw, mh)

            # Check if player intersects with mob
            if self.leg_rect.intersects(mob_rect) or self.head_rect.intersects(mob_rect):
                player_bottom = py
                mob_top = my + mh
                
                # Check if it is a stomp: falling down and hitting the top section of the mob
                is_stomp = self.velocity[1] < 0 and player_bottom >= mob_top - min(30, mh * 0.4)

                if is_stomp:
                    mob.die()
                    self.velocity[1] = 300  # Bounce up after stomp
                else:
                    self.die()  # Player dies otherwise
                    return

    def pick_up_gun(self, gun):
        if self.has_gun:
            return
        self.has_gun = True
        # Không add vào self, GameScene sẽ add vào layer
        self.gun_sprite = cocos.sprite.Sprite("assets/interactions/Gun.png")
        self.gun_sprite.image_anchor_x = self.gun_sprite.width // 2
        self.gun_sprite.image_anchor_y = self.gun_sprite.height // 2
        self.gun_sprite.scale = 0.8

    def shoot(self):
        if not self.has_gun or self.is_die:
            return None
        direction = 1 if self.scale_x > 0 else -1
        from .Bullet import Bullet
        px, py = self.position
        offset_x = 20 if self.scale_x > 0 else -20
        bullet_pos = (px + offset_x, py + 30)
        bullet = Bullet(bullet_pos, direction)
        return bullet

    def get_hitbox(self):
        w = self.base_w * self.scale
        h = self.base_h * self.scale
        x, y = self.position
        return cocos.rect.Rect(x - w / 2, y, w, h)