from ursina import *
from games.minecraft.player import MinecraftPlayer
from games.minecraft.world import World
from games.minecraft.enemies import EnemySystem
from games.minecraft.ui import UI
from games.minecraft.save_system import SaveSystem
from games.minecraft.assets import Assets
from games.minecraft.items import ItemSystem
from games.minecraft.fluids import FluidSystem

'''
games/minecraft/
│
├── minecraft_game.py          # main controller (ONLY orchestrates)
├── player.py                  # FirstPersonController wrapper
├── world.py                   # blocks, placement, terrain
├── enemies.py                 # zombies/skeletons logic
├── items.py                   # power cube, pickups
├── fluids.py                 # lava/water systems
├── ui.py                     # health bar, text, HUD
├── save_system.py            # JSON save/load
├── assets.py                 # central asset loader (sounds/models)
│
└── assets/
    ├── Zombie.obj
    ├── Skeleton.obj
    ├── Atlas.png
    ├── Zombie_Atlas.png
    ├── sounds/
    └── textures/
'''

class MinecraftGame:
    '''
    MinecraftGame is a snadbox world where everything is mad up of blocks and with silly enemies for some fun.
    '''

    def __init__(self):

        self.entities = []
        self.systems = []

        # ------state------
        self.state = {
            "boxes": [],
            "enemies": [],
            "block_types": [
                {'name': 'Stone', 'texture': 'white_cube', 'color': color.gray},
                {'name': 'Bricks', 'texture': 'brick', 'color': color.brown},
                {'name': 'Red Block', 'texture': 'white_cube', 'color': color.red},
                {'name': 'Blue Block', 'texture': 'white_cube', 'color': color.azure},
                {'name': 'Orange Block', 'texture': 'white_cube', 'color': color.orange},
                {'name': 'Coal', 'texture': 'white_cube', 'color': color.black},
                {'name': 'Water', 'texture': 'white_cube', 'color': color.rgba(0,120,255,120)},
                {'name': 'Lava','texture': 'white_cube','color': color.rgba(255,120,0,180)},
            ],
            "current_block_index": 0,
            "game_over": False,
            "game_started": False,
            "player_health": 100,
            "max_health": 100,
            "lava_cooldown": 0,
            "power_cube": None,
            "instructions_open": True
                        }

        # ---- PLAYER ----
        self.player = MinecraftPlayer(self)

        # ---- WORLD ----
        self.world = World(self)

        # ---- ENEMIES ----
        self.enemies = EnemySystem(self)

        # ---- UI ----
        self.ui = UI(self)

        # ---- SAVE ----
        self.save = SaveSystem(self)
        # ---- ASSETS ----
        self.assets = Assets()
        # ---- ITEMS ----
        self.items = ItemSystem(self)
        # ---- FLUIDS ----
        self.fluids = FluidSystem(self)

        self.systems = [
            self.player,
            self.world,
            self.enemies,
            self.ui,
            self.save,
            self.assets,
            self.items,
            self.fluids
        ]
        
    def reset_player(self):
            self.player.player.position = (0, 5, 0)
            self.state["player_health"] = 100
            
    def update(self):

        self.ui.update()

        if self.state["instructions_open"]:
            return

        for s in self.systems:
            if hasattr(s, "update"):
                s.update()        
        if self.player.player.y < -20:
            self.reset_player()

    def input(self, key):

        self.ui.input(key)

        if self.state["instructions_open"]:
            return

        self.player.input(key)
        self.world.input(key)
        self.enemies.input(key)

        for s in self.systems:
            if hasattr(s, "input"):
                s.input(key)

    def destroy(self):

        # destroy systems
        for s in self.systems:
            if hasattr(s, "destroy"):
                s.destroy()

        # destroy all blocks
        for block in self.state["boxes"][:]:
            destroy(block)

        self.state["boxes"].clear()

        # destroy enemies
        for enemy in self.state["enemies"][:]:

            # enemy object or entity safety
            if hasattr(enemy, "entity"):
                destroy(enemy.entity)
            else:
                destroy(enemy)

        self.state["enemies"].clear()

        self.systems.clear()
        self.entities.clear()

        # reset camera
        camera.parent = scene
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.orthographic = False
