from ursina import *
from games.minecraft.items import ItemSystem


class World:

    def __init__(self, game):
        self.game = game
        self.state = game.state
        self.items = ItemSystem(game)
        self.pending_positions = set()

        self.build_ground()

    def is_valid(self, e):
        return (
            e is not None
            and hasattr(e, "enabled")
            and e.enabled
            and hasattr(e, "position")
        )

    def clean_boxes(self):
        self.state["boxes"] = [
            b for b in self.state["boxes"]
            if self.is_valid(b)
        ]

    def build_ground(self):
        self.state.setdefault("boxes", [])

        for x in range(30):
            for z in range(30):
                b = Button(
                    model='cube',
                    texture='grass.png',
                    color=color.white,
                    position=(x, 0, z),
                    collider='box',
                    parent=scene
                )
                self.state["boxes"].append(b)

        self.items.spawn_power_cube()

    def input(self, key):

        self.clean_boxes()

        state = self.state
        player = self.game.player.player

        if not player:
            return

        # BLOCK SWITCH
        if key == 'scroll up':
            state["current_block_index"] = (state["current_block_index"] + 1) % len(state["block_types"])

        if key == 'scroll down':
            state["current_block_index"] = (state["current_block_index"] - 1) % len(state["block_types"])

        current_block = state["block_types"][state["current_block_index"]]

        # ================= PLACE BLOCK =================
        if key == 'left mouse down':

            for b in state["boxes"][:]:

                if not self.is_valid(b):
                    continue

                if b.hovered:

                    pos = b.position + mouse.normal

                    if pos in self.pending_positions:
                        return

                    if any(self.is_valid(x) and x.position == pos for x in state["boxes"]):
                        return

                    self.pending_positions.add(pos)
                    invoke(self.pending_positions.discard, pos, delay=0.1)

                    if current_block["name"] == "Water":
                        self.game.fluids.spawn_water(pos)
                        return

                    if current_block["name"] == "Lava":
                        self.game.fluids.spawn_lava(pos)
                        return

                    new_block = Button(
                        model='cube',
                        texture=current_block["texture"],
                        color=current_block["color"],
                        position=pos,
                        collider='box',
                        parent=scene
                    )

                    state["boxes"].append(new_block)
                    return

        # ================= BREAK BLOCK =================
        if key == 'right mouse down':

            for b in state["boxes"][:]:

                if not self.is_valid(b):
                    continue

                if b.hovered and getattr(b, "enabled", False) and b.y != 0:

                    # SAFE FLUID GROUP REMOVE
                    if hasattr(b, "group") and b.group:

                        group_copy = b.group[:]

                        for fb in group_copy:
                            if fb in state["boxes"]:
                                state["boxes"].remove(fb)
                            if fb:
                                destroy(fb)

                        b.group.clear()
                        return

                    if b in state["boxes"]:
                        state["boxes"].remove(b)

                    destroy(b)
                    return