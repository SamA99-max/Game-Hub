from ursina import *


# ================= FLUID MANAGER =================

class FluidSystem:

    def __init__(self, game):
        self.game = game
        self.state = game.state

    def spawn_water(self, pos):
        block_type = next(b for b in self.state["block_types"] if b["name"] == "Water")
        WaterBlock(self.game, pos, block_type)

    def spawn_lava(self, pos):
        block_type = next(b for b in self.state["block_types"] if b["name"] == "Lava")
        LavaBlock(self.game, pos, block_type)

    def update(self):

        player = self.game.player.player
        if not player:
            return

        self.state["lava_cooldown"] -= time.dt

        player_pos = Vec3(
            round(player.x),
            round(player.y),
            round(player.z)
        )

        # CLEAN INVALID / DESTROYED BLOCKS
        self.state["boxes"] = [
            b for b in self.state["boxes"]
            if b and hasattr(b, "enabled") and b.enabled
        ]

        for block in self.state["boxes"]:

            if getattr(block, "fluid_name", None) != "Lava":
                continue

            if block.position == player_pos:

                if self.state["lava_cooldown"] <= 0:
                    self.state["player_health"] -= 5
                    self.state["lava_cooldown"] = 1
                break


# ================= BASE FLUID =================

class BaseFluid(Button):

    def __init__(self, game, pos, block_type, spread_limit=3, group=None):

        # SAFE DEFAULTS (prevents KeyError crashes)
        texture = block_type.get("texture", "white_cube")
        col = block_type.get("color", color.white)
        name = block_type.get("name", "Fluid")
        self.alive = True

        super().__init__(
            model='cube',
            texture=texture,
            color=col,
            position=pos,
            collider='box',
            parent=scene
        )

        self.game = game
        self.state = game.state

        self.block_type = block_type
        self.fluid_name = name

        self.spread_limit = spread_limit
        self.alive = True

        self.group = group if group else []
        self.group.append(self)

        self.state["boxes"].append(self)

        if self.spread_limit > 0:
            invoke(self.safe_spread, delay=0.25)

    def safe_spread(self):
        if not self.alive or not self.enabled:
            return

        invoke(self.spread, delay=0)

    def spread(self):
        if not self.alive:
            return
        if not self.enabled:
            return


        if self.spread_limit <= 0:
            return

        directions = [
            Vec3(0, -1, 0),
            Vec3(1, 0, 0),
            Vec3(-1, 0, 0),
            Vec3(0, 0, 1),
            Vec3(0, 0, -1)
        ]

        for d in directions:

            if not self or not self.enabled:
                return

            pos = getattr(self, "position", None)
            if pos is None:
                return

            new_pos = pos + d

            occupied = any(
                b and hasattr(b, "position") and b.position == new_pos
                for b in self.state["boxes"]
            )

            if occupied:
                continue

            self.create_child(new_pos, self.spread_limit - 1)

    def create_child(self, pos, limit):
        pass

    def destroy(self):
        self.alive = False
        self.enabled = False

        if self in self.state["boxes"]:
            self.state["boxes"].remove(self)

        self.group.clear()

        super().destroy()


# ================= WATER =================

class WaterBlock(BaseFluid):

    def create_child(self, pos, limit):
        WaterBlock(
            self.game,
            pos,
            next(b for b in self.state["block_types"] if b["name"] == "Water"),
            limit,
            self.group
        )


# ================= LAVA =================

class LavaBlock(BaseFluid):

    def create_child(self, pos, limit):
        LavaBlock(
            self.game,
            pos,
            next(b for b in self.state["block_types"] if b["name"] == "Lava"),
            limit,
            self.group
        )