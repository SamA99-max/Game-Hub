from ursina import *
import random
import math

class PacmanGame:
    """
    PacmanGame class designed for a modular mini-game engine.
    Encapsulates grid physics, ghost AI target routines, chomping animations,
    particle bursts, and dynamic scoreboard overlays under a fully clean lifecycle.
    """
    
    # Classic Pac-Man maze layout
    # '#' = Wall, '.' = Pellet, 'o' = Power Pellet, ' ' = Empty, '-' = Ghost Gate
    MAZE = [
        "############################",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#o####.#####.##.#####.####o#",
        "#.####.#####.##.#####.####.#",
        "#..........................#",
        "#.####.##.########.##.####.#",
        "#.####.##.########.##.####.#",
        "#......##....##....##......#",
        "######.##### ## #####.######",
        "     #.##### ## #####.#     ",
        "     #.##    -     ##.#     ",
        "     #.## ######## ##.#     ",
        "######.## #      # ##.######",
        "      .   #      #   .      ",
        "######.## #      # ##.######",
        "     #.## ######## ##.#     ",
        "     #.##          ##.#     ",
        "     #.## ######## ##.#     ",
        "######.## ######## ##.######",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#.####.#####.##.#####.####.#",
        "#o..##................##..o#",
        "###.##.##.########.##.##.###",
        "###.##.##.########.##.##.###",
        "#......##....##....##......#",
        "#.##########.##.##########.#",
        "#.##########.##.##########.#",
        "#..........................#",
        "############################"
    ]

    GRID_WIDTH = len(MAZE[0])
    GRID_HEIGHT = len(MAZE)

    # =========================================================================
    # NEON RETRO PARTICLE EFFECT
    # =========================================================================
    class RetroParticle(Entity):
        def __init__(self, game, position, target_color):
            self.game = game
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 7)
            super().__init__(
                model='quad',
                color=target_color,
                scale=random.uniform(0.1, 0.2),
                position=position + Vec3(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), -0.1)
            )
            self.dx = math.cos(angle) * speed
            self.dy = math.sin(angle) * speed
            self.life = random.uniform(0.3, 0.6)

        def update(self):
            if self.game.destroyed:
                return
            self.position += Vec3(self.dx * time.dt, self.dy * time.dt, 0)
            self.dx *= 0.92
            self.dy *= 0.92
            self.scale_x -= time.dt * 0.2
            self.scale_y -= time.dt * 0.2
            self.life -= time.dt
            if self.life <= 0 or self.scale_x <= 0:
                if self in self.game.effects:
                    self.game.effects.remove(self)
                destroy(self)

    # =========================================================================
    # FLOATING POPUP TEXT
    # =========================================================================
    class FloatingText(Entity):
        def __init__(self, game, val, position, txt_color=color.yellow):
            self.game = game
            super().__init__(
                position=position + Vec3(0, 0.5, -0.2)
            )
            self.label = Text(
                text=str(val),
                parent=self,
                color=txt_color,
                scale=1.5,
                origin=(0, 0)
            )
            self.life = 0.8

        def update(self):
            if self.game.destroyed:
                return
            self.y += time.dt * 1.5
            self.life -= time.dt
            self.label.color = color.color(self.label.color.h, self.label.color.s, self.label.color.v, self.life / 0.8)
            if self.life <= 0:
                destroy(self.label)
                if self in self.game.effects:
                    self.game.effects.remove(self)
                destroy(self)

    # =========================================================================
    # GRID ENTITY BASE
    # =========================================================================
    class GridEntity(Entity):
        def __init__(self, game, start_col, start_row, model='circle', color=color.white, scale=0.8):
            self.game = game
            self.grid_x = start_col
            self.grid_y = start_row
            self.target_x = start_col
            self.target_y = start_row
            self.move_progress = 0.0
            self.speed = 5.0
            self.dir_x = 0
            self.dir_y = 0

            super().__init__(
                model=model,
                color=color,
                scale=scale,
                position=game.grid_to_world(start_col, start_row)
            )

        def advance_movement(self):
            if self.game.destroyed:
                return

            self.move_progress += time.dt * self.speed
            while self.move_progress >= 1.0:
                self.move_progress -= 1.0
                self.grid_x = self.target_x
                self.grid_y = self.target_y
                
                # Screen wrap-around tunnels
                if self.grid_x < 0:
                    self.grid_x = self.game.GRID_WIDTH - 1
                elif self.grid_x >= self.game.GRID_WIDTH:
                    self.grid_x = 0
                    
                self.target_x = self.grid_x
                self.target_y = self.grid_y
                self.decide_next_step()

            p1 = self.game.grid_to_world(self.grid_x, self.grid_y)
            p2 = self.game.grid_to_world(self.target_x, self.target_y)
            
            if abs(self.target_x - self.grid_x) > 1:
                self.position = p1 if self.move_progress < 0.5 else p2
            else:
                self.position = lerp(p1, p2, self.move_progress)

        def decide_next_step(self):
            pass

    # =========================================================================
    # PACMAN CHARACTER CONTROLLER
    # =========================================================================
    class Pacman(GridEntity):
        def __init__(self, game, col, row):
            super().__init__(game, col, row, model='circle', color=color.yellow, scale=0.85)
            self.next_dir_x = 0
            self.next_dir_y = 0
            self.speed = 6.0
            
            # Interactive bites mouth wedge shape
            self.mouth = Entity(
                parent=self,
                model='quad',
                color=color.black,
                scale=(0.55, 0.55),
                position=(0.25, 0, -0.01),
                rotation_z=45
            )
            self.mouth_timer = 0.0
            self.base_scale = 0.85

        def update(self):
            if self.game.destroyed or self.game.game_over or self.game.won:
                return

            # Mouth rotation animation
            self.mouth_timer += time.dt * 18
            self.mouth.scale = Vec2(0.55, abs(math.sin(self.mouth_timer)) * 0.55)

            # Stretch along movement axis
            if self.dir_x != 0 or self.dir_y != 0:
                pulse = math.sin(self.mouth_timer) * 0.08
                if self.dir_x != 0:
                    self.scale = Vec3(self.base_scale + pulse, self.base_scale - pulse, self.base_scale)
                else:
                    self.scale = Vec3(self.base_scale - pulse, self.base_scale + pulse, self.base_scale)
            else:
                self.scale = Vec3(self.base_scale, self.base_scale, self.base_scale)

            # Continuous steer buffering inputs
            if held_keys['left arrow'] or held_keys['a']:
                self.next_dir_x, self.next_dir_y = -1, 0
            elif held_keys['right arrow'] or held_keys['d']:
                self.next_dir_x, self.next_dir_y = 1, 0
            elif held_keys['up arrow'] or held_keys['w']:
                self.next_dir_x, self.next_dir_y = 0, -1
            elif held_keys['down arrow'] or held_keys['s']:
                self.next_dir_x, self.next_dir_y = 0, 1

            self.advance_movement()
            self.check_collisions()

        def decide_next_step(self):
            if self.game.is_walkable(self.grid_x + self.next_dir_x, self.grid_y + self.next_dir_y):
                self.dir_x, self.dir_y = self.next_dir_x, self.next_dir_y
                if self.dir_x == 1: self.rotation_z = 0
                elif self.dir_x == -1: self.rotation_z = 180
                elif self.dir_y == 1: self.rotation_z = 270
                elif self.dir_y == -1: self.rotation_z = 90
                
            if self.game.is_walkable(self.grid_x + self.dir_x, self.grid_y + self.dir_y):
                self.target_x = self.grid_x + self.dir_x
                self.target_y = self.grid_y + self.dir_y
            else:
                self.dir_x, self.dir_y = 0, 0

        def check_collisions(self):
            # Regular pellets eat
            for pellet in self.game.pellets[:]:
                if pellet.enabled and pellet.grid_x == self.grid_x and pellet.grid_y == self.grid_y:
                    pellet.disable()
                    self.game.score += 10
                    self.game.pellets_left -= 1
                    self.game.pellets_eaten_total += 1
                    self.game.spawn_burst(self.position, color.yellow, count=4)
                    self.game.check_fruit_spawn()
                    self.game.update_ui()
                    
            # Pulsing Power pellets eat
            for p_pellet in self.game.power_pellets[:]:
                if p_pellet.enabled and p_pellet.grid_x == self.grid_x and p_pellet.grid_y == self.grid_y:
                    p_pellet.disable()
                    self.game.score += 50
                    self.game.spawn_burst(self.position, color.white, count=12)
                    self.game.spawn_popup("+50", self.position, color.white)
                    
                    self.game.frightened_timer = 9.0
                    self.game.ghost_mode = "FRIGHTENED"
                    for g in self.game.ghosts:
                        if not g.is_dead:
                            g.set_frightened(True)
                    self.game.update_ui()

            # Cherry bonus pop-ups eat
            if self.game.active_fruit and self.game.active_fruit.enabled:
                dist_to_fruit = math.hypot(self.x - self.game.active_fruit.x, self.y - self.game.active_fruit.y)
                if dist_to_fruit < 0.7:
                    self.game.active_fruit.disable()
                    self.game.score += 500
                    self.game.spawn_burst(self.game.active_fruit.position, color.red, count=15)
                    self.game.spawn_popup("+500 Cherry!", self.game.active_fruit.position, color.red)
                    self.game.active_fruit = None
                    self.game.update_ui()

            if self.game.pellets_left <= 0 and not self.game.won:
                self.game.won = True
                self.game.status_text.text = "VICTORY!\nPress R to Restart"
                self.game.status_text.color = color.green
                self.game.status_text.enabled = True

    # =========================================================================
    # GHOST ENEMY SYSTEM
    # =========================================================================
    class Ghost(GridEntity):
        def __init__(self, game, col, row, ghost_color, scatter_target, name):
            super().__init__(game, col, row, model='circle', color=ghost_color, scale=0.85)
            self.original_color = ghost_color
            self.scatter_target = scatter_target
            self.name = name
            self.is_frightened = False
            self.is_dead = False
            self.speed = 4.0
            
            # Pupiled visual eyes setup
            self.eye_left = Entity(parent=self, model='circle', color=color.white, scale=0.25, position=(-0.2, 0.1, -0.01))
            self.eye_right = Entity(parent=self, model='circle', color=color.white, scale=0.25, position=(0.2, 0.1, -0.01))
            self.pupil_left = Entity(parent=self.eye_left, model='circle', color=color.blue, scale=0.4, position=(0, 0, -0.01))
            self.pupil_right = Entity(parent=self.eye_right, model='circle', color=color.blue, scale=0.4, position=(0, 0, -0.01))

            # Animated procedural wiggler skirt
            self.skirt_legs = []
            for i in range(3):
                leg = Entity(
                    parent=self,
                    model='quad',
                    color=self.color,
                    scale=(0.25, 0.3),
                    position=(-0.25 + (i * 0.25), -0.3, 0.01)
                )
                self.skirt_legs.append(leg)
                
            self.anim_timer = random.uniform(0, 10.0)

        def set_frightened(self, value):
            self.is_frightened = value
            target_col = color.blue if value else self.original_color
            self.color = target_col
            for leg in self.skirt_legs:
                leg.color = target_col
                
            if value:
                self.speed = 2.5
                self.pupil_left.color = color.orange
                self.pupil_right.color = color.orange
            else:
                self.speed = 4.0
                self.pupil_left.color = color.blue
                self.pupil_right.color = color.blue

        def reset_ghost(self, start_col, start_row):
            self.grid_x = start_col
            self.grid_y = start_row
            self.target_x = start_col
            self.target_y = start_row
            self.move_progress = 0.0
            self.dir_x = 0
            self.dir_y = -1
            self.is_dead = False
            self.set_frightened(False)
            self.position = self.game.grid_to_world(start_col, start_row)

        def get_target(self):
            if self.is_dead: 
                return Vec2(13, 11)  # Base entryway coords
            
            if self.game.ghost_mode == "SCATTER":
                return self.scatter_target
            else:
                return self.get_chase_target()

        def get_chase_target(self):
            return Vec2(self.game.pacman.grid_x, self.game.pacman.grid_y)

        def update(self):
            if self.game.destroyed or self.game.game_over or self.game.won:
                return

            self.anim_timer += time.dt * 15
            for idx, leg in enumerate(self.skirt_legs):
                leg.y = -0.3 + (math.sin(self.anim_timer + (idx * 1.5)) * 0.08)

            eye_offset = Vec2(self.dir_x * 0.1, self.dir_y * 0.1)
            self.pupil_left.position = eye_offset
            self.pupil_right.position = eye_offset

            self.advance_movement()
            self.check_pacman_collision()

        def decide_next_step(self):
            possible_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            next_moves = []
            
            allow_gate = self.is_dead or (self.grid_y >= 11 and self.grid_y <= 13 and self.grid_x >= 11 and self.grid_x <= 16)

            if self.is_frightened:
                for dx, dy in possible_dirs:
                    if dx == -self.dir_x and dy == -self.dir_y:
                        continue
                    if self.game.is_walkable(self.grid_x + dx, self.grid_y + dy, allow_gate=allow_gate):
                        next_moves.append((dx, dy))
                
                if next_moves:
                    self.dir_x, self.dir_y = random.choice(next_moves)
                else:
                    self.dir_x, self.dir_y = -self.dir_x, -self.dir_y
            else:
                target = self.get_target()
                best_dir = None
                best_dist = float('inf')
                
                for dx, dy in possible_dirs:
                    if dx == -self.dir_x and dy == -self.dir_y:
                        continue
                    
                    next_col = self.grid_x + dx
                    next_row = self.grid_y + dy
                    
                    if self.game.is_walkable(next_col, next_row, allow_gate=allow_gate):
                        dist = math.hypot(next_col - target.x, next_row - target.y)
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = (dx, dy)
                
                if best_dir:
                    self.dir_x, self.dir_y = best_dir
                else:
                    self.dir_x, self.dir_y = -self.dir_x, -self.dir_y

            self.target_x = self.grid_x + self.dir_x
            self.target_y = self.grid_y + self.dir_y

        def check_pacman_collision(self):
            if not self.game.pacman or self.game.destroyed:
                return
            if math.hypot(self.x - self.game.pacman.x, self.y - self.game.pacman.y) < 0.65:
                if self.is_frightened:
                    self.is_dead = True
                    self.is_frightened = False
                    
                    self.color = color.clear
                    for leg in self.skirt_legs:
                        leg.color = color.clear
                        
                    self.speed = 8.5
                    
                    ghost_score = 200
                    self.game.score += ghost_score
                    
                    self.game.spawn_burst(self.position, self.original_color, count=25)
                    self.game.spawn_popup(f"+{ghost_score}", self.position, self.original_color)
                    self.game.shake_timer = 0.15
                    
                    self.game.update_ui()
                elif not self.is_dead:
                    self.game.handle_pacman_death()

    # =========================================================================
    # DETAILED INDIVIDUAL GHOST PERSONALITIES
    # =========================================================================
    class Blinky(Ghost):
        def get_chase_target(self):
            return Vec2(self.game.pacman.grid_x, self.game.pacman.grid_y)

    class Pinky(Ghost):
        def get_chase_target(self):
            px = self.game.pacman.grid_x + (self.game.pacman.dir_x * 4)
            py = self.game.pacman.grid_y + (self.game.pacman.dir_y * 4)
            return Vec2(px, py)

    class Inky(Ghost):
        def get_chase_target(self):
            px = self.game.pacman.grid_x + (self.game.pacman.dir_x * 2)
            py = self.game.pacman.grid_y + (self.game.pacman.dir_y * 2)
            if len(self.game.ghosts) > 0:
                blinky = self.game.ghosts[0]
                dx = px - blinky.grid_x
                dy = py - blinky.grid_y
                return Vec2(px + dx, py + dy)
            return Vec2(px, py)

    class Clyde(Ghost):
        def get_chase_target(self):
            dist = math.hypot(self.grid_x - self.game.pacman.grid_x, self.grid_y - self.game.pacman.grid_y)
            if dist > 8:
                return Vec2(self.game.pacman.grid_x, self.game.pacman.grid_y)
            else:
                return self.scatter_target

    # =========================================================================
    # PULSING BONUS FRUIT CHERRY
    # =========================================================================
    class Fruit(Entity):
        def __init__(self, game, col, row):
            self.game = game
            super().__init__(
                position=game.grid_to_world(col, row),
                scale=0.8
            )
            self.c1 = Entity(parent=self, model='circle', color=color.red, scale=0.45, position=(-0.15, -0.1, -0.05))
            self.c2 = Entity(parent=self, model='circle', color=color.red, scale=0.45, position=(0.15, -0.2, -0.05))
            self.stem = Entity(parent=self, model='quad', color=color.green, scale=(0.1, 0.5), position=(0, 0.15, 0), rotation_z=-20)
            self.scale_pulse = 0.0

        def update(self):
            if self.game.destroyed:
                return
            self.scale_pulse += time.dt * 6
            cur_scale = 0.8 + (math.sin(self.scale_pulse) * 0.1)
            self.scale = Vec3(cur_scale, cur_scale, 1)

    # =========================================================================
    # CORE PACMAN ENGINE SYSTEM INITIALIZATION
    # =========================================================================
    def __init__(self):
        self.destroyed = False

        # Save previous window configuration
        self.old_window_color = window.color
        self.old_camera_orthographic = camera.orthographic
        self.old_camera_fov = camera.fov
        self.old_camera_position = camera.position
        self.old_camera_rotation = camera.rotation

        # Retro layout camera adjustments
        window.color = color.black
        camera.orthographic = True
        camera.fov = 34
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)

        # Dynamic entities trackers lists
        self.entities = []
        self.ui_elements = []
        self.effects = []
        self.walls = []
        self.pellets = []
        self.power_pellets = []
        self.ghosts = []

        # UI structures
        self.score_text = None
        self.high_score_text = None
        self.lives_text = None
        self.status_text = None
        self.mode_text = None
        self.gate_entity = None
        self.active_fruit = None
        self.pacman = None

        # Pulsing trackers variables
        self.wall_pulse_timer = 0.0

        # High score persist initialization
        self.high_score = 0

        self.start_game()

    # =========================================================================
    # GRID COORD CONVERTER AND PATH VALIDATOR
    # =========================================================================
    def grid_to_world(self, col, row):
        x = col - (self.GRID_WIDTH / 2) + 0.5
        y = (self.GRID_HEIGHT / 2) - row - 0.5
        return Vec3(x, y, 0)

    def is_walkable(self, col, row, allow_gate=False):
        if col < 0 or col >= self.GRID_WIDTH:
            return True
        if row < 0 or row >= self.GRID_HEIGHT:
            return False
        
        tile = self.MAZE[row][col]
        if tile == '#':
            return False
        if tile == '-' and not allow_gate:
            return False
        return True

    # =========================================================================
    # PARTICLES AND POPUPS GENERATORS
    # =========================================================================
    def spawn_burst(self, pos, target_color, count=8):
        if self.destroyed:
            return
        for _ in range(count):
            p = self.RetroParticle(self, pos, target_color)
            self.effects.append(p)
            self.entities.append(p)

    def spawn_popup(self, val, pos, txt_color=color.yellow):
        if self.destroyed:
            return
        p = self.FloatingText(self, val, pos, txt_color)
        self.effects.append(p)
        self.entities.append(p)

    def check_fruit_spawn(self):
        if not self.fruit_spawned and (self.pellets_eaten_total == 50 or self.pellets_eaten_total == 150):
            if self.active_fruit:
                if self.active_fruit in self.entities:
                    self.entities.remove(self.active_fruit)
                destroy(self.active_fruit)
                
            self.active_fruit = self.Fruit(self, 13, 17)
            self.entities.append(self.active_fruit)
            self.spawn_burst(self.grid_to_world(13, 17), color.red, count=15)
            self.spawn_popup("CHERRY BONUS!", self.grid_to_world(13, 17), color.red)

    # =========================================================================
    # PLAYER LIVES LOSS AND GAME RESETS
    # =========================================================================
    def handle_pacman_death(self):
        if self.destroyed:
            return
        self.lives -= 1
        self.shake_timer = 0.5
        
        self.spawn_burst(self.pacman.position, color.red, count=35)
        self.spawn_popup("Ouch!", self.pacman.position, color.red)
        
        self.update_ui()
        if self.lives <= 0:
            self.game_over = True
            self.status_text.text = "GAME OVER\nPress R to Restart"
            self.status_text.color = color.red
            self.status_text.enabled = True
        else:
            # Re-spawn positions on life loss
            self.pacman.grid_x = 13
            self.pacman.grid_y = 23
            self.pacman.target_x = 13
            self.pacman.target_y = 23
            self.pacman.move_progress = 0.0
            self.pacman.dir_x = 0
            self.pacman.dir_y = 0
            self.pacman.position = self.grid_to_world(13, 23)
            
            # Re-spawn ghosts back inside baseline gates
            start_positions = [(13, 11), (14, 11), (13, 12), (14, 12)]
            for i, g in enumerate(self.ghosts):
                col, row = start_positions[i]
                g.reset_ghost(col, row)

    # =========================================================================
    # THE MAP CONSTRUCT AND ENTITY SPAWNERS
    # =========================================================================
    def create_map(self):
        for w in self.walls:
            destroy(w)
        self.walls.clear()

        if self.gate_entity:
            destroy(self.gate_entity)
            self.gate_entity = None
        if self.active_fruit:
            destroy(self.active_fruit)
            self.active_fruit = None

        for p in self.pellets:
            destroy(p)
        for p in self.power_pellets:
            destroy(p)
            
        self.pellets.clear()
        self.power_pellets.clear()
        self.pellets_left = 0
        self.pellets_eaten_total = 0
        self.fruit_spawned = False

        for row in range(self.GRID_HEIGHT):
            for col in range(self.GRID_WIDTH):
                tile = self.MAZE[row][col]
                pos = self.grid_to_world(col, row)
                
                if tile == '#':
                    blue_wall = Entity(
                        model='quad',
                        color=color.blue,
                        scale=0.92,
                        position=pos,
                        z=0.1
                    )
                    black_inner = Entity(
                        model='quad',
                        color=color.black,
                        scale=0.72,
                        position=pos + Vec3(0, 0, -0.01),
                        z=-5
                    )
                    self.walls.append(blue_wall)
                    self.walls.append(black_inner)
                    self.entities.extend([blue_wall, black_inner])
                    
                elif tile == '-':
                    self.gate_entity = Entity(
                        model='quad',
                        color=color.pink,
                        scale=(0.9, 0.2),
                        position=pos,
                        z=0.1
                    )
                    self.entities.append(self.gate_entity)
                elif tile == '.':
                    pellet = Entity(
                        model='circle',
                        color=color.yellow,
                        scale=0.15,
                        position=pos
                    )
                    pellet.grid_x = col
                    pellet.grid_y = row
                    self.pellets.append(pellet)
                    self.entities.append(pellet)
                    self.pellets_left += 1
                elif tile == 'o':
                    p_pellet = Entity(
                        model='circle',
                        color=color.yellow,
                        scale=0.35,
                        position=pos
                    )
                    p_pellet.grid_x = col
                    p_pellet.grid_y = row
                    self.power_pellets.append(p_pellet)
                    self.entities.append(p_pellet)
                    self.pellets_left += 1

    def spawn_entities(self):
        if self.pacman:
            destroy(self.pacman)
        for g in self.ghosts:
            destroy(g)
        self.ghosts.clear()

        # Pacman starts on center bottom row
        self.pacman = self.Pacman(self, 13, 23)
        self.entities.append(self.pacman)

        # Build Ghost instances
        blinky = self.Blinky(self, 13, 11, color.red, Vec2(self.GRID_WIDTH, -3), "Blinky")
        pinky = self.Pinky(self, 14, 11, color.pink, Vec2(-2, -3), "Pinky")
        inky = self.Inky(self, 13, 12, color.cyan, Vec2(self.GRID_WIDTH, self.GRID_HEIGHT + 2), "Inky")
        clyde = self.Clyde(self, 14, 12, color.orange, Vec2(-2, self.GRID_HEIGHT + 2), "Clyde")

        self.ghosts = [blinky, pinky, inky, clyde]
        self.entities.extend(self.ghosts)

    # =========================================================================
    # USER INTERFACE RENDERS & DATA BINDINGS
    # =========================================================================
    def build_ui(self):
        for ui in self.ui_elements:
            destroy(ui)
        self.ui_elements.clear()

        self.score_text = Text(
            text="SCORE\n000000",
            position=(-0.65, 0.45),
            scale=2,
            color=color.yellow,
        )
        self.ui_elements.append(self.score_text)

        self.high_score_text = Text(
            text="HIGH SCORE\n000000",
            position=(-0.15, 0.45),
            scale=2,
            color=color.red,
        )
        self.ui_elements.append(self.high_score_text)
        
        self.lives_text = Text(
            text="LIVES\nO O O",
            position=(0.4, 0.45),
            scale=2,
            color=color.green,
        )
        self.ui_elements.append(self.lives_text)

        self.mode_text = Text(
            text="MODE: SCATTER",
            position=(-0.65, -0.42),
            scale=1.5,
            color=color.green,
        )
        self.ui_elements.append(self.mode_text)
        
        self.status_text = Text(
            text="",
            position=(0, 0.05),
            origin=(0, 0),
            scale=3.5,
            color=color.yellow,
            enabled=False,
        )
        self.ui_elements.append(self.status_text)

    def update_ui(self):
        if self.destroyed:
            return
        if self.score > self.high_score:
            self.high_score = self.score
            
        self.score_text.text = f"SCORE\n{self.score:06d}"
        self.high_score_text.text = f"HIGH SCORE\n{self.high_score:06d}"
        self.lives_text.text = f"LIVES\n{'O ' * self.lives}"
        self.mode_text.text = f"MODE: {self.ghost_mode}"
        
        if self.ghost_mode == "CHASE":
            self.mode_text.color = color.red
        elif self.ghost_mode == "SCATTER":
            self.mode_text.color = color.green
        else:
            self.mode_text.color = color.cyan

    def start_game(self):
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.won = False
        self.frightened_timer = 0.0
        self.ghost_mode = "SCATTER"
        self.mode_timer = 7.0
        self.mode_cycle_count = 0
        self.shake_timer = 0.0
        self.fruit_spawned = False
        
        self.create_map()
        self.spawn_entities()
        self.build_ui()
        self.update_ui()

    # =========================================================================
    # GLOBAL TIMERS & INTERACTIVE UPDATE PHASES
    # =========================================================================
    def update(self):
        if self.destroyed:
            return

        # Pulsing outline walls color effects
        self.wall_pulse_timer += time.dt * 4
        pulsing_color = color.rgb(0, 0, 180 + int(abs(math.sin(self.wall_pulse_timer)) * 75))
        for idx, w in enumerate(self.walls):
            if idx % 2 == 0:  # Pulsing the outer glowing segment
                w.color = pulsing_color

        # Pulsing active Power Pellets scale size
        for p_pellet in self.power_pellets:
            if p_pellet.enabled:
                scale_pulse = 0.35 + (math.sin(self.wall_pulse_timer * 2) * 0.1)
                p_pellet.scale = Vec3(scale_pulse, scale_pulse, 1)

        # Cam Shake
        if self.shake_timer > 0:
            self.shake_timer -= time.dt
            camera.x = random.uniform(-0.15, 0.15)
            camera.y = random.uniform(-0.15, 0.15)
            if self.shake_timer <= 0:
                camera.x = 0
                camera.y = 0

        # Halt loops during Gameover / Victory states
        if self.game_over or self.won:
            return

        # Scared ghosts cycles timings
        if self.frightened_timer > 0:
            self.frightened_timer -= time.dt
            
            # Flash white warning color before powerup decay
            if self.frightened_timer < 3.0:
                flash_on = int(self.frightened_timer * 8) % 2 == 0
                for g in self.ghosts:
                    if g.is_frightened and not g.is_dead:
                        g.color = color.white if flash_on else color.blue
                        for leg in g.skirt_legs:
                            leg.color = color.white if flash_on else color.blue
            
            if self.frightened_timer <= 0:
                for g in self.ghosts:
                    if not g.is_dead:
                        g.set_frightened(False)
                self.ghost_mode = "CHASE" if (self.mode_cycle_count % 2 == 1) else "SCATTER"
                self.update_ui()
        else:
            self.mode_timer -= time.dt
            if self.mode_timer <= 0:
                self.mode_cycle_count += 1
                if self.ghost_mode == "SCATTER":
                    self.ghost_mode = "CHASE"
                    self.mode_timer = 20.0
                else:
                    self.ghost_mode = "SCATTER"
                    self.mode_timer = 7.0
                self.update_ui()
                            
        # Respawn dead ghosts when reaching home base coordinates
        for g in self.ghosts:
            if g.is_dead and g.grid_x == 13 and g.grid_y == 11:
                g.is_dead = False
                g.color = g.original_color
                for leg in g.skirt_legs:
                    leg.color = g.original_color
                g.speed = 4.0
                g.pupil_left.color = color.blue
                g.pupil_right.color = color.blue
                self.spawn_burst(g.position, g.original_color, count=12)

    def input(self, key):
        if self.destroyed:
            return
        if key == 'r':
            self.start_game()

    # =========================================================================
    # THE TEARDOWN SHUTDOWN PHASES (PREVENTS CRASHES)
    # =========================================================================
    def destroy(self):
        """
        Kills all map assets, scoreboard text panels, floating labels, 
        and fully restores default engine perspectives without tracebacks.
        """
        self.destroyed = True
        self.game_over = True

        # Clear references
        self.pellets.clear()
        self.power_pellets.clear()
        self.ghosts.clear()
        self.walls.clear()
        self.effects.clear()
        self.pacman = None
        self.active_fruit = None
        self.gate_entity = None

        # Terminate physical models
        for entity in self.entities.copy():
            destroy(entity)
        self.entities.clear()

        # Terminate texts overlays
        for ui in self.ui_elements.copy():
            destroy(ui)
        self.ui_elements.clear()

        # Re-apply window preferences back to normal caller state
        window.color = self.old_window_color
        camera.orthographic = self.old_camera_orthographic
        camera.fov = self.old_camera_fov
        camera.parent = scene
        camera.position = self.old_camera_position
        camera.rotation = self.old_camera_rotation