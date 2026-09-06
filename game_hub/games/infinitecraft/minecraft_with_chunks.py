from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import os
import ast


class InfiniteCraft:
    '''
    Ifinitecraft is an endles flat snadbox game where everything is made of blocks and gets saved regularly in a json file.
    '''

    def __init__(self):

        self.CHUNK_SIZE = 16
        self.RENDER_DISTANCE = 1

        self.BASE_DIR = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.block_types = [
            {'name': 'Stone', 'texture': 'white_cube', 'color': color.gray},
            {'name': 'Bricks', 'texture': 'brick', 'color': color.brown},
            {'name': 'Red Block', 'texture': 'white_cube', 'color': color.red},
            {'name': 'Blue Block', 'texture': 'white_cube', 'color': color.azure},
            {'name': 'Orange Block', 'texture': 'white_cube', 'color': color.orange},
        ]

        self.current_block_index = 0
        self.current_block = self.block_types[0]

        self.entities = []
        self.ui_elements = []

        self.loaded_chunks = {}
        self.chunk_data = {}
        self.saves = {}

        self.player = None
        self.block_text = None
        self.coords_text = None
        self.cyan_marker = None
        # ---------------- LOAD WORLD ----------------

        self.load_chunk_data()

        # ---------------- PLAYER ----------------

        self.player = FirstPersonController()
        self.entities.append(self.player)

        # ---------------- SKY ----------------

        self.sky = Sky()
        self.entities.append(self.sky)

        # ---------------- UI ----------------

        self.block_text = Text(
            text=f"Current Block: {self.current_block['name']}",
            position=window.top_left,
            scale=1.5,
            origin=(-.5, .5)
        )

        self.coords_text = Text(
            text="",
            position=window.top_right,
            scale=1.25,
            origin=(.5, .5)
        )

        self.ui_elements.extend([
            self.block_text,
            self.coords_text
        ])

        # ---------------- START CHUNKS ----------------

        self.update_chunks()
        
    def save_chunk_data(self):

        print("SAVING CHUNK DATA...")

        # Sync loaded chunks into chunk_data
        for chunk_pos, chunk in self.loaded_chunks.items():
            self.chunk_data[chunk_pos] = chunk['data']

        save_data = {}

        # Convert ALL tuple keys to strings
        for chunk_pos, block_data in self.chunk_data.items():

            save_data[str(chunk_pos)] = {
                str(block_pos): block_index
                for block_pos, block_index in block_data.items()
            }

        final_path = os.path.join(self.BASE_DIR, "world_data.json")
        temp_path = final_path + ".tmp"

        with open(temp_path, "w") as f:
            json.dump(save_data, f, indent=4)

            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, final_path)

        print("WORLD SAVED!")
            
    def load_chunk_data(self):

        path = os.path.join(self.BASE_DIR, 'world_data.json')

        if not os.path.exists(path):
            return

        try:

            with open(path, 'r') as f:

                raw_data = json.load(f)

            self.chunk_data = {}

            for chunk_key, block_data in raw_data.items():

                chunk_pos = ast.literal_eval(chunk_key)

                self.chunk_data[chunk_pos] = {
                    ast.literal_eval(block_pos): block_index
                    for block_pos, block_index in block_data.items()
                }

            print("WORLD LOADED!")

        except Exception as e:

            print(f"FAILED TO LOAD WORLD: {e}")
            self.chunk_data = {}
                    
    def generate_chunk(self, cx, cz):

        base_x = cx * self.CHUNK_SIZE
        base_z = cz * self.CHUNK_SIZE

        chunk_blocks = []

        block_data = self.chunk_data.get(
            (cx, cz),
            {}
        )

        for x in range(self.CHUNK_SIZE):

            for z in range(self.CHUNK_SIZE):

                b = Button(
                    texture='grass',
                    model='cube',
                    position=(
                        base_x + x,
                        0,
                        base_z + z
                    ),
                    parent=scene,
                    origin_y=0.5,
                    color=color.white
                )

                chunk_blocks.append(b)
                self.entities.append(b)

        for pos, block_index in block_data.items():

            info = self.block_types[block_index]

            b = Button(
                texture=info['texture'],
                color=info['color'],
                model='cube',
                position=Vec3(*pos),
                parent=scene,
                origin_y=0.5
            )

            chunk_blocks.append(b)
            self.entities.append(b)

        self.loaded_chunks[(cx, cz)] = {
            'blocks': chunk_blocks,
            'data': block_data
        }
    
    def unload_chunk(self, cx, cz):
        chunk = self.loaded_chunks.pop((cx, cz), None)
        if chunk:
            for b in chunk['blocks']:
                destroy(b)
            self.chunk_data[(cx, cz)] = chunk['data']
    
    def player_chunk(self):
        return int(self.player.x) // self.CHUNK_SIZE, int(self.player.z) // self.CHUNK_SIZE
    
    def update_chunks(self):
        pcx, pcz = self.player_chunk()
        self.active = set()

        # Load surrounding chunks (3x3)
        for dx in range(-self.RENDER_DISTANCE, self.RENDER_DISTANCE + 1):
            for dz in range(-self.RENDER_DISTANCE, self.RENDER_DISTANCE + 1):
                key = (pcx + dx, pcz + dz)
                self.active.add(key)
                if key not in self.loaded_chunks:
                    self.generate_chunk(*key)

        # Unload far chunks
        for key in list(self.loaded_chunks.keys()):
            if key not in self.active:
                self.unload_chunk(*key)
    
    def add_block(self, pos, block_index):
        pos_key = (round(pos.x), round(pos.y), round(pos.z))
        cx, cz = int(pos.x) // self.CHUNK_SIZE, int(pos.z) // self.CHUNK_SIZE
        chunk = self.loaded_chunks.get((cx, cz))
        if not chunk or pos_key in chunk['data']:
            return

        chunk['data'][pos_key] = block_index
        info = self.block_types[block_index]
        b = Button(texture=info['texture'], color=info['color'],
                model='cube', position=Vec3(*pos_key),
                parent=scene, origin_y=0.5)
        chunk['blocks'].append(b)
            
    def remove_block(self, b):
        pos = b.position
        cx, cz = int(pos.x) // self.CHUNK_SIZE, int(pos.z) // self.CHUNK_SIZE
        chunk = self.loaded_chunks.get((cx, cz))
        if not chunk:
            return

        pos_key = (round(pos.x), round(pos.y), round(pos.z))
        chunk['data'].pop(pos_key, None)
        if b in chunk['blocks']:
            chunk['blocks'].remove(b)
        destroy(b)
    
    def input(self, key):

        if key in ['scroll up', 'scroll down']:
            self.current_block_index = (self.current_block_index + (1 if key == 'scroll up' else -1)) % len(self.block_types)
            self.current_block = self.block_types[self.current_block_index]
            self.block_text.text = f"Current Block: {self.current_block['name']}"

        if mouse.hovered_entity:
            b = mouse.hovered_entity
            if isinstance(b, Button):
                if key == 'left mouse down':
                    pos = b.position + mouse.normal
                    if pos.y >= 0:
                        self.add_block(pos, self.current_block_index)
                elif key == 'right mouse down':

                    if getattr(b, 'is_marker', False):
                        return

                    if b.texture != 'grass':
                        self.remove_block(b)
    
    def update(self):

        self.update_chunks()

        self.player.speed = 10 if held_keys['r'] else 5

        self.coords_text.text = (
            f"X: {int(self.player.x)} "
            f"Y: {int(self.player.y)} "
            f"Z: {int(self.player.z)}"
        )

        player_x = round(self.player.x)
        player_z = round(self.player.z)

        marker_position = (
            player_x,
            -1,
            player_z
        )

        if self.cyan_marker is None or not self.cyan_marker.enabled:

            self.cyan_marker = Button(
                texture='white_cube',
                color=color.cyan,
                model='cube',
                position=marker_position,
                parent=scene,
                origin_y=0,
                collider='box'
            )
            self.cyan_marker.is_marker = True

        elif self.cyan_marker.position != marker_position:

            self.cyan_marker.position = marker_position
        
    def destroy(self):

        print("DESTROYING MYSELF:(")
        self.save_chunk_data()

        for chunk in self.loaded_chunks.values():

            for block in chunk['blocks']:

                destroy(block)

        for entity in self.entities.copy():

            destroy(entity)

        for ui in self.ui_elements.copy():

            destroy(ui)

        if self.cyan_marker:

            destroy(self.cyan_marker)

        self.entities.clear()
        self.ui_elements.clear()

        self.loaded_chunks.clear()
        self.chunk_data.clear()

        self.player = None
        self.cyan_marker = None

        camera.parent = scene
        camera.rotation_x = 0
        camera.rotation_y = 0
        camera.rotation_z = 0
        camera.position = (0, 0, 0)