from ursina import *
import random

class BreakoutGame:
    """
    BreakoutGame class built for a modular mini-game engine.
    Encapsulates all breakout logic, states, inner entities, particles, and 
    smooth UI swoosh actions, completely preventing Panda3D NodePath assertion errors on exit.
    """

    # Game State Constants
    STATE_START = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2

    # # Neon Colors Palette
    # COLORS = [
    #     color.hex("#FF3366"),  # Neon Red
    #     color.hex("#FF9933"),  # Neon Orange
    #     color.hex("#FFFF33"),  # Neon Yellow
    #     color.hex("#33FF33"),  # Neon Green
    #     color.hex("#33FFFF"),  # Neon Cyan
    #     color.hex("#3333FF"),  # Neon Blue
    #     color.hex("#9933FF"),  # Neon Purple
    #     color.hex("#FF33FF")   # Neon Pink
    # ]
    COLORS = [
        color.red,
        color.orange,
        color.yellow,
        color.green,
        color.cyan,
        color.blue,
        color.azure,
        color.magenta
    ]

    # =========================================================================
    # BRICK PARTICLE CLASS
    # =========================================================================
    class BrickParticle(Entity):
        def __init__(self, game, position, particle_color):
            self.game = game
            super().__init__(
                model='quad',
                color=particle_color,
                position=position,
                scale=random.uniform(0.08, 0.16),
                z=-0.2
            )
            self.velocity = Vec2(random.uniform(-3.5, 3.5), random.uniform(-1.0, 5.0))
            self.gravity = -9.8
            self.lifetime = random.uniform(0.3, 0.6)

        def update(self):
            # Guard against active updates during shutdown or paused games
            if self.game.destroyed or self.game.game_state == BreakoutGame.STATE_PAUSED:
                return

            self.lifetime -= time.dt
            if self.lifetime <= 0:
                if self in self.game.active_particles:
                    self.game.active_particles.remove(self)
                if self in self.game.entities:
                    self.game.entities.remove(self)
                destroy(self)
                return
            
            # Physics translation
            self.velocity.y += self.gravity * time.dt
            self.x += self.velocity.x * time.dt
            self.y += self.velocity.y * time.dt
            self.alpha = max(0, self.lifetime / 0.6)

    # =========================================================================
    # BALL TRAIL CLASS
    # =========================================================================
    class BallTrail(Entity):
        def __init__(self, game, position, trail_color):
            self.game = game
            super().__init__(
                model='circle',
                color=trail_color,
                position=position,
                scale=0.15,
                z=-0.05
            )
            self.lifetime = 0.25

        def update(self):
            if self.game.destroyed or self.game.game_state == BreakoutGame.STATE_PAUSED:
                return

            self.lifetime -= time.dt
            if self.lifetime <= 0:
                if self in self.game.active_trails:
                    self.game.active_trails.remove(self)
                if self in self.game.entities:
                    self.game.entities.remove(self)
                destroy(self)
                return
            
            # Fade out & size decay
            self.alpha = max(0, self.lifetime / 0.25)
            self.scale -= time.dt * 0.4

    # =========================================================================
    # POWERUP ITEM CLASS
    # =========================================================================
    class PowerUp(Entity):
        def __init__(self, game, position, p_type):
            self.game = game
            p_color = color.gold if p_type == "multiball" else color.magenta
            super().__init__(
                model='circle',
                color=p_color,
                position=position,
                scale=0.35,
                z=-0.1
            )
            self.type = p_type
            self.speed = 3.0

        def update(self):
            if self.game.destroyed or self.game.game_state == BreakoutGame.STATE_PAUSED:
                return

            # Linear fall downward
            self.y -= self.speed * time.dt
            
            # Bottom bounds sweep check
            if self.y < -6:
                if self in self.game.powerups:
                    self.game.powerups.remove(self)
                if self in self.game.entities:
                    self.game.entities.remove(self)
                destroy(self)

    # =========================================================================
    # CORE BREAKOUT INITIALIZATION
    # =========================================================================
    def __init__(self):
        # Tracker lists to avoid memory leaks
        self.entities = []
        self.ui_elements = []
        
        # Track active dynamic elements
        self.active_particles = []
        self.active_trails = []
        self.powerups = []
        self.balls = []
        self.bricks = []

        # Centralized lifecycle state guard
        self.destroyed = False

        # Save previous engine configurations
        self.old_window_color = window.color
        self.old_camera_orthographic = camera.orthographic
        self.old_camera_fov = camera.fov
        self.old_camera_position = camera.position

        # Apply breakout specialized layout configurations
        window.color = color.black
        camera.orthographic = True
        camera.fov = 14
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)

        # Game statistics & trackers
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.game_state = self.STATE_START

        # Camera Shake values
        self.camera_shake_timer = 0
        self.camera_shake_amount = 0

        # Boundary constraints
        self.walls = [
            Entity(model='quad', color=color.dark_gray, scale=(.2, 10, .5), position=(-6, 0, 0)),
            Entity(model='quad', color=color.dark_gray, scale=(.2, 10, .5), position=(6, 0, 0)),
            Entity(model='quad', color=color.dark_gray, scale=(12, .2, .5), position=(0, 5, 0))
        ]
        self.entities.extend(self.walls)

        # Main steering paddle
        self.paddle = Entity(
            model='quad',
            color=color.cyan,
            scale=(2.0, 0.3, .5),
            position=(0, -4.5, 0)
        )
        self.entities.append(self.paddle)
        
        self.paddle_base_width = 2.0
        self.paddle_timer = 0.0

        # Build UI overlays
        self.build_ui()

    # =========================================================================
    # UI SETUP & DISPLAY
    # =========================================================================
    def build_ui(self):
        self.title_text = Text(
            text="HYPER BREAKOUT",
            origin=(0, 0),
            scale=4,
            color=color.cyan,
            position=(0, 0.2)
        )
        self.ui_elements.append(self.title_text)

        self.instruction_text = Text(
            text="Press SPACE to Start\nUse LEFT / RIGHT arrows to steer paddle\nPress 'P' to Pause / 'R' to Resume",
            origin=(0, 0),
            scale=1.5,
            color=color.white,
            position=(0, -0.15)
        )
        self.ui_elements.append(self.instruction_text)

        self.hud_text = Text(
            text="Score: 0 | High Score: 0 | Level: 1",
            position=(-0.82, 0.46),
            scale=1.8,
            color=color.white,
            enabled=False
        )
        self.ui_elements.append(self.hud_text)

        self.paused_text = Text(
            text="GAME PAUSED\n\nPress 'R' or 'P' to Resume",
            origin=(0, 0),
            scale=3,
            color=color.yellow,
            position=(0, 0.05),
            enabled=False
        )
        self.ui_elements.append(self.paused_text)

    def update_ui(self):
        if not self.destroyed and self.hud_text:
            self.hud_text.text = f"Score: {self.score}  |  High Score: {self.high_score}  |  Level: {self.level}"

    # =========================================================================
    # GAMEPLAY MECHANICS & SPAWNINGS
    # =========================================================================
    def create_ball(self, position=(0, -3, -0.1), velocity=None):
        if velocity is None:
            angle = random.uniform(0.4, 0.8) * random.choice([-1, 1])
            velocity = Vec2(angle, 1.0).normalized()

        ball = Entity(
            model='circle',
            color=color.white,
            scale=0.25,
            position=position,
            z=-0.1
        )
        ball.velocity = velocity
        ball.speed = 6.0 + (self.level * 0.4)
        
        self.balls.append(ball)
        self.entities.append(ball)

    def create_bricks(self):
        # Clear any leftover bricks
        for b in self.bricks:
            if b in self.entities:
                self.entities.remove(b)
            destroy(b)
        self.bricks.clear()

        rows = min(5 + (self.level // 2), 8)
        cols = 10
        
        for y in range(rows):
            row_color = random.choice(self.COLORS)
            for x in range(cols):
                target_y = 3.8 - y * 0.45
                
                # Start brick 8 units lower for the intro "swoosh up" action
                brick = Entity(
                    model='quad',
                    color=row_color,
                    scale=(0.95, 0.35, .5),
                    position=(-4.5 + x, target_y - 8.0, 0)
                )
                brick.target_y = target_y
                brick.power = None
                
                # Assign powers RNG
                rand = random.random()
                if rand < 0.08:
                    brick.power = "multiball"
                    brick.color = color.gold
                elif rand < 0.16:
                    brick.power = "wide_paddle"
                    brick.color = color.magenta

                self.bricks.append(brick)
                self.entities.append(brick)

    def trigger_screen_shake(self, amount=0.06, duration=0.08):
        self.camera_shake_amount = amount
        self.camera_shake_timer = duration

    def spawn_particles(self, pos, p_color):
        for _ in range(12):
            p = self.BrickParticle(self, pos, p_color)
            self.active_particles.append(p)
            self.entities.append(p)

    def reset_game(self):
        self.score = 0
        self.level = 1
        self.paddle.scale_x = self.paddle_base_width
        self.paddle.x = 0
        self.paddle_timer = 0
        
        # Clean up dynamic structures
        for b in self.balls.copy():
            destroy(b)
        self.balls.clear()

        for p in self.powerups.copy():
            destroy(p)
        self.powerups.clear()

        for p in self.active_particles.copy():
            destroy(p)
        self.active_particles.clear()

        for t in self.active_trails.copy():
            destroy(t)
        self.active_trails.clear()

        self.create_bricks()
        self.create_ball()
        self.update_ui()

    # =========================================================================
    # ENGINE UPDATE & INPUT INTERFACES
    # =========================================================================
    def input(self, key):
        if self.destroyed:
            return

        if self.game_state == self.STATE_PLAYING:
            if key == 'p':
                self.game_state = self.STATE_PAUSED
                self.paused_text.enabled = True
                
        elif self.game_state == self.STATE_PAUSED:
            if key == 'r' or key == 'p':
                self.game_state = self.STATE_PLAYING
                self.paused_text.enabled = False

    def update(self):
        if self.destroyed:
            return

        # 1. State: Start Menu
        if self.game_state == self.STATE_START:
            self.title_text.enabled = True
            self.instruction_text.enabled = True
            self.hud_text.enabled = False
            self.paused_text.enabled = False
            
            if held_keys['space']:
                self.game_state = self.STATE_PLAYING
                self.title_text.enabled = False
                self.instruction_text.enabled = False
                self.hud_text.enabled = True
                self.reset_game()
            return

        # 2. State: Paused (Early exit out of loop)
        elif self.game_state == self.STATE_PAUSED:
            return

        # ----------------------------------------------------
        # Active Gameplay Physics Loops
        # ----------------------------------------------------
        
        # Smooth Brick introductory "Swoosh" interpolation
        for brick in self.bricks:
            if hasattr(brick, 'target_y') and brick.y < brick.target_y:
                brick.y = lerp(brick.y, brick.target_y, time.dt * 6.5)
                if brick.target_y - brick.y < 0.05:
                    brick.y = brick.target_y

        # Wide paddle power-up decay
        if self.paddle_timer > 0:
            self.paddle_timer -= time.dt
            if self.paddle_timer <= 0:
                self.paddle.scale_x = self.paddle_base_width
                self.paddle.color = color.cyan

        # Camera Shake offsets resolution
        if self.camera_shake_timer > 0:
            self.camera_shake_timer -= time.dt
            camera.x = random.uniform(-self.camera_shake_amount, self.camera_shake_amount)
            camera.y = random.uniform(-self.camera_shake_amount, self.camera_shake_amount)
            if self.camera_shake_timer <= 0:
                camera.x = 0
                camera.y = 0

        # Steering paddle actions
        move_dir = held_keys['right arrow'] - held_keys['left arrow']
        self.paddle.x += move_dir * 9.5 * time.dt
        
        limit = 5.9 - (self.paddle.scale_x / 2.0)
        self.paddle.x = clamp(self.paddle.x, -limit, limit)

        # Process falling Power-Ups
        for p in self.powerups.copy():
            if not p or not hasattr(p, 'x'):
                continue
            if (abs(p.x - self.paddle.x) < (p.scale_x/2 + self.paddle.scale_x/2) and
                abs(p.y - self.paddle.y) < (p.scale_y/2 + self.paddle.scale_y/2)):
                
                self.trigger_screen_shake(0.04, 0.06)
                
                if p.type == "multiball":
                    current_balls = self.balls.copy()
                    if len(current_balls) > 0:
                        for b in current_balls:
                            self.create_ball(position=b.position, velocity=Vec2(-b.velocity.x, b.velocity.y).normalized())
                            self.create_ball(position=b.position, velocity=Vec2(b.velocity.x * 1.2, -b.velocity.y).normalized())
                    else:
                        self.create_ball(position=(self.paddle.x, self.paddle.y + 0.5, -0.1))

                elif p.type == "wide_paddle":
                    self.paddle.scale_x = self.paddle_base_width * 1.5
                    self.paddle.color = color.magenta
                    self.paddle_timer = 10.0

                if p in self.powerups:
                    self.powerups.remove(p)
                if p in self.entities:
                    self.entities.remove(p)
                destroy(p)

        # Process balls physics & overlaps
        for ball in self.balls.copy():
            if not ball or not hasattr(ball, 'x'):
                continue

            # Render trail
            if random.random() < 0.4:
                trail = self.BallTrail(self, ball.position, ball.color)
                self.active_trails.append(trail)
                self.entities.append(trail)

            # --- Motion phase X ---
            ball.x += ball.velocity.x * ball.speed * time.dt

            # Wall bounces
            if ball.x - 0.125 < -5.9:
                ball.x = -5.9 + 0.125
                ball.velocity.x = abs(ball.velocity.x)
                self.trigger_screen_shake(0.02, 0.04)
            elif ball.x + 0.125 > 5.9:
                ball.x = 5.9 - 0.125
                ball.velocity.x = -abs(ball.velocity.x)
                self.trigger_screen_shake(0.02, 0.04)

            # --- Motion phase Y ---
            ball.y += ball.velocity.y * ball.speed * time.dt

            # Top Wall boundary bounce
            if ball.y + 0.125 > 4.9:
                ball.y = 4.9 - 0.125
                ball.velocity.y = -abs(ball.velocity.y)
                self.trigger_screen_shake(0.02, 0.04)

            # Paddle elastic deflection
            if (abs(ball.x - self.paddle.x) < (0.125 + self.paddle.scale_x / 2.0) and
                abs(ball.y - self.paddle.y) < (0.125 + self.paddle.scale_y / 2.0)):
                
                ball.y = self.paddle.y + (self.paddle.scale_y / 2.0) + 0.125
                hit_pos = (ball.x - self.paddle.x) / (self.paddle.scale_x / 2.0)
                
                ball.velocity.y = abs(ball.velocity.y)
                ball.velocity.x = hit_pos * 1.3
                ball.velocity = ball.velocity.normalized()
                
                self.trigger_screen_shake(0.03, 0.05)

            # AABB Axis Alignment Brick Overlap Checks
            for brick in self.bricks.copy():
                if not brick or not hasattr(brick, 'x'):
                    continue
                b_half_w = brick.scale_x / 2.0
                b_half_h = brick.scale_y / 2.0
                
                if abs(brick.y - brick.target_y) < 2.0:
                    if (abs(ball.x - brick.x) < (0.125 + b_half_w) and
                        abs(ball.y - brick.y) < (0.125 + b_half_h)):
                        
                        overlap_x = (0.125 + b_half_w) - abs(ball.x - brick.x)
                        overlap_y = (0.125 + b_half_h) - abs(ball.y - brick.y)
                        
                        if overlap_x < overlap_y:
                            if ball.x < brick.x:
                                ball.x -= overlap_x
                                ball.velocity.x = -abs(ball.velocity.x)
                            else:
                                ball.x += overlap_x
                                ball.velocity.x = abs(ball.velocity.x)
                        else:
                            if ball.y < brick.y:
                                ball.y -= overlap_y
                                ball.velocity.y = -abs(ball.velocity.y)
                            else:
                                ball.y += overlap_y
                                ball.velocity.y = abs(ball.velocity.y)

                        # Impact events
                        self.spawn_particles(brick.position, brick.color)
                        self.trigger_screen_shake(0.05, 0.06)

                        # Drop powerups
                        if brick.power:
                            p_up = self.PowerUp(self, brick.position, brick.power)
                            self.powerups.append(p_up)
                            self.entities.append(p_up)

                        if brick in self.bricks:
                            self.bricks.remove(brick)
                        if brick in self.entities:
                            self.entities.remove(brick)
                        destroy(brick)

                        self.score += 10
                        if self.score > self.high_score:
                            self.high_score = self.score
                        self.update_ui()
                        break

            # Lost ball clean out of bounds
            if ball.y < -5.5:
                if ball in self.balls:
                    self.balls.remove(ball)
                if ball in self.entities:
                    self.entities.remove(ball)
                destroy(ball)

        # Fallback respawn checks
        if len(self.balls) == 0:
            self.create_ball(position=(self.paddle.x, self.paddle.y + 0.5, -0.1))

        # Progression to next level on complete clear
        if len(self.bricks) == 0 and self.game_state == self.STATE_PLAYING:
            self.level += 1
            self.update_ui()
            
            for b in self.balls.copy():
                destroy(b)
            self.balls.clear()

            for p in self.powerups.copy():
                destroy(p)
            self.powerups.clear()
            
            self.create_bricks()
            self.create_ball()

    # =========================================================================
    # COMPLETE TEARDOWN INTERFACE
    # =========================================================================
    def destroy(self):
        """
        Safely clears and destroys all custom Breakout elements, cancelling active update frames
        of inner classes and restoring original camera parameters without Panda3D assertion errors.
        """
        # Set central guard flag FIRST to prevent inner classes from executing active logic mid-destruction
        self.destroyed = True
        self.game_state = self.STATE_PAUSED

        # Safely detach dynamic collections
        self.balls.clear()
        self.bricks.clear()
        self.powerups.clear()
        self.active_particles.clear()
        self.active_trails.clear()

        # Clear physical models and game entities
        for entity in self.entities.copy():
            destroy(entity)
        self.entities.clear()

        # Clear text structures
        for ui in self.ui_elements.copy():
            destroy(ui)
        self.ui_elements.clear()

        # Restore previous engine settings
        window.color = self.old_window_color
        camera.orthographic = self.old_camera_orthographic
        camera.fov = self.old_camera_fov
        camera.parent = scene
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)