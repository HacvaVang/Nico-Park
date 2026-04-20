import json
import os
from dataclasses import dataclass


@dataclass
class GameRules:
    # Core progression
    keys_required: int = 1
    # Co-op clear condition
    require_all_players_at_exit: bool = True
    # Team wipe condition
    fail_if_any_player_dead: bool = False


def load_rules(config_path: str = "assets/rules.json") -> GameRules:
    """Load optional rules JSON; fallback to sane defaults when missing/invalid."""
    rules = GameRules()

    if not os.path.exists(config_path):
        return rules

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "keys_required" in data:
            rules.keys_required = max(1, int(data["keys_required"]))
        elif "coins_required" in data:
            # Backward-compatible with old config name.
            rules.keys_required = max(1, int(data["coins_required"]))
        if "require_all_players_at_exit" in data:
            rules.require_all_players_at_exit = bool(data["require_all_players_at_exit"])
        if "fail_if_any_player_dead" in data:
            rules.fail_if_any_player_dead = bool(data["fail_if_any_player_dead"])
    except Exception as e:
        print(f"[Rules] Không đọc được {config_path}: {e}. Dùng default rules.")

    return rules
