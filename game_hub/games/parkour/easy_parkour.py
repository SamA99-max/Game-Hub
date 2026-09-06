from ursina import *
import random

class EasyParkour:
    '''
    EasyParkour is a simple parkour game where the player can move left and right and jump on platforms.
    The platforms are generated infinitely as the player moves forward.
    The player can fall off the platforms and reset to the starting position. 
    The game uses basic physics for gravity and collision detection.
    '''

    def __init__(self):

        self.entities = []
        self.ui_elements = []

        # ---------------- PLAYER ----------------
        self.player = Entity(
            model='cube',
            texture='white_cube',
            color=color.azure,
            scale=(0.5, 1.0, 0.5),   # smaller player
            position=(0, 2, 0),
            collider='box'
        )
        self.entities.append(self.player)

        # ---------------- CAMERA ----------------
        camera.parent = self.player
        camera.position = (0, 8, -20)
        camera.rotation_x = 15
        camera.fov = 90

        # ---------------- PHYSICS ----------------
        self.y_velocity = 0
        self.on_ground = False

        self.speed = 7
        self.jump_power = 0.5   # smaller jump

        # ---------------- WORLD ----------------
        self.platforms = []
        self.world_end = 0
        
        # ---------------- STARTING WORLD ----------------
        self.create_platform(0, 0)
        self.world_end = 5

        for i in range(6):
            self.create_platform(self.world_end, random.randint(-1, 3))
            self.world_end += random.randint(4, 7)

    def create_platform(self, x, y):
        
        p = Entity(
            model='cube',
            texture='grass',
            scale=(4, 1, 4),   # smaller platforms
            position=(x, y, 0),
            collider='box'
        )
        self.platforms.append(p)
        self.entities.append(p)


    def update(self):
        # ---------------- MOVEMENT (ARROWS ONLY) ----------------
        if held_keys['left arrow']:
            self.player.x -= time.dt * self.speed
        if held_keys['right arrow']:
            self.player.x += time.dt * self.speed

        # ---------------- GRAVITY ----------------
        self.y_velocity -= 1.5 * time.dt
        self.player.y += self.y_velocity

        # ---------------- COLLISION ----------------
        self.on_ground = False
        hit = self.player.intersects()

        if hit.hit:
            if self.y_velocity <= 0:
                self.player.y = hit.entity.y + 1
                self.y_velocity = 0
                self.on_ground = True

        # ---------------- JUMP (UP ARROW) ----------------
        if held_keys['up arrow'] and self.on_ground:
            self.y_velocity = self.jump_power

        # ---------------- INFINITE WORLD ----------------
        while self.world_end < self.player.x + 50:
            self.create_platform(self.world_end, random.randint(-1, 4))
            self.world_end += random.randint(4, 7)

        # ---------------- RESET ----------------
        if self.player.y < -10:
            self.player.position = (0, 2, 0)
            self.y_velocity = 0



    def destroy(self):

        for entity in self.entities.copy():
            destroy(entity)
            
        for ui in self.ui_elements.copy():
            destroy(ui)

        self.player = None
        self.entities.clear()
        self.ui_elements.clear()
        self.platforms.clear()
        camera.parent = scene
        camera.rotation_x = 0
        camera.rotation_y = 0
        camera.rotation_z = 0
        camera.position = (0, 0, 0)
