from ursina import *
from random import randint

class ItemSystem:

    def __init__(self, game):
        self.game = game
        self.power_cube = None

    def spawn_power_cube(self):
        state = self.game.state

        if state["power_cube"]:
            return

        rx, rz = randint(1, 30), randint(1, 30)

        def on_click():
            state["block_types"].append({
                'name': f'Power Block {len(state["block_types"])}',
                'texture': 'white_cube',
                'color': color.hsv(randint(0, 360), 1, 1)
            })

            destroy(state["power_cube"])
            state["power_cube"] = None

        cube = Button(
            model='cube',
            texture='white_cube',
            color=color.azure,
            position=(rx, 1, rz),
            parent=scene,
            on_click=on_click
        )

        state["power_cube"] = cube
        state["boxes"].append(cube)

    def input(self, key):
        if key == 'm':
            self.spawn_power_cube()
        if 'left mouse down' in key and self.game.state["power_cube"] and self.game.state["power_cube"].hovered:
            self.game.state["power_cube"].on_click()
    
    def update(self):
        pass