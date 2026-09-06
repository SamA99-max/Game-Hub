from ursina import *
from random import uniform, randint
from math import radians, sin, cos

class AsteroidsGame:
    """
    AsteroidsGame is a game where you have to shoot astroids in space and also dodge them there are no levels but you 3 lives.
    the game runs with ursina 
    """
    
    def __init__(self):
        # ---------------- ENGINE LIFECYCLE TRACKING ----------------
        self.destroyed = False

        # Save previous engine configurations to restore on destroy
        self.old_window_color = window.color
        self.old_camera_orthographic = camera.orthographic
        self.old_camera_fov = camera.fov
        self.old_camera_position = camera.position
        self.old_camera_rotation = camera.rotation

        # Set game specialized orthographic camera settings
        window.color = color.black
        camera.orthographic = True
        camera.fov = 11
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)

        # ---------------- ENTITY TRACKERS ----------------
        self.entities = []
        self.ui_elements = []
        
        self.stars = []
        self.asteroids = []
        self.bullets = []
        self.particles = []

        # ---------------- GAME STATE ----------------
        self.score = 0
        self.lives = 3
        self.game_paused = False
        self.velocity = Vec2(0, 0)
        self.invulnerable_timer = 5.0
        
        # ---------------- UI ELEMENTS ----------------
        self.score_text = Text(text=f'Score: {self.score}', position=(-0.85, 0.45), scale=2, color=color.yellow)
        self.ui_elements.append(self.score_text)
        
        self.lives_text = Text(text=f'Lives: {self.lives}', position=(0.65, 0.45), scale=2, color=color.azure)
        self.ui_elements.append(self.lives_text)

        self.pause_bg = Entity(model='quad', color=color.black66, scale=(20, 15), z=-1, enabled=False)
        self.entities.append(self.pause_bg)
        
        self.pause_text = Text(
            text='-- PAUSED --\n\nControls:\n[W / Up] - Thrust Forward\n[S / Down] - Reverse Thrust\n[A / D or Left / Right] - Rotate Ship\n[Space] - Shoot Laser\n\nPress [C] to Continue', 
            position=(-0.35, 0.25), scale=1.5, color=color.cyan, enabled=False
        )
        self.ui_elements.append(self.pause_text)

        self.game_over_text = None

        # ---------------- BACKGROUND DECOR (STARS) ----------------
        # Generate a static starfield for a better space atmosphere
        for _ in range(150):
            star = Entity(
                model='circle',
                color=color.hsv(0, 0, uniform(0.5, 1)), 
                scale=uniform(0.01, 0.04),
                position=(uniform(-12, 12), uniform(-8, 8), 1) # Z=1 pushes them behind gameplay
            )
            self.stars.append(star)
            self.entities.append(star)

        # ---------------- PLAYER SHIP ----------------
        self.player = Entity(
            model='quad',
            color=color.azure,
            scale=(0.7, 1),
            collider='box'
        )
        self.player.rotation_z = 0
        self.entities.append(self.player)

        # ---------------- INITIAL ASTEROIDS ----------------
        for i in range(6):
            self.spawn_asteroid()

    # =========================================================================
    # PARTICLE EFFECTS
    # =========================================================================
    def spawn_exhaust(self, pos, rot):
        """Spawns fire particles behind the player ship when thrusting."""
        if self.destroyed: return

        rad = radians(rot + 180)
        # Calculate position at the back of the ship
        rear_x = pos.x + sin(rad) * 0.4
        rear_y = pos.y + cos(rad) * 0.4

        p = Entity(
            model='circle', 
            color=color.orange, 
            scale=uniform(0.1, 0.25), 
            position=(rear_x, rear_y, -0.2)
        )
        
        # Send particles in the opposite direction of the ship with random spread
        spread = radians(rot + 180 + uniform(-25, 25))
        p.vel = Vec2(sin(spread), cos(spread)) * uniform(2, 5)
        p.life = uniform(0.2, 0.5)

        # Animate shrinking and fading
        p.animate_scale(0, duration=p.life)
        p.animate_color(color.rgba(255, 50, 0, 0), duration=p.life)
        
        self.particles.append(p)
        self.entities.append(p)

    def spawn_explosion(self, pos, scale_size, particle_color):
        """Spawns a burst of particles when an object is destroyed."""
        if self.destroyed: return

        num_particles = int(15 * scale_size)
        for _ in range(num_particles):
            p = Entity(
                model='circle', 
                color=particle_color, 
                scale=uniform(0.05, 0.2), 
                position=(pos.x, pos.y, -0.2)
            )
            angle = radians(uniform(0, 360))
            p.vel = Vec2(sin(angle), cos(angle)) * uniform(3, 10)
            p.life = uniform(0.3, 0.7)

            p.animate_scale(0, duration=p.life)
            p.animate_color(color.clear, duration=p.life)
            
            self.particles.append(p)
            self.entities.append(p)

    # =========================================================================
    # GAMEPLAY MECHANICS
    # =========================================================================
    def spawn_asteroid(self, pos=None, scale=None):
        if self.destroyed: return

        if pos is None:
            while True:
                candidate_pos = (uniform(-10, 10), uniform(-6, 6))
                if self.player and self.player.enabled:
                    if distance((candidate_pos[0], candidate_pos[1], 0), self.player.position) > 4.0:
                        pos = candidate_pos
                        break
                else:
                    pos = candidate_pos
                    break

        # Using low-resolution circles to make them look like jagged polygons
        asteroid = Entity(
            model=Circle(resolution=randint(5, 8)),
            color=color.light_gray,
            scale=scale if scale is not None else uniform(1.0, 2.0),
            position=pos,
            collider='box' 
        )

        asteroid.speed = Vec2(uniform(-2.5, 2.5), uniform(-2.5, 2.5))
        # Give asteroids a random tumbling spin
        asteroid.spin_speed = uniform(-80, 80)

        self.asteroids.append(asteroid)
        self.entities.append(asteroid)
        return asteroid

    def shoot(self):
        if self.destroyed or self.lives <= 0 or self.game_paused or not self.player.enabled:
            return
            
        angle = radians(self.player.rotation_z)

        # Elongated quad to look like a laser beam
        bullet = Entity(
            model='quad',
            color=color.cyan,
            scale=(0.08, 0.6),
            position=self.player.position,
            rotation_z=self.player.rotation_z,
            collider='box'
        )

        bullet.direction = Vec2(sin(angle), cos(angle))
        bullet.life = 1.5
        
        self.bullets.append(bullet)
        self.entities.append(bullet)

    def wrap(self, entity):
        if not entity or self.destroyed: return
        if entity.x > 10.5: entity.x = -10.5
        if entity.x < -10.5: entity.x = 10.5
        if entity.y > 6.5: entity.y = -6.5
        if entity.y < -6.5: entity.y = 6.5

    # =========================================================================
    # CORE ENGINE INTERFACE (INPUT & UPDATE)
    # =========================================================================
    def input(self, key):
        if self.destroyed: return
        
        if held_keys['space']:
            self.shoot()
        elif key == 'p':
            self.game_paused = not self.game_paused
            self.pause_bg.enabled = self.game_paused
            self.pause_text.enabled = self.game_paused
        elif key == 'c' and self.game_paused:
            self.game_paused = False
            self.pause_bg.enabled = False
            self.pause_text.enabled = False

    def update(self):
        if self.destroyed: return

        if self.lives <= 0 or self.game_paused:
            return

        # 1. Update Particles safely
        for p in self.particles[:]:
            p.life -= time.dt
            if p.life <= 0:
                if p in self.particles: self.particles.remove(p)
                if p in self.entities: self.entities.remove(p)
                destroy(p)
                continue
            p.position += p.vel * time.dt

        # 2. Player Invulnerability Visuals (blinking translucent)
        if self.player and self.player.enabled:
            if self.invulnerable_timer > 0:
                self.invulnerable_timer -= time.dt
                if int(self.invulnerable_timer * 15) % 2 == 0:
                    self.player.color = color.rgba(0, 255, 255, 100) # Semi-transparent
                else:
                    self.player.color = color.azure
            else:
                self.player.color = color.azure

            # 3. Player Rotation
            if held_keys['d'] or held_keys['right arrow']:
                self.player.rotation_z -= 220 * time.dt
            if held_keys['a'] or held_keys['left arrow']:
                self.player.rotation_z += 220 * time.dt

            # 4. Player Thrust & Particles
            if held_keys['w'] or held_keys['up arrow']:
                angle = radians(self.player.rotation_z)
                self.velocity += Vec2(sin(angle), cos(angle)) * 9 * time.dt
                self.spawn_exhaust(self.player.position, self.player.rotation_z)

            if held_keys['s'] or held_keys['down arrow']:
                # Brake: Smoothly reduce velocity to 0
                self.velocity = lerp(self.velocity, Vec2(0, 0), 4 * time.dt)

            self.velocity *= 0.98 # Friction
            self.player.position += self.velocity * time.dt
            self.wrap(self.player)

            # 5. Player Collision
            hit_info = self.player.intersects()
            if hit_info.hit and hit_info.entity in self.asteroids and self.invulnerable_timer <= 0:
                self.spawn_explosion(self.player.position, 2, color.azure) # Player explodes
                self.lives -= 1
                self.lives_text.text = f'Lives: {self.lives}'
                self.player.position = (0, 0)
                self.velocity = Vec2(0, 0)
                self.invulnerable_timer = 2.5
                
                if self.lives <= 0:
                    self.player.enabled = False
                    self.game_over_text = Text(text='GAME OVER', position=(-0.25, 0), scale=3, color=color.red)
                    self.ui_elements.append(self.game_over_text)

        # 6. Bullets Update & Collision
        for bullet in self.bullets[:]:
            bullet.position += bullet.direction * 15 * time.dt
            bullet.life -= time.dt
            
            if bullet.life <= 0:
                if bullet in self.bullets: self.bullets.remove(bullet)
                if bullet in self.entities: self.entities.remove(bullet)
                destroy(bullet)
                continue

            hit_info = bullet.intersects()
            if hit_info.hit and hit_info.entity in self.asteroids:
                ast = hit_info.entity
                
                if bullet in self.bullets: self.bullets.remove(bullet)
                if bullet in self.entities: self.entities.remove(bullet)
                destroy(bullet)

                self.score += 100
                self.score_text.text = f'Score: {self.score}'

                # Spawn explosion particles from the asteroid
                self.spawn_explosion(ast.position, ast.scale_x, color.light_gray)

                # Asteroids split into smaller pieces
                if ast.scale_x > 0.9:
                    for _ in range(2):
                        self.spawn_asteroid(pos=ast.position, scale=ast.scale_x * 0.5)

                if ast in self.asteroids: self.asteroids.remove(ast)
                if ast in self.entities: self.entities.remove(ast)
                destroy(ast)

                if len(self.asteroids) < 5:
                    self.spawn_asteroid()
                break

        # 7. Asteroids Update (Movement & Spinning)
        for asteroid in self.asteroids:
            asteroid.position += asteroid.speed * time.dt
            asteroid.rotation_z += asteroid.spin_speed * time.dt # Add visual spin
            self.wrap(asteroid)

    # =========================================================================
    # DETAILED CLEANUP (THE DESTRUCTION INTERFACE)
    # =========================================================================
    def destroy(self):
        """
        Wipes out all dynamic entities, stars, UI, and particles.
        Safely halts updates and completely restores the engine camera state.
        """
        # 1. Flag lifecycle guard
        self.destroyed = True
        self.game_paused = True

        # 2. Clear reference lists so no logic processes them
        self.stars.clear()
        self.asteroids.clear()
        self.bullets.clear()
        self.particles.clear()

        # 3. Destroy all physical entities (including stars, player, pause bg, etc.)
        for entity in self.entities.copy():
            destroy(entity)
        self.entities.clear()

        # 4. Destroy all UI texts
        for ui in self.ui_elements.copy():
            destroy(ui)
        self.ui_elements.clear()

        # 5. Restore original engine state to avoid breaking main menus
        window.color = self.old_window_color
        camera.orthographic = self.old_camera_orthographic
        camera.fov = self.old_camera_fov
        camera.parent = scene
        camera.position = self.old_camera_position
        camera.rotation = self.old_camera_rotation