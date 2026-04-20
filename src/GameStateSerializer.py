# GameStateSerializer.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .GameScene import GameScene

_tick = 0

TELEPORT_THRESHOLD = 200
GHOST_LERP = 0.25
LOCAL_LERP = 0.12


def serialize_state(game: "GameScene", player_id_map: dict) -> dict:
    global _tick
    _tick += 1

    state = {
        "tick": _tick,
        "players": {},
        "mobs": [],
        "bosses": [],
        "keys": [],
        "bullets": [],
        "keys_collected": game.keys_collected,
        "door_opened": game.door_opened,
    }

    for char, pid in player_id_map.items():
        if char is None:
            continue
        # FIX scale sync: tách scale (size) và flip hướng (facing)
        # scale_x của cocos = scale * flip_direction
        # → facing = -1 nếu lật trái, 1 nếu phải
        raw_scale_x = char.scale_x
        facing = -1 if raw_scale_x < 0 else 1
        state["players"][str(pid)] = {
            "x": char.position[0],
            "y": char.position[1],
            "scale": char.scale,
            "facing": facing,
            # Thêm thuộc tính để đồng bộ animation (giả sử bạn có biến này trong Character)
            "anim_frame": getattr(char, 'current_frame', 0),
            "is_die": getattr(char, 'is_die', False),
        }

    for i, mob in enumerate(game.mobs):
        state["mobs"].append({
            "id": i,
            "x": mob.position[0], "y": mob.position[1],
            "scale_x": mob.scale_x,
            "is_die": mob.is_die,
        })

    for i, boss in enumerate(game.bosses):
        state["bosses"].append({
            "id": i,
            "x": boss.position[0], "y": boss.position[1],
            "health": boss.health, "max_health": boss.max_health,
            "is_die": boss.is_die, "activated": boss.activated,
        })

    for i, key_item in enumerate(game.keys):
        state["keys"].append({
            "id": i,
            "collected": getattr(key_item, 'collected', False),
        })

    for i, bullet in enumerate(game.bullets):
        state["bullets"].append({
            "id": i,
            "x": bullet.position[0], "y": bullet.position[1],
            "dead": getattr(bullet, 'dead', False),
        })

    return state


def apply_state_to_client(state: dict, game: "GameScene", local_player_id: int):
    # ── Players ──────────────────────────────────────────────────────
    for pid_str, pdata in state.get("players", {}).items():
        pid = int(pid_str)

        # Xử lý cho người chơi hiện tại (Local)
        if pid == local_player_id:
            # ... (Giữ nguyên logic di chuyển hiện tại của bạn)
            lx, ly = game.player.position
            sx, sy = pdata["x"], pdata["y"]
            dist = ((lx - sx) ** 2 + (ly - sy) ** 2) ** 0.5
            if dist > TELEPORT_THRESHOLD:
                game.player.position = (sx, sy)
            elif dist > 60:
                game.player.position = (lx + (sx - lx) * LOCAL_LERP, ly + (sy - ly) * LOCAL_LERP)

            # Cập nhật scale cho local player nếu cần
            game.player.scale = pdata.get("scale", 1.0)

        # Xử lý cho người chơi khác (Ghost / Player 2)
        else:
            ghost = game.ghost_players.get(pid)
            if not ghost: continue

            # 1. Cập nhật Vị trí
            tx, ty = pdata["x"], pdata["y"]
            ghost.position = (ghost.position[0] + (tx - ghost.position[0]) * GHOST_LERP, ty)

            # 2. Cập nhật Scale & Facing (Chuẩn hóa)
            s = pdata.get("scale", 1.0)
            f = pdata.get("facing", 1)
            ghost.scale = s

            # 3. Cập nhật Animation (Đây là phần giúp Player 2 hết đứng yên)
            # Giả sử trong lớp Character/GhostPlayer của bạn có phương thức này
            if hasattr(ghost, 'update_animation'):
                ghost.update_animation(pdata.get("anim_frame", 0))

    # ── Mobs ─────────────────────────────────────────────────────────
    for mdata in state.get("mobs", []):
        mid = mdata["id"]
        if mid < len(game.mobs):
            m = game.mobs[mid]
            m.position = (mdata["x"], mdata["y"])
            m.is_die = mdata["is_die"]
            # Nếu quái chết, ẩn đi hoặc xử lý logic tại đây
            if m.is_die:
                m.visible = False

    # ── Bosses ───────────────────────────────────────────────────────
    for bdata in state.get("bosses", []):
        bid = bdata["id"]
        if bid < len(game.bosses):
            b = game.bosses[bid]
            b.position = (bdata["x"], bdata["y"])
            b.health = bdata["health"]
            b.is_die = bdata["is_die"]
            b.activated = bdata["activated"]

    # ── Keys ─────────────────────────────────────────────────────────
    for kdata in state.get("keys", []):
        kid = kdata["id"]
        if kid < len(game.keys):
            key_item = game.keys[kid]
            if kdata["collected"] and not key_item.collected:
                key_item.collect()

    # ── Shared state / HUD ───────────────────────────────────────────
    game.keys_collected = state.get("keys_collected", 0)
    game.door_opened = state.get("door_opened", False)

    if game.hud_layer:
        bosses = state.get("bosses", [])
        if bosses and bosses[0]["activated"]:
            b = bosses[0]
            game.hud_layer.update_boss_hp(b["health"], b["max_health"])