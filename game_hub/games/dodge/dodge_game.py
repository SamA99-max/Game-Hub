from ursina import *
from random import uniform, choice, randint

class DodgeGame:
    """
    DodgeGame class designed for a modular mini-game engine.
    Encapsulates the synthwave endless runner, neon grid lines, trailing particles,
    and environmental fog under a perfectly clean lifecycle.
    """

    def __init__(self):
        # ---------------- ENGINE LIFECYCLE TRACKING ----------------
        self.destroyed = False

        # Save previous engine configurations to restore on destroy
        self.old_camera_position = camera.position
        self.old_camera_rotation = camera.rotation
        self.old_camera_fov = camera.fov
        self.old_fog_color = getattr(scene, 'fog_color', color.clear)
        self.old_fog_density = getattr(scene, 'fog_density', (0, 0))

        # Set game specialized camera & environment settings
        camera.position = (0, 6, -14)
        camera.rotation = (22, 0, 0)
        camera.fov = 85
        scene.fog_color = color.black
        scene.fog_density = (10, 70)

        # Entity tracking for clean destruction
        self.entities = []
        self.ui_elements = []
        
        self.grid_lines = []
        self.obstacles = []
        self.particles = []

        # ---------------- GAME STATE ----------------
        self.score = 0
        self.game_over = False
        self.max_limit = 4.5
        self.frame_counter = 0 
        self.neon_colors = [color.magenta, color.lime, color.orange, color.yellow, color.violet]
        
        self.spawn_timer = 1.0  # Safely replaces invoke() loops

        # ---------------- WORLD & UI BUILD ----------------
        self.build_world()
        self.build_ui()

    # =========================================================================
    # WORLD CONSTRUCTION
    # =========================================================================
    def build_world(self):
        # Ground Plane with Glowing Neon Grid
        self.ground = Entity(
            model='plane',
            texture='white_cube',
            scale=(20, 1, 120),
            color=color.rgb(15, 15, 25),
            position=(0, 0, 50)
        )
        self.entities.append(self.ground)

        # Visual Grid Lines on Ground
        for z_pos in range(0, 100, 4):
            line = Entity(
                model='cube',
                scale=(20, 0.05, 0.1),
                color=color.cyan,
                position=(0, 0.02, z_pos),
                unlit=True
            )
            self.grid_lines.append(line)
            self.entities.append(line)

        # Player Setup with Cyber Glow
        self.player = Entity(
            model='cube',
            texture='white_cube',
            color=color.cyan,
            scale=(1, 1, 1),
            position=(0, 0.5, 0),
            collider='box'
        )
        self.entities.append(self.player)

    def build_ui(self):
        self.score_text = Text(
            text='SCORE: 0',
            position=(-0.85, 0.45),
            scale=2.5,
            color=color.cyan,
            origin=(-0.5, 0.5)
        )
        self.ui_elements.append(self.score_text)

        self.restart_text = Text(
            text='',
            position=(0, 0),
            scale=3,
            color=color.red,
            origin=(0, 0)
        )
        self.ui_elements.append(self.restart_text)

    # =========================================================================
    # DYNAMIC PARTICLE EFFECTS
    # =========================================================================
    def create_trail_particle(self):
        if self.destroyed or self.game_over:
            return
            
        p = Entity(
            model='cube',
            color=color.azure,
            scale=(0.4, 0.4, 0.4),
            position=self.player.position + Vec3(0, -0.2, -0.5),
            unlit=True
        )
        p.animate_scale(0, duration=0.4)
        p.animate_color(color.clear, duration=0.4)
        p.life = 0.4  # Tracked manually instead of via destroy(delay=X)
        
        self.particles.append(p)
        self.entities.append(p)

    def particle_burst(self, pos, burst_color):
        if self.destroyed:
            return
            
        for _ in range(12):
            p = Entity(
                model='cube',
                scale=uniform(0.1, 0.3),
                color=burst_color,
                position=pos,
                unlit=True
            )
            p.animate_position(
                pos + Vec3(uniform(-2, 2), uniform(0, 2), uniform(-2, 2)),
                duration=0.5,
                curve=curve.linear
            )
            p.animate_color(color.clear, duration=0.5)
            p.life = 0.5
            
            self.particles.append(p)
            self.entities.append(p)

    # =========================================================================
    # OBSTACLE GENERATOR
    # =========================================================================
    def spawn_obstacle(self):
        if self.destroyed or self.game_over:
            return
        
        size = uniform(0.8, 1.8)
        obs_color = choice(self.neon_colors)
        
        obs = Entity(
            model='cube',
            texture='white_cube',
            color=obs_color,
            scale=(size, size, size),
            position=(uniform(-self.max_limit, self.max_limit), size / 2, 50),
            collider='box',
            unlit=False
        )
        obs.speed = uniform(12, 18)
        obs.rot_speed = Vec3(randint(-50, 50), randint(-50, 50), randint(-50, 50))
        
        self.obstacles.append(obs)
        self.entities.append(obs)
        
        # Determine the delay for the next spawn based on current score
        next_delay = max(0.4, uniform(0.7, 1.3) - (self.score * 0.01))
        self.spawn_timer = next_delay

    # =========================================================================
    # CORE ENGINE INTERFACE (INPUT & UPDATE)
    # =========================================================================
    def input(self, key):
        if self.destroyed: return

        if key == 'r' and self.game_over:
            # Cleanly reset game state
            for obs in self.obstacles:
                if obs in self.entities:
                    self.entities.remove(obs)
                destroy(obs)
            self.obstacles.clear()
            
            self.score = 0
            self.score_text.text = 'SCORE: 0'
            self.score_text.color = color.cyan
            self.restart_text.text = ''
            
            self.game_over = False
            self.player.color = color.cyan
            self.player.position = (0, 0.5, 0)
            self.player.rotation = (0, 0, 0)
            camera.rotation_z = 0
            
            self.spawn_timer = 1.0

    def update(self):
        if self.destroyed: return
        
        self.frame_counter += 1 
        
        # 1. Update Safe Particles 
        for p in self.particles[:]:
            p.life -= time.dt
            if p.life <= 0:
                if p in self.particles: self.particles.remove(p)
                if p in self.entities: self.entities.remove(p)
                destroy(p)

        # 2. Animate synthwave grid lines regardless of game over
        for line in self.grid_lines:
            line.z -= 15 * time.dt
            if line.z < -10:
                line.z += 100

        if self.game_over:
            return

        # 3. Dynamic spawner (Replaces invoke loop)
        self.spawn_timer -= time.dt
        if self.spawn_timer <= 0:
            self.spawn_obstacle()

        # 4. Player movement using A/D or Left/Right arrows
        move_dir = held_keys['right arrow'] - held_keys['left arrow'] + held_keys['d'] - held_keys['a']
        self.player.x += move_dir * 12 * time.dt
        
        # Smooth banking/rotation effect when turning
        target_rotation_z = -move_dir * 15
        self.player.rotation_z = lerp(self.player.rotation_z, target_rotation_z, time.dt * 10)
        
        # Camera slight dynamic tilt
        camera.rotation_z = lerp(camera.rotation_z, -move_dir * 2, time.dt * 5)

        # 5. Spawn engine trails
        if move_dir != 0 or self.frame_counter % 3 == 0:
            self.create_trail_particle()

        # Keep player within bounds
        self.player.x = clamp(self.player.x, -self.max_limit, self.max_limit)

        # 6. Move obstacles toward the player
        for obs in self.obstacles[:]:
            obs.z -= obs.speed * time.dt
            obs.rotation += obs.rot_speed * time.dt

            # Collision Check
            hit_info = self.player.intersects()
            if hit_info.hit and hit_info.entity in self.obstacles:
                self.game_over = True
                self.particle_burst(self.player.position, color.red)
                self.player.color = color.red
                
                self.score_text.text = f'GAME OVER!\nFINAL SCORE: {int(self.score)}'
                self.score_text.color = color.red
                self.restart_text.text = 'PRESS R TO RESTART'
                camera.shake(duration=0.5, magnitude=0.5)
                return
            
            # Remove obstacles that passed behind the player
            if obs.z < -5:
                self.particle_burst(obs.position, obs.color)
                
                if obs in self.entities: self.entities.remove(obs)
                self.obstacles.remove(obs)
                destroy(obs)
                
                self.score += 1
                self.score_text.text = f'SCORE: {int(self.score)}'

    # =========================================================================
    # DETAILED CLEANUP (THE DESTRUCTION INTERFACE)
    # =========================================================================
    def destroy(self):
        """
        Safely clears all dynamic entities, grid lines, UI elements, and particles.
        Halts updates and completely restores camera, environment, and fog settings.
        """
        self.destroyed = True
        self.game_over = True

        # Clear pooled references
        self.grid_lines.clear()
        self.obstacles.clear()
        self.particles.clear()

        # Destroy physical entities
        for entity in self.entities.copy():
            destroy(entity)
        self.entities.clear()

        # Destroy UI elements
        for ui in self.ui_elements.copy():
            destroy(ui)
        self.ui_elements.clear()

        # Restore original engine state to avoid breaking main menus
        camera.position = self.old_camera_position
        camera.rotation = self.old_camera_rotation
        camera.fov = self.old_camera_fov
        scene.fog_color = self.old_fog_color
        scene.fog_density = self.old_fog_density