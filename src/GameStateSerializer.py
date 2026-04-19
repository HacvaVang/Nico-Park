# GameStateSerializer.py
"""
Chuyển đổi GameScene state thành dict có thể JSON-serialize,
và áp dụng state nhận được lên client's GameScene.

State format:
{
  "tick": int,
  "players": {
    "1": {"x": float, "y": float, "vx": float, "vy": float,
          "scale_x": float, "health": int, "has_gun": bool, "is_die": bool},
    "2": {...}
  },
  "mobs": [{"id": int, "x": float, "y": float, "scale_x": float,
             "health": int, "is_die": bool}, ...],
  "bosses": [{"id": int, "x": float, "y": float, "health": int,
              "max_health": int, "is_die": bool, "activated": bool}, ...],
  "coins": [{"id": int, "x": float, "y": float, "collected": bool}, ...],
  "bullets": [{"id": int, "x": float, "y": float, "vx": float, "vy": float,
                "dead": bool}, ...],
  "coins_collected": int,
  "door_opened": bool,
}
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .GameScene import GameScene


_tick = 0


def serialize_state(game: "GameScene", player_id_map: dict) -> dict:
    """
    Tạo snapshot state từ GameScene của host.
    player_id_map: {character_obj: player_id}  e.g. {game.player: 1, p2_char: 2}
    """
    global _tick
    _tick += 1

    state = {
        "tick": _tick,
        "players": {},
        "mobs": [],
        "bosses": [],
        "coins": [],
        "bullets": [],
        "coins_collected": game.coins_collected,
        "door_opened": game.door_opened,
    }

    # Players
    for char, pid in player_id_map.items():
        if char is None:
            continue
        state["players"][str(pid)] = {
            "x": char.position[0],
            "y": char.position[1],
            "vx": getattr(char, 'velocity', [0, 0])[0],
            "vy": getattr(char, 'velocity', [0, 0])[1],
            "scale_x": char.scale_x,
            "health": getattr(char, 'health', 3),
            "has_gun": getattr(char, 'has_gun', False),
            "is_die": getattr(char, 'is_die', False),
        }

    # Mobs
    for i, mob in enumerate(game.mobs):
        state["mobs"].append({
            "id": i,
            "x": mob.position[0],
            "y": mob.position[1],
            "scale_x": mob.scale_x,
            "health": getattr(mob, 'health', 1),
            "is_die": mob.is_die,
        })

    # Bosses
    for i, boss in enumerate(game.bosses):
        state["bosses"].append({
            "id": i,
            "x": boss.position[0],
            "y": boss.position[1],
            "health": boss.health,
            "max_health": boss.max_health,
            "is_die": boss.is_die,
            "activated": boss.activated,
        })

    # Coins
    for i, coin in enumerate(game.coins):
        state["coins"].append({
            "id": i,
            "x": coin.position[0],
            "y": coin.position[1],
            "collected": getattr(coin, 'collected', False),
        })

    # Bullets
    for i, bullet in enumerate(game.bullets):
        state["bullets"].append({
            "id": i,
            "x": bullet.position[0],
            "y": bullet.position[1],
            "vx": getattr(bullet, 'velocity', [0, 0])[0] if hasattr(bullet, 'velocity') else 0,
            "vy": getattr(bullet, 'velocity', [0, 0])[1] if hasattr(bullet, 'velocity') else 0,
            "dead": getattr(bullet, 'dead', False),
        })

    return state


def apply_state_to_client(state: dict, game: "GameScene", local_player_id: int):
    """
    Áp dụng state từ server lên ClientGameScene.
    local_player_id: player_id của người chơi trên máy này (thường là 2).
    """
    # Players
    for pid_str, pdata in state.get("players", {}).items():
        pid = int(pid_str)
        if pid == local_player_id:
            # Player cục bộ: chỉ sync visual, không override vị trí
            # (để tránh teleport do network lag - dùng reconciliation sau)
            pass
        else:
            # Ghost player (player kia)
            ghost = game.ghost_players.get(pid)
            if ghost:
                ghost.position = (pdata["x"], pdata["y"])
                ghost.scale_x = pdata["scale_x"]

    # Mobs
    for mdata in state.get("mobs", []):
        mid = mdata["id"]
        if mid < len(game.mobs):
            mob = game.mobs[mid]
            mob.position = (mdata["x"], mdata["y"])
            mob.scale_x = mdata["scale_x"]
            mob.is_die = mdata["is_die"]

    # Bosses
    for bdata in state.get("bosses", []):
        bid = bdata["id"]
        if bid < len(game.bosses):
            boss = game.bosses[bid]
            boss.position = (bdata["x"], bdata["y"])
            boss.health = bdata["health"]
            boss.is_die = bdata["is_die"]
            boss.activated = bdata["activated"]

    # Coins
    for cdata in state.get("coins", []):
        cid = cdata["id"]
        if cid < len(game.coins):
            coin = game.coins[cid]
            if cdata["collected"] and not coin.collected:
                coin.collect()

    # HUD
    game.coins_collected = state.get("coins_collected", 0)
    game.door_opened = state.get("door_opened", False)

    # Boss HUD
    if game.hud_layer:
        bosses = state.get("bosses", [])
        if bosses:
            b = bosses[0]
            if b["activated"]:
                game.hud_layer.update_boss_hp(b["health"], b["max_health"])
