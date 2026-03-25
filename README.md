# Nico Park Platform Game

A platform game framework built with Cocos2d-x using Python and tile maps.

## Setup

1. Download and install Cocos2d-x from https://www.cocos.com/en/cocos2d-x
2. Ensure Python is installed and cocos2d Python bindings are available.
3. Set up the cocos command line tool.

## Building

Use the cocos command to compile:

```
cocos compile -p win32 -l python -m release
```

## Running

Run the compiled executable or use:

```
python Classes/main.py
```

(Assuming cocos2d is in path)

## Assets

Place your TML tile map file as `Resources/map.tmx` (assuming TML is TMX format).
Place player sprite as `Resources/player.png`.

## Framework Components

- AppDelegate: Application entry point
- GameScene: Main game scene with physics and tile map
- Player: Controllable character with physics body
- Tile Map: Loaded from TML/TMX file with collision detection

## Controls

- Left/Right Arrow: Move
- Space: Jump

## Notes

If TML is a custom format, modify the TMXTiledMap loading to parse TML accordingly.