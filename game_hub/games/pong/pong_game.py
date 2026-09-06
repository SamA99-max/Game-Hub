from ursina import *
import random

class PongGame:
    '''
    PongGame is a simple pong game with AI and 2 player mode. 
    It is a clone of the classic pong game, but with some added features. 
    The AI can be set to different difficulty levels, and the game can be paused and resumed. 
    The game also has a menu system for selecting the game mode and difficulty level.
    And also able to handle 2 player mode.
    '''
    def __init__(self):
        # -------------------------
        # ASSETS & CLEANUP TRACKING
        # -------------------------
        self.entities = []
        self.ui_elements = []

        # Save previous engine camera and window settings to restore later
        self.old_window_color = window.color
        self.old_camera_orthographic = camera.orthographic
        self.old_camera_fov = camera.fov

        # Set Pong-specific camera/window layouts
        window.color = color.black
        camera.orthographic = True
        camera.fov = 1.1
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)

        # -------------------------
        # GAME STATES & SCORE
        # -------------------------
        self.two_player = False
        self.left_score = 0
        self.right_score = 0
        self.max_score = 5
        self.game_paused = False
        self.wanna_hit = 70
        self.menu = True
        self.choosing_difficulty = False
        self.collision_cooldown = .15

        # -------------------------
        # PADDLES
        # -------------------------
        self.left_paddle = Entity(
            scale=(1/32, 6/32),
            x=-.75,
            model='quad',
            origin_x=.5,
            collider='box'
        )
        self.entities.append(self.left_paddle)

        self.right_paddle = duplicate(
            self.left_paddle,
            x=.75,
            rotation_z=180
        )
        self.entities.append(self.right_paddle)

        # AI tracking attributes
        self.left_paddle_target_y = 0
        self.left_paddle_ai_timer = 0

        # -------------------------
        # WALLS
        # -------------------------
        self.floor = Entity(
            model='quad',
            y=-.5,
            origin_y=.5,
            collider='box',
            scale=(2, 10),
            visible=True,
            color=color.rgba(0, 0, 255, 0.05)
        )
        self.entities.append(self.floor)

        self.ceiling = duplicate(self.floor, y=.5, rotation_z=180, visible=True)
        self.entities.append(self.ceiling)

        self.left_wall = duplicate(self.floor, x=-.5 * window.aspect_ratio, rotation_z=90, visible=True)
        self.entities.append(self.left_wall)

        self.right_wall = duplicate(self.floor, x=.5 * window.aspect_ratio, rotation_z=-90, visible=True)
        self.entities.append(self.right_wall)

        # -------------------------
        # BALL
        # -------------------------
        self.ball = Entity(
            model='circle',
            scale=.05,
            collider='box',
            speed=10,
            rotation_z=random.choice([0, 180]),
            collision_cooldown=self.collision_cooldown
        )
        self.entities.append(self.ball)

        # Attach custom dynamic attributes to match original game code
        self.ball_last_x = self.ball.x
        self.ball_ai_will_hit = True

        # -------------------------
        # USER INTERFACE
        # -------------------------
        self.score_text = Text(
            text=f"{self.left_score} : {self.right_score}",
            position=(0, .45),
            scale=2,
            origin=(0, 0),
            visible=False # Hidden during main menu
        )
        self.ui_elements.append(self.score_text)

        self.menu_text = Text(
            text="PONG\n\n1 - One Player\n2 - Two Player",
            origin=(0, 0),
            scale=2
        )
        self.ui_elements.append(self.menu_text)

    # =========================================================================
    # CORE ENGINE INTERFACE (UPDATE LOOP)
    # =========================================================================
    def update(self):
        if self.menu or self.game_paused:
            return

        # Advance ball step
        self.ball.collision_cooldown -= time.dt
        self.ball.position += self.ball.right * self.ball.speed * time.dt

        # -------------------------
        # LEFT PADDLE CONTROLLER (P1 OR AI)
        # -------------------------
        if self.two_player:
            # Player 1 manual input
            self.left_paddle.y += (
                held_keys['w'] -
                held_keys['s']
            ) * time.dt
        else:
            # Smooth AI Prediction
            ball_dx = self.ball.x - self.ball_last_x
            self.ball_last_x = self.ball.x

            self.left_paddle_ai_timer -= time.dt

            if self.left_paddle_ai_timer <= 0:
                # Human-like AI Reaction Latency
                self.left_paddle_ai_timer = random.uniform(.05, .10)

                if ball_dx < 0:
                    # Ball is traveling towards the AI paddle
                    distance_to_paddle = abs(self.ball.x - self.left_paddle.x)
                    prediction = self.ball.y + ball_dx * distance_to_paddle * 2

                    if self.ball_ai_will_hit:
                        prediction += random.uniform(-.02, .02)
                        self.left_paddle_target_y = prediction
                    else:
                        self.left_paddle_target_y = -.45 if self.ball.y > 0 else .45
                else:
                    # Return to center and hover gracefully
                    self.left_paddle_target_y = random.uniform(-.03, .03)

            # Clamp AI Target Position to paddle bounds
            self.left_paddle_target_y = clamp(self.left_paddle_target_y, -.45, .45)

            # Lerp towards targeted position
            smooth_ratio = 6 * time.dt
            desired_pos = lerp(self.left_paddle.y, self.left_paddle_target_y, smooth_ratio)

            # Enforce max AI movement speed
            max_ai_speed = 2.8 * time.dt
            self.left_paddle.y += clamp(desired_pos - self.left_paddle.y, -max_ai_speed, max_ai_speed)

        # -------------------------
        # RIGHT PADDLE CONTROLLER
        # -------------------------
        self.right_paddle.y += (
            held_keys['up arrow'] -
            held_keys['down arrow']
        ) * time.dt

        # Hard boundaries for both paddles
        limit = .45
        self.left_paddle.y = clamp(self.left_paddle.y, -limit, limit)
        self.right_paddle.y = clamp(self.right_paddle.y, -limit, limit)

        # -------------------------
        # BALL COLLISION MECHANICS
        # -------------------------
        if self.ball.collision_cooldown <= 0:
            hit_info = self.ball.intersects()

            if hit_info.hit:
                self.ball.collision_cooldown = self.collision_cooldown

                # Paddle bounces
                if hit_info.entity in (self.left_paddle, self.right_paddle):
                    bounce_dir = -1 if hit_info.entity == self.left_paddle else 1

                    self.ball.rotation_z += 180 * bounce_dir
                    self.ball.rotation_z -= (
                        (hit_info.entity.world_y - self.ball.y)
                        * 20 * 32 * bounce_dir
                    )
                    # Speed up on successful hit rallies
                    self.ball.speed *= 1.08

                    # Decide if AI will fail this rally (difficulty RNG check)
                    if hit_info.entity == self.right_paddle:
                        self.ball_ai_will_hit = random.randint(1, 100) <= self.wanna_hit

                # Goal Detection
                elif hit_info.entity == self.right_wall:
                    self.left_score += 1
                    self.update_score()
                    return

                elif hit_info.entity == self.left_wall:
                    self.right_score += 1
                    self.update_score()
                    return

                # Spawn collision impact particle
                self.spawn_hit_particle(hit_info.world_point)

        # Ceiling & floor bounces
        if (
            self.ball.y > self.ceiling.y - self.ball.scale_y / 2 or
            self.ball.y < self.floor.y + self.ball.scale_y / 2
        ):
            self.ball.rotation_z = -self.ball.rotation_z

    # =========================================================================
    # PARTICLE ANIMATION HELPER
    # =========================================================================
    def spawn_hit_particle(self, hit_point):
        particle = Entity(
            model='quad',
            position=hit_point,
            scale=0,
            texture='circle',
            add_to_scene_entities=False
        )
        self.entities.append(particle)

        particle.animate_scale(.2, .5, curve=curve.out_expo)
        particle.animate_color(color.clear, duration=.5, curve=curve.out_expo)
        destroy(particle, delay=.5)
        # Setup scheduled list cleaning of dead particles
        invoke(lambda: self.entities.remove(particle) if particle in self.entities else None, delay=.5)

    # =========================================================================
    # CORE GAME LOGIC METHODS
    # =========================================================================
    def update_score(self):
        self.score_text.text = f"{self.left_score} : {self.right_score}"

        if self.left_score >= self.max_score or self.right_score >= self.max_score:
            winner = "Left" if self.left_score >= self.max_score else "Right"
            winner_text = Text(
                f"{winner} Player Wins!",
                scale=2,
                origin=(0, 0)
            )
            self.ui_elements.append(winner_text)

            self.ball.speed = 0
            self.game_paused = True

            # Clear winner text and close/reset game after brief pause
            invoke(destroy, winner_text, delay=3)
            invoke(lambda: self.ui_elements.remove(winner_text) if winner_text in self.ui_elements else None, delay=3)
        else:
            self.reset()

    def reset(self):
        self.ball.position = (0, 0, 0)
        self.ball.rotation = (0, 0, 0)
        self.ball.rotation_z = random.choice([0, 180])
        self.ball.speed = 10
        self.ball.collision_cooldown = self.collision_cooldown

        self.left_paddle.y = 0
        self.right_paddle.y = 0

        self.left_paddle_target_y = 0
        self.left_paddle_ai_timer = 0
        self.ball_ai_will_hit = True
        self.ball_last_x = self.ball.x

    # =========================================================================
    # INPUT INTERFACE
    # =========================================================================
    def input(self, key):
        if self.menu:
            if not self.choosing_difficulty:
                if key == '1':
                    self.two_player = False
                    self.choosing_difficulty = True
                    self.menu_text.text = (
                        "Difficulty\n\n"
                        "1 - Easy (20%)\n"
                        "2 - Medium (40%)\n"
                        "3 - Hard (60%)\n"
                        "4 - Extreme (80%)\n"
                        "5 - Infinite (100%)"
                    )
                    return

                elif key == '2':
                    self.two_player = True
                    self.menu = False
                    self.score_text.visible = True
                    destroy(self.menu_text)
                    if self.menu_text in self.ui_elements:
                        self.ui_elements.remove(self.menu_text)
                    self.reset()
                    return
            else:
                difficulties = {
                    '1': 20,
                    '2': 40,
                    '3': 60,
                    '4': 80,
                    '5': 100
                }
                if key in difficulties:
                    self.wanna_hit = difficulties[key]
                    self.menu = False
                    self.choosing_difficulty = False
                    self.score_text.visible = True
                    destroy(self.menu_text)
                    if self.menu_text in self.ui_elements:
                        self.ui_elements.remove(self.menu_text)
                    self.reset()
                    return

        # Pause & Resume controls
        if key == 'p':
            self.game_paused = True
            print("game_paused")
        elif key == 'r':
            self.game_paused = False
            print("game_resume")

    # =========================================================================
    # ENGINE DESTROY INTERFACE (CLEAN SHUTDOWN)
    # =========================================================================
    def destroy(self):
        """
        Cleans up active UI, entities, resets window color to default,
        and cleanly restores core engine perspective.
        """
        self.game_paused = True

        # Clear registered game objects
        for entity in self.entities.copy():
            destroy(entity)
        self.entities.clear()

        # Clear UI components
        for ui in self.ui_elements.copy():
            destroy(ui)
        self.ui_elements.clear()

        # Restore engine defaults
        window.color = self.old_window_color
        camera.orthographic = self.old_camera_orthographic
        camera.fov = self.old_camera_fov
        camera.parent = scene
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)