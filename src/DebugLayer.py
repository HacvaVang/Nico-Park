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

        # ── 2. Player boxes — use same scaled dims as Character.update() ─────
        player = self.game_layer.player
        s  = player.scale
        w  = player.base_w * s
        h  = player.base_h * s
        leg_h  = h * (1 - 64 / 96)
        leg_w  = w * (1 - 32 / 80)
        head_h = h * (64 / 96)
        px, py = player.position   # py = bottom of sprite (bottom-anchor)

        # Full body / wall rect
        _rect(px - w/2, py, w, h, COL_PLAYER)

        # Leg rect (floor detection \u2014 narrow + short)
        _rect(px - leg_w/2, py, leg_w, leg_h, COL_LEG)

        # Head rect (ceiling detection \u2014 full width, upper portion)
        _rect(px - w/2, py + leg_h, w, head_h, COL_HEAD)

        # ── 3. Buttons ───────────────────────────────────────────────────────
        for btn in self.game_layer.buttons:
            bw, bh = btn.width, btn.height
            bx, by = btn.position
            _rect(bx - bw/2, by - bh/2, bw, bh, COL_BUTTON)

        # ── 4. Obstacles ─────────────────────────────────────────────────────
        for obs in self.game_layer.obstacles:
            r = obs.get_hitbox()
            _rect(r.x, r.y, r.width, r.height, COL_OBSTACLE)

        glLineWidth(1.0)
        glDisable(GL_BLEND)
