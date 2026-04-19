"""DebugLayer — draws collision boxes, character hitboxes and button/obstacle rects as coloured outlines.

Best used as a CHILD of GameScene (not the scroller), so it shares the same
local coordinate space as all sprites — guaranteeing pixel-perfect alignment.

Usage (in GameScene.__init__):
    self.debug = DebugLayer(map_manager, self)
    self.add(self.debug, z=100)
"""

import cocos
from cocos.layer import Layer
from pyglet.gl import (
    glBegin, glEnd, glColor4f, glVertex2f,
    GL_LINE_LOOP,
    glLineWidth, glEnable, glDisable, GL_BLEND,
    GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, glBlendFunc,
)


# ─── colour palette (r, g, b, a)  all 0‑1 ────────────────────────────────────
COL_LAND      = (0.2, 1.0, 0.2, 0.9)   # green  – land collision tiles
COL_PLAYER    = (0.2, 0.6, 1.0, 1.0)   # blue   – full player box
COL_LEG       = (1.0, 1.0, 0.0, 1.0)   # yellow – leg rect
COL_HEAD      = (1.0, 0.4, 0.0, 1.0)   # orange – head rect
COL_BUTTON    = (1.0, 0.2, 1.0, 0.9)   # purple – button hitbox
COL_OBSTACLE  = (1.0, 0.2, 0.2, 0.9)   # red    – obstacle hitbox
COL_SHIP      = (0.0, 1.0, 1.0, 0.9)   # cyan   – ship hitbox



def _rect(x, y, w, h, color):
    """Draw a hollow rectangle outline."""
    r, g, b, a = color
    glColor4f(r, g, b, a)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()


class DebugLayer(Layer):
    """Child-of-GameScene overlay: draws all hitboxes in the same coordinate space as sprites."""

    is_event_handler = False

    def __init__(self, map_manager, game_layer):
        super(DebugLayer, self).__init__()
        self.map_manager = map_manager
        self.game_layer  = game_layer   # GameScene reference for buttons / obstacles / player

    def draw(self):
        super(DebugLayer, self).draw()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(2.0)

        # ── 1. Land collision boxes ──────────────────────────────────────────
        for rect in self.map_manager.get_land_collisions():
            _rect(rect.x, rect.y, rect.width, rect.height, COL_LAND)

        # ── 2. Player boxes \u2014 use the actual collision rects from Character ──
        player = self.game_layer.player

        # Full body / wall rect
        r_full = player.get_full_collision_rect()
        _rect(r_full.x, r_full.y, r_full.width, r_full.height, COL_PLAYER)

        # Leg rect (floor detection)
        r_leg = player.get_leg_collision_rect()
        _rect(r_leg.x, r_leg.y, r_leg.width, r_leg.height, COL_LEG)

        # Head rect (ceiling detection)
        r_head = player.get_head_collision_rect()
        _rect(r_head.x, r_head.y, r_head.width, r_head.height, COL_HEAD)

        # Head rect (ceiling detection)
        r_leg_boss = self.game_layer.bosses[0].get_leg_collision_rect() if self.game_layer.bosses else None
        if r_leg_boss:
            _rect(r_leg_boss.x, r_leg_boss.y, r_leg_boss.width, r_leg_boss.height, COL_HEAD)
        # Head rect (ceiling detection)
        r_head_boss = self.game_layer.bosses[0].get_head_collision_rect() if self.game_layer.bosses else None
        if r_head_boss:
            _rect(r_head_boss.x, r_head_boss.y, r_head_boss.width, r_head_boss.height, COL_HEAD)

        # ── 3. Buttons ───────────────────────────────────────────────────────
        for btn in self.game_layer.buttons:
            bw, bh = btn.width, btn.height
            bx, by = btn.position
            _rect(bx - bw/2, by - bh/2, bw, bh, COL_BUTTON)

        # ── 4. Obstacles ─────────────────────────────────────────────────────
        for obs in self.game_layer.obstacles:
            r = obs.get_hitbox()
            _rect(r.x, r.y, r.width, r.height, COL_OBSTACLE)
        for mob in getattr(self.game_layer, 'mobs', []):
            r = mob.get_hitbox()
            _rect(r.x, r.y, r.width, r.height, COL_OBSTACLE)
        collectibles = getattr(self.game_layer, 'keys', None)
        if collectibles is None:
            collectibles = getattr(self.game_layer, 'coins', [])
        for item in collectibles:
            r = item.get_hitbox()
            _rect(r.x, r.y, r.width, r.height, COL_OBSTACLE)
        for gun in getattr(self.game_layer, 'guns', []):
            r = gun.get_hitbox()
            _rect(r.x, r.y, r.width, r.height, COL_OBSTACLE)



        # ── 5. Ships ─────────────────────────────────────────────────────────
        for ship in getattr(self.game_layer, 'ships', []):
            if ship.visible:
                r = ship.get_hitbox()
                _rect(r.x, r.y, r.width, r.height, COL_SHIP)


        glLineWidth(1.0)
        glDisable(GL_BLEND)
