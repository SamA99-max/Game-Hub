from ursina import *
import random


class HardParkour:
    '''
    HardParkour is a slighlty more challenging parkour game where the player can move left and right and jump on platforms.
    The platforms are generated infinitely as the player moves forward.
    There are coins to collect and moving platforms to jump on.
    The player can fall off the platforms and reset to the starting position.
    WARNING: Sometimes the score glitches and the platform score updates to fast, but doesn't affect gameplay. Orient yourself upon the coins-counter.
    '''

    def __init__(self):

        # ---------------- STORAGE ----------------

        self.entities = []
        self.ui_elements = []

        # ---------------- PLAYER ----------------

        self.player = Entity(
            model='cube',
            texture='white_cube',
            color=color.azure,
            scale=(0.5, 1, 0.5),
            position=(0, 2, 0),
            collider='box'
        )

        self.entities.append(self.player)
        self.dead = False

        # ---------------- CAMERA ----------------

        camera.parent = self.player
        camera.position = (0, 8, -20)
        camera.rotation_x = 15

        # ---------------- PHYSICS ----------------

        self.y_velocity = 0
        self.on_ground = False

        self.speed = 7
        self.jump_power = 0.5

        # ---------------- DASH ----------------

        self.dash_forward = 6

        # ---------------- SCORE ----------------

        self.score = 0
        self.coin_score = 0
        self.platform_score = 0

        self.last_platform = None

        self.score_text = Text(
            '',
            position=(-0.85, 0.45),
            scale=1.5
        )

        self.ui_elements.append(self.score_text)

        # ---------------- WORLD ----------------

        self.platforms = []
        self.coins = []
        self.coin_positions = []

        self.world_end = 0
        
        self.build_world()
    
    class MovingPlatform(Entity):

        def __init__(self, game, x, y):

            self.game = game

            super().__init__(
                model='cube',
                texture='white_cube',
                color=color.rgb(180, 220, 180),
                scale=(4, 1, 4),
                position=(x, y, 0),
                collider='box'
            )

            self.start_x = x
            self.speed = random.uniform(1.0, 2.5) * random.choice([-1, 1])
            self.range = random.uniform(2, 6)
            self.last_x = self.x

        def update(self):

            if not self.game.player:
                return

            self.last_x = self.x

            next_x = self.x + self.speed * time.dt

            for p in self.game.platforms.copy():

                if p is not self and abs(p.x - next_x) < 2 and abs(p.y - self.y) < 1:
                    self.speed *= -1
                    return

            self.x = next_x

            if abs(self.x - self.start_x) > self.range:
                self.speed *= -1

        @property
        def dx(self):
            return self.x - self.last_x

    def update_score(self):
        self.score_text.text = f'Score: {self.score} | Coins: {self.coin_score} | Platforms: {self.platform_score}'

    def create_coin(self, x, y, save=True):
        pos = (x, y + 1.5)

        if save:
            self.coin_positions.append(pos)

        c = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.4,
            position=(pos[0], pos[1], 0),
            collider='box'
        )
        self.coins.append(c)
        self.entities.append(c)
    
    def create_platform(self, x, y):
        if random.random() < 0.3:
            p = self.MovingPlatform(self, x, y)
        else:
            p = Entity(
                model='cube',
                texture='grass',
                scale=(4, 1, 4),
                position=(x, y, 0),
                collider='box'
            )
        self.platforms.append(p)
        self.entities.append(p)
        
        if random.random() < 0.6:
            self.create_coin(x, y)
        
    def build_world(self):
        for entity in self.entities.copy():
            if entity != self.player:
                destroy(entity)

        self.entities = [self.player]
        self.platforms.clear()
        self.coins.clear()
        self.coin_positions.clear()

        # first platform (static)
        p = Entity(
            model='cube',
            texture='grass',
            scale=(4, 1, 4),
            position=(0, 0, 0),
            collider='box'
        )
        self.platforms.append(p)
        self.entities.append(p)
        self.world_end = 5

        for i in range(8):
            self.create_platform(self.world_end, random.randint(-1, 3))
            self.world_end += random.randint(4, 7)
        
            
    def input(self, key):
        if key == 'down arrow':
            if held_keys['left arrow']:
                self.player.x -= self.dash_forward
            else:
                self.player.x += self.dash_forward

    
    def reset_game(self):
        if self.dead:
            return
        if not self.player:
            return

        self.player.position = (0, 2, 0)

        self.y_velocity = 0
        self.score = 0
        self.coin_score = 0
        self.platform_score = 0
        self.last_platform = None

        # ✅ respawn coins in same positions
        for c in self.coins.copy():
            destroy(c)
        self.coins.clear()

        for pos in self.coin_positions:
            c = Entity(
                model='sphere',
                color=color.yellow,
                scale=0.4,
                position=(pos[0], pos[1], 0),
                collider='box'
            )
            self.coins.append(c)
            self.entities.append(c)

        self.update_score()
    
    def update(self):

        if not self.player:
            return
        
        if self.dead:
            return
        # movement
        if held_keys['left arrow']:
            self.player.x -= time.dt * self.speed
        if held_keys['right arrow']:
            self.player.x += time.dt * self.speed

        # auto jump
        if held_keys['up arrow'] and self.on_ground:
            self.y_velocity = self.jump_power

        # gravity
        self.y_velocity -= 1.5 * time.dt
        self.player.y += self.y_velocity

        # collision
        self.on_ground = False

        for p in self.platforms.copy():
            if self.player.intersects(p).hit and self.y_velocity <= 0:
                self.player.y = p.y + 1
                self.y_velocity = 0
                self.on_ground = True

                if isinstance(p, self.MovingPlatform):
                    self.player.x += p.dx

                if p != self.last_platform:
                    self.platform_score += 1
                    self.score += 1
                    self.last_platform = p

        # coins
        for c in self.coins[:]:
            if self.player.intersects(c).hit:
                destroy(c)
                self.coins.remove(c)

                self.coin_score += 1
                self.score += 1

        # world generation
        while self.world_end < self.player.x + 50:
            self.create_platform(self.world_end, random.randint(-1, 4))
            self.world_end += random.randint(4, 7)

        # death
        if self.player.y < -10:
            invoke(self.reset_game, delay=0.2)

        self.update_score()
            
    def destroy(self):
        self.dead = True
        self.player = None
        for ntt in self.entities.copy():
            destroy(ntt)
        for ui in self.ui_elements.copy():
            destroy(ui)

        self.entities.clear()
        self.ui_elements.clear()
        self.platforms.clear()
        self.coins.clear()
        self.coin_positions.clear()
        camera.parent = scene
        camera.rotation_x = 0
        camera.rotation_y = 0
        camera.rotation_z = 0
        camera.position = (0, 0, 0)

            