from ursina import *
from random import randint
from games.minecraft.assets import Assets


class Enemy:

    def __init__(self, game, pos):

        self.game = game
        self.state = game.state
        self.assets = Assets()

        self.entity = Entity(
            model='cube',
            color=color.red,
            position=pos,
            collider='box',
            parent=scene,
            scale=(1, 2, 1)
        )

        self.health = 3
        self.cooldown = 0

    # ---------------- DISTANCE ----------------

    def distance_xz(self, a, b):
        return ((a.x - b.x) ** 2 + (a.z - b.z) ** 2) ** 0.5

    # ---------------- UPDATE ----------------

    def update(self):

        state = self.state
        
        if self.state["instructions_open"]:
            return

        if state["game_over"]:
            return

        player = self.game.player.player

        if not player:
            return

        direction = (
            player.position - self.entity.position
        ).normalized()

        # wall detection
        hit = raycast(
            origin=self.entity.position + Vec3(0, 1, 0),
            direction=direction,
            distance=0.6,
            ignore=(self.entity,)
        )

        if not hit.hit:

            self.entity.position += direction * time.dt * 2

        else:

            side = Vec3(direction.z, 0, -direction.x)

            side_hit = raycast(
                origin=self.entity.position + Vec3(0, 1, 0),
                direction=side,
                distance=0.6,
                ignore=(self.entity,)
            )

            if not side_hit.hit:
                self.entity.position += side * time.dt * 1.5

        # ---------------- ATTACK ----------------

        if self.distance_xz(
            self.entity.position,
            player.position
        ) < 1.5 and self.cooldown <= 0:

            state["player_health"] -= 5
            self.cooldown = 1.5
            self.assets.attack.play()
            self.entity.animate_color(color.white, duration=0.1)

        else:

            self.cooldown -= time.dt

        # ---------------- DEATH ----------------

        if self.health <= 0:

            if self in self.game.enemies.enemies:
                self.game.enemies.enemies.remove(self)

            destroy(self.entity)
        
        if state["player_health"] <= 0:
            state["game_over"] = True
        if state["game_over"]:
            self.entity.color = color.gray
            return    

# =========================================================


class EnemySystem:

    def __init__(self, game):

        self.game = game
        self.state = game.state

        self.enemies = []

        self.spawn()

    # ---------------- SPAWN ----------------

    def spawn(self):

        for i in range(5):

            enemy = Enemy(
                self.game,
                (randint(5, 20), 1, randint(5, 20))
            )

            self.enemies.append(enemy)

    # ---------------- INPUT ----------------

    def input(self, key):

        for e in self.enemies[:]:

            if e.entity.hovered and key == 'left mouse down':

                e.health -= 1

                e.entity.color = color.rgb(
                    255,
                    max(0, 100 + e.health * 50),
                    100
                )

    # ---------------- UPDATE ----------------

    def update(self):

        if self.state["game_over"]:
            return

        for e in self.enemies[:]:
            e.update()

    # ---------------- DESTROY ----------------

    def destroy(self):

        for e in self.enemies[:]:

            destroy(e.entity)

        self.enemies.clear()