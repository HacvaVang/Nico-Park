import cocos
from cocos.tiles import load, TmxObjectLayer

class MapManager:
    """Manages map data including collision boxes and spawn points."""
    
    def __init__(self, map_path="assets/map.tmx"):
        self.map_path = map_path
        self.land_collisions = []
        self.object_spawn_position : dict[str, list[tuple[float, float]]] = dict()
        self._load_data()

    def _load_data(self):
        tile_map = load(self.map_path)
        for _, obj_layer in tile_map.find(TmxObjectLayer):
            layer_name = (getattr(obj_layer, "name", "") or "").lower()
            
            if layer_name == "land collision":
                for obj in getattr(obj_layer, "objects", []):
                    x = getattr(obj, "x", 0)
                    y = getattr(obj, "y", 0)
                    w = getattr(obj, "width", 0)
                    h = getattr(obj, "height", 0)
                    self.land_collisions.append(cocos.rect.Rect(x, y, w, h))
                    
            elif layer_name in ("spawn position", "starting position"):
                for obj in getattr(obj_layer, "objects", []):
                    name = getattr(obj, "name", "") or "Character"
                    existing = self.object_spawn_position.get(name, [])
                    self.object_spawn_position[name] = existing + [(obj.x, obj.y)]

    def get_land_collisions(self):
        return self.land_collisions

    def get_starting_position(self):
        positions = self.object_spawn_position.get("Character", [])
        return positions[0] if positions else (96, 480)  # fallback to (0,0) if not found

    def get_object_position_list(self, name: str):
        return self.object_spawn_position.get(name, [])
