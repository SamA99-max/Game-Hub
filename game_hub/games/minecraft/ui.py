from ursina import *


class UI:

    def __init__(self, game):

        self.game = game

        # ---------------- HEALTH BAR ----------------

        self.health_bar = Entity(
            model='quad',
            color=color.lime,
            scale=(0.5, 0.05),
            parent=camera.ui,
            position=(-0.7, 0.45)
        )

        # ---------------- CURRENT BLOCK TEXT ----------------

        self.block_text = Text(
            text='',
            position=(-0.85, 0.38),
            scale=1.5,
            parent=camera.ui
        )

        # ---------------- DAMAGE SCREEN FLASH ----------------

        self.hitscreen = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 1),
            color=color.rgba(255, 0, 0, 0.5),
            enabled=False
        )

        self.last_hp = self.game.state["player_health"]

        # ---------------- INSTRUCTION SCREEN ----------------

        self.instruction_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 1),
            color=color.rgba(0, 0, 0, 220),
            enabled=True
        )

        self.instructions = Text(
            parent=camera.ui,
            text=
"""
MINECRAFT

W A S D  - Move
SPACE    - Jump
R        - Sprint

Left Click  - Place Block
Right Click - Break Block

Scroll Wheel - Change Block

P - Save World
L - Load World
M - Spawn Power Cube

ESC - Return To Menu

Press ENTER To Start
""",
            position=(0, 0),
            origin=(0, 0),
            scale=1.3,
            enabled=True
        )

    # ==================================================
    # UPDATE
    # ==================================================

    def update(self):

        state = self.game.state

        hp = state["player_health"]
        max_hp = state["max_health"]

        # ---------------- HEALTH BAR ----------------

        ratio = max(hp / max_hp, 0)

        self.health_bar.scale_x = 0.5 * ratio

        if hp > 20:
            self.health_bar.color = color.lime
        else:
            self.health_bar.color = color.red

        # ---------------- DAMAGE FLASH ----------------

        if hp < self.last_hp:

            self.hitscreen.enabled = True

            invoke(
                setattr,
                self.hitscreen,
                'enabled',
                False,
                delay=0.15
            )

        self.last_hp = hp

        # ---------------- CURRENT BLOCK ----------------

        block = state["block_types"][
            state["current_block_index"]
        ]

        self.block_text.text = f'Block: {block["name"]}'

    # ==================================================
    # INPUT
    # ==================================================

    def input(self, key):

        if key == 'enter':

            self.game.state["instructions_open"] = False

            self.instruction_bg.enabled = False
            self.instructions.enabled = False

    # ==================================================
    # DESTROY
    # ==================================================

    def destroy(self):

        destroy(self.health_bar)
        destroy(self.block_text)
        destroy(self.hitscreen)
        destroy(self.instruction_bg)
        destroy(self.instructions)