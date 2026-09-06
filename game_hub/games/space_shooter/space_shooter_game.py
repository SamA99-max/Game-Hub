from ursina import *
import random
import math
import time as pytime


class SpaceShooter:
    '''
    SpaceShooter is a simple space shooter game where the player can move left and right and shoot bullets at enemies.
    The enemies spawn randomly and move downwards. The player can collect upgrades to increase their abilities. 
    The player can also face a boss that spawns after a certain amount of time.
    '''

    # =====================================================
    # PLAYER
    # =====================================================
    class Player(Entity):

        def __init__(self, game):
            self.game = game

            super().__init__(
                model='quad',
                color=color.cyan,
                scale=(0.1, 0.15),
                position=(0, -0.4)
            )

            self.hp = 10
            self.max_hp = 10
            self.multi = 1
            self.fire_rate = 0.15
            self.heal_potions = 0
            self.last_shot = 0
            self.damage = 2

            self.shield_active = False
            self.shield_duration = 5
            self.shield_pytimer = 0
            self.shield_cooldown = 8
            self.shield_cooldown_pytimer = 0

            self.shield_visual = Entity(
                parent=self,
                model='circle',
                color=color.rgba(0, 150, 255, 0.33),
                scale=1.8,
                enabled=False
            )

        def shoot(self):
            if pytime.time() - self.last_shot < self.fire_rate:
                return

            self.last_shot = pytime.time()

            for i in range(self.multi):
                spread = (i - (self.multi - 1) / 2) * 0.05

                bullet = SpaceShooter.Bullet(
                    self.game,
                    position=self.position + Vec3(spread, 0.05, 0)
                )

                self.game.bullets.append(bullet)

    # =====================================================
    # BULLET
    # =====================================================
    class Bullet(Entity):

        def __init__(self, game, **kwargs):
            self.game = game

            super().__init__(
                model='quad',
                color=color.yellow,
                scale=(0.02, 0.05),
                **kwargs
            )

            self.speed = 2

        def update(self):
            if not self.enabled:
                return
            self.y += self.speed * pytime.dt

            if self.y > 0.7:
                if self in self.game.bullets:
                    self.game.bullets.remove(self)
                destroy(self)

    # =====================================================
    # ENEMY BASE
    # =====================================================
    class Enemy(Entity):

        def __init__(self, game):
            self.game = game

            super().__init__(
                model='circle',
                color=color.red,
                scale=0.06,
                position=(random.uniform(-0.8, 0.8), 0.7, 0)
            )

            self.speed = random.uniform(0.2, 0.4)
            self.shield = random.random() < 0.25

            if self.shield:
                self.shield_visual = Entity(
                    parent=self,
                    model='circle',
                    color=color.rgba(0, 150, 255, 0.33),
                    scale=1.8
                )

            self.game.enemies.append(self)

        def update(self):
            if not self.enabled:
                return
            player = self.game.player
            if not player:
                destroy(self)
                return
            self.y -= self.speed * pytime.dt

            if distance(self.position, player.position) < 0.08:
                if not player.shield_active:
                    player.hp -= 1

                self.destroy_self()
                return

            if self.y < -0.7:
                self.destroy_self()

        def destroy_self(self):
            if self in self.game.enemies:
                self.game.enemies.remove(self)
            destroy(self)

    # =====================================================
    # KAMIKAZE
    # =====================================================
    class KamikazeEnemy(Enemy):
        
        def __init__(self, game):
            super().__init__(game)
            self.color = color.orange
            self.speed = random.uniform(0.3, 0.5)

        def update(self):
            if not self.enabled:
                return
            player = self.game.player
            if not player:
                destroy(self)
                return
            direction = player.position - self.position

            if direction.length() > 0:
                direction = direction.normalized()

            self.position += direction * 0.8 * pytime.dt

            if distance(self.position, player.position) < 0.08:
                if not player.shield_active:
                    player.hp -= 1.5

                self.destroy_self()

    # =====================================================
    # SNIPER ENEMY
    # =====================================================
    class SniperEnemy(Enemy):

        def __init__(self, game):
            super().__init__(game)
            self.color = color.azure
            self.speed = 0.15
            self.shoot_pytimer = 0

        def update(self):
            if not self.enabled:
                return
            player = self.game.player
            if not player:
                destroy(self)
                return
            super().update()

            self.shoot_pytimer += pytime.dt

            if self.shoot_pytimer >= 2:
                self.shoot_pytimer = 0

                direction = player.position - self.position
                if direction.length() > 0:
                    direction = direction.normalized()

                SpaceShooter.SniperBullet(
                    self.game,
                    direction=direction,
                    position=self.position
                )

    # =====================================================
    # SNIPER BULLET
    # =====================================================
    class SniperBullet(Entity):

        def __init__(self, game, direction, **kwargs):
            self.game = game
            self.direction = direction

            super().__init__(
                model='quad',
                color=color.white,
                scale=0.025,
                **kwargs
            )

            self.speed = 0.7

        def update(self):
            if not self.enabled:
                return
            player = self.game.player
            if not player:
                destroy(self)
                return
            self.position += self.direction * self.speed * pytime.dt

            if distance(self.position, player.position) < 0.06:
                if not player.shield_active:
                    player.hp -= 0.5
                destroy(self)

            if not self or not self.enabled:
                return

            if abs(self.x) > 1 or abs(self.y) > 1:
                destroy(self)
                return

    # =====================================================
    # BOSS BULLET
    # =====================================================
    class BossBullet(Entity):

        def __init__(self, game, dx=0, **kwargs):
            self.game = game

            super().__init__(
                model='quad',
                color=color.orange,
                scale=0.03,
                **kwargs
            )

            self.dx = dx
            self.dy = -0.4
            self.game.boss_bullets.append(self)

        def update(self):
            if not self.enabled:
                return
            player = self.game.player
            if not player:
                destroy(self)
                return
            self.x += self.dx * pytime.dt
            self.y += self.dy * pytime.dt

            if distance(self.position, player.position) < 0.06:
                if not player.shield_active:
                    player.hp -= 1
                self.destroy_self()
                return

            if self.y < -0.7:
                self.destroy_self()

        def destroy_self(self):
            if self in self.game.boss_bullets:
                self.game.boss_bullets.remove(self)
            destroy(self)

    # =====================================================
    # UPGRADE
    # =====================================================
    class Upgrade(Entity):

        def __init__(self, game, kind, **kwargs):
            self.game = game
            self.kind = kind

            super().__init__(
                model='quad',
                color={
                    "multi": color.lime,
                    "damage": color.red,
                    "heal": color.azure
                }[kind],
                scale=0.05,
                **kwargs
            )

            self.game.upgrades.append(self)

        def update(self):
            if not self.enabled:
                return
            self.y -= 0.2 * pytime.dt
            player = self.game.player
            if not player:
                destroy(self)
                return

            if distance(self.position, player.position) < 0.08:

                if self.kind == "multi":
                    player.multi = min(player.multi + 1, 8)

                elif self.kind == "damage":
                    player.damage += 2

                elif self.kind == "heal":
                    self.game.game_heal()

                self.destroy_self()

        def destroy_self(self):
            if self in self.game.upgrades:
                self.game.upgrades.remove(self)
            destroy(self)

    # =====================================================
    # BOSS
    # =====================================================
    class Boss(Entity):

        def __init__(self, game):
            self.game = game

            super().__init__(
                model='circle',
                color=color.violet,
                scale=0.25,
                position=(0, 0.4)
            )

            self.max_hp = 30 + game.player.multi * 15 + game.player.damage * 20
            self.hp = self.max_hp

            self.move_pytimer = 0
            self.shoot_pytimer = 0

        def update(self):
            if not self.enabled:
                return
            self.move_pytimer += pytime.dt
            self.shoot_pytimer += pytime.dt

            self.x += math.sin(self.move_pytimer * 2) * 0.002

            if self.shoot_pytimer >= 2:
                self.shoot_pytimer = 0
                self.shoot()

        def shoot(self):
            for a in range(-1, 2):
                SpaceShooter.BossBullet(
                    self.game,
                    position=self.position,
                    dx=a * 0.15
                )

    # =====================================================
    # GAME CORE
    # =====================================================
    def __init__(self):
        self.sky = Entity(
            model = 'quad',
            texture = 'background.jpg',
            scale = (2, 2),
            position = (0, 0, 1)
        )
        self.enemies = []
        self.bullets = []
        self.boss_bullets = []
        self.upgrades = []

        self.score = 0
        self.game_over = False
        self.boss = None
        self.bosses_defeated = 0

        self.spawn_pytimer = 0
        self.boss_pytimer = 0

        self.player = self.Player(self)

        self.ui = Text(position=(-0.85, 0.45), scale=1.2)
        self.game_over_text = Text(scale=3)

        self.boss_bar_bg = Entity(parent=camera.ui, model='quad', color=color.black,
                                 scale=(0.82, 0.045), position=(0, 0.45))

        self.boss_bar = Entity(parent=camera.ui, model='quad', color=color.lime,
                             scale=(0.8, 0.03), position=(0, 0.45, -0.01))

        self.boss_name = Text(text="VOID BOSS", parent=camera.ui,
                              position=(0, 0.49), scale=1.5)

        self.boss_bar.visible = False
        self.boss_bar_bg.visible = False
        self.boss_name.visible = False
        camera.orthographic = True
        camera.fov = 0.5

    # =====================================================
    # HEAL SYSTEM
    # =====================================================
    def game_heal(self):

        p = self.player

        if p.hp >= p.max_hp:
            p.heal_potions += 1
            return

        if p.hp <= 3:
            p.hp = min(p.max_hp, p.hp + 5)
        elif p.hp <= 7:
            p.hp = min(p.max_hp, p.hp + 3)
        else:
            p.hp = min(p.max_hp, p.hp + 1.5)

    # =====================================================
    # INPUT
    # =====================================================
    def input(self, key):

        p = self.player

        if key == 'h':
            if p.heal_potions > 0 and p.hp < p.max_hp:
                p.heal_potions -= 1
                self.game_heal()

        if key == 's':
            if not p.shield_active and p.shield_cooldown_pytimer <= 0:
                p.shield_active = True
                p.shield_visual.enabled = True
                p.shield_cooldown_pytimer = p.shield_cooldown

        if key == 'r' and self.game_over:
            self.restart()

    # =====================================================
    # RESTART
    # =====================================================
    def restart(self):

        for obj in self.enemies + self.bullets + self.boss_bullets + self.upgrades:
            destroy(obj)

        if self.boss:
            destroy(self.boss)

        self.enemies.clear()
        self.bullets.clear()
        self.boss_bullets.clear()
        self.upgrades.clear()

        self.score = 0
        self.boss = None
        self.spawn_pytimer = 0
        self.boss_pytimer = 0
        self.game_over = False

        p = self.player
        p.hp = 10
        p.multi = 1
        p.damage = 2
        p.heal_potions = 0
        p.position = (0, -0.4)

        self.game_over_text.text = ""

        self.boss_bar.visible = False
        self.boss_bar_bg.visible = False
        self.boss_name.visible = False

    def update_boss_bar(self):

        if self.boss:

            hp_percent = max(0, self.boss.hp / self.boss.max_hp)

            self.boss_bar.scale_x = 0.8 * hp_percent
            self.boss_bar.x = -(0.8 - self.boss_bar.scale_x) / 2

            self.boss_bar.color = color.rgb(
                int(255 * (1 - hp_percent)),
                int(255 * hp_percent),
                0
            )

            self.boss_bar.visible = True
            self.boss_bar_bg.visible = True
            self.boss_name.visible = True

        else:
            self.boss_bar.visible = False
            self.boss_bar_bg.visible = False
            self.boss_name.visible = False

    # =====================================================
    # UPDATE LOOP
    # =====================================================
    def update(self):

        if self.game_over:
            return

        p = self.player

        if p.shield_active:
            p.shield_pytimer += pytime.dt

            if p.shield_pytimer >= p.shield_duration:
                p.shield_active = False
                p.shield_visual.enabled = False
                p.shield_pytimer = 0

        if p.shield_cooldown_pytimer > 0:
            p.shield_cooldown_pytimer -= pytime.dt
        # movement
        speed = 1.5 * pytime.dt
        if held_keys['a'] or held_keys['left arrow']:
            p.x -= speed
        if held_keys['d'] or held_keys['right arrow']:
            p.x += speed

        p.x = clamp(p.x, -0.9, 0.9)

        if held_keys['space']:
            p.shoot()

        # spawn
        self.spawn_pytimer += pytime.dt
        if self.spawn_pytimer > 0.7:
            self.spawn_pytimer = 0

            roll = random.random()

            if self.bosses_defeated > 2 and roll < 0.15:
                self.KamikazeEnemy(self)

            elif self.bosses_defeated >= 4 and roll < 0.30:
                self.SniperEnemy(self)
            else:
                self.Enemy(self)

        # boss spawn
        self.boss_pytimer += pytime.dt
        if self.boss_pytimer > 20 and self.boss is None:
            self.boss_pytimer = 0
            self.boss = self.Boss(self)

        # collisions + boss logic (kept compact for engine use)
        if p.hp <= 0:
            self.game_over = True
            self.game_over_text.text = "GAME OVER\nPress R"

        self.ui.text = (
            f"Score: {self.score} | "
            f"HP: {p.hp:.1f}/{p.max_hp} | "
            f"Multi: {p.multi} | "
            f"Damage: {p.damage} | "
            f"Heals: {p.heal_potions} | "
            f"Shield: {'ON' if p.shield_active else 'OFF'}"
        )
        for b in self.bullets.copy():

            if not b or not b.enabled:
                continue

            for e in self.enemies.copy():

                if not e or not e.enabled:
                    continue

                if distance(b.world_position, e.world_position) < 0.06:

                    # shield logic
                    if hasattr(e, "shield") and e.shield:
                        e.shield = False
                        if hasattr(e, "shield_visual"):
                            destroy(e.shield_visual)

                    else:
                        self.score += 1

                        if random.random() < 0.15:
                            self.Upgrade(self, "heal", position=e.position)

                        e.destroy_self()

                    if b in self.bullets:
                        self.bullets.remove(b)
                    destroy(b)
                    break
            # ---------------- BOSS COLLISION ----------------
            if self.boss:

                for b in self.bullets.copy():

                    if not b or not b.enabled:
                        continue

                    if distance(b.world_position, self.boss.world_position) < 0.15:

                        self.boss.hp -= self.player.damage

                        if b in self.bullets:
                            self.bullets.remove(b)

                        destroy(b)

                        # boss death
                        if self.boss.hp <= 0:
                            self.score += 20
                            self.bosses_defeated += 1

                            # ---------------- DROP UPGRADE ----------------
                            drop_type = random.choice(["multi", "damage"])

                            self.Upgrade(
                                self,
                                drop_type,
                                position=self.boss.position
                            )

                            destroy(self.boss)
                            self.boss = None

                        break
        self.update_boss_bar()
            
    def destroy(self):

        # ---- mark game as dead FIRST ----
        self.game_over = True

        # ---- destroy player ----
        if self.player:
            destroy(self.player)
            self.player = None

        # ---- destroy ALL enemies ----
        for e in self.enemies:
            destroy(e)
        self.enemies.clear()

        # ---- destroy ALL bullets ----
        for b in self.bullets:
            destroy(b)
        self.bullets.clear()

        # ---- destroy boss ----
        if self.boss:
            destroy(self.boss)
            self.boss = None

        # ---- destroy boss bullets ----
        for b in self.boss_bullets:
            destroy(b)
        self.boss_bullets.clear()

        # ---- destroy upgrades ----
        for u in self.upgrades:
            destroy(u)
        self.upgrades.clear()

        # ---- destroy UI elements ----
        destroy(self.ui)
        destroy(self.game_over_text)
        destroy(self.boss_bar)
        destroy(self.boss_bar_bg)
        destroy(self.boss_name)
        destroy(self.sky)

        # ---- IMPORTANT: stop camera from following old game ----
        camera.parent = scene
        