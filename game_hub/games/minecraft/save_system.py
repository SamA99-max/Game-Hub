import json
import os
from ursina import *


class SaveSystem:

    def __init__(self, game):

        self.game = game
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.state = game.state
        self.path = os.path.join(self.BASE_DIR, "save_for_game_engine_minecraft.json")

    def input(self, key):

        if key == 'p':
            self.save()

        if key == 'l':
            self.load()

    def save(self):

        state = self.state

        data = {
            "player_pos": list(self.game.player.player.position),
            "player_health": state["player_health"],
            "block_types": [
                {
                    "name": b["name"],
                    "texture": b["texture"],
                    "color": [
                        b["color"].r if hasattr(b["color"], "r") else 1,
                        b["color"].g if hasattr(b["color"], "g") else 1,
                        b["color"].b if hasattr(b["color"], "b") else 1,
                        b["color"].a if hasattr(b["color"], "a") else 1,
                    ]
                }
                for b in state["block_types"]
            ],
            "blocks": []
        }

        for b in state["boxes"]:
            if hasattr(b, "name") and b.name == "cyan_marker":
                continue

            data["blocks"].append({
                "pos": [b.x, b.y, b.z],
                "color": [b.color.r, b.color.g, b.color.b, b.color.a],
                "texture": str(getattr(b, "texture", "white_cube")),
                "name": getattr(b, "name", "")
            })

        with open(self.path, "w") as f:
            json.dump(data, f)

        print("Saved world!")

    def load(self):

        if not os.path.exists(self.path):
            print("No save file found")
            return

        state = self.state

        # clear world
        for b in state["boxes"]:
            destroy(b)
        state["boxes"].clear()

        with open(self.path, "r") as f:
            data = json.load(f)

        # restore player
        self.game.player.player.position = Vec3(*data["player_pos"])

        state["player_health"] = data.get("player_health", 100)

        # restore blocks
        for b in data["blocks"]:

            pos = Vec3(*b["pos"])

            new_block = Button(
                model='cube',
                texture=b["texture"],
                color=color.rgba(*b["color"]),
                position=pos,
                parent=scene,
                collider='box'
            )

            if b["name"]:
                new_block.name = b["name"]

            state["boxes"].append(new_block)

        print("Loaded world!")