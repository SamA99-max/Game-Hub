from ursina import Audio


class Assets:

    def __init__(self):

        # ---------------- SOUNDS ----------------
        self.jump = Audio('sounds/jump.mp3', autoplay=False)
        self.walk = Audio('sounds/walk.mp3', loop=True, autoplay=False)

        self.place = Audio('sounds/place.wav', autoplay=False)
        self.break_block = Audio('sounds/break.mp3', autoplay=False)

        self.attack = Audio('sounds/click.wav', autoplay=False)

        self.player_hit = Audio('sounds/player_damage.mp3', autoplay=False)

        self.zombie_idle = Audio('sounds/zombie.mp3', autoplay=False)
        self.skeleton_idle = Audio('sounds/skeleton.mp3', autoplay=False)

        # ---------------- UI / FEEDBACK ----------------
        self.ui_click = Audio('sounds/click.wav', autoplay=False)

    def destroy(self):
        # Ursina cleans Audio automatically, but we keep structure consistent
        pass