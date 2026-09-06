from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import *


class MinecraftPlayer:

    def __init__(self, game):

        self.game = game

        self.player = FirstPersonController()
        self.player.speed = 5

        self.health = 100
        self.max_health = 100

    def update(self):

        if self.game.state["instructions_open"]:

            self.player.speed = 0
            return

    def input(self, key):
        if held_keys['r']:
            self.player.speed = 10
        else:
            self.player.speed = 5

    def destroy(self):
        destroy(self.player)