from ursina import *
import random

class FlappyBirdGame:
    """
    FlappyBirdGame class designed for a modular mini-game engine.
    Encapsulates all zero-instantiation object pools, math-based collisions,
    particle bursts, cloud parallax, and camera shake routines under a clean lifecycle.
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
        window.color = color.cyan
        camera.orthographic = True
        camera.fov = 10
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)

        # Entity tracking for clean destruction
        self.entities = []
        self.ui_elements = []

        # Sky background entity
        self.sky = Sky()
        self.entities.append(self.sky)

        # ---------------- 1. OBJECT POOLS (ZERO LAG ARCHITECTURE) ----------------
        self.MAX_PARTICLES = 300
        self.particles_pool = [Entity(model='sphere', unlit=True, enabled=False) for _ in range(self.MAX_PARTICLES)]
        self.p_idx = 0
        self.entities.extend(self.particles_pool)

        self.MAX_TRAILS = 100
        self.trail_pool = [
            {'ent': Entity(model='sphere', color=color.azure, unlit=True, enabled=False), 'life': 0} 
            for _ in range(self.MAX_TRAILS)
        ]
        self.trail_idx = 0
        self.entities.extend([t['ent'] for t in self.trail_pool])

        self.MAX_PIPES = 6
        self.pipe_pool = []
        for _ in range(self.MAX_PIPES):
            top = Entity(model='cube', texture='white_cube', color=color.olive, scale=(1, 0, 1), enabled=False)
            bottom = Entity(model='cube', texture='white_cube', color=color.olive, scale=(1, 0, 1), enabled=False)
            self.pipe_pool.append({'top': top, 'bottom': bottom, 'passed': False})
            self.entities.extend([top, bottom])
        self.pipe_idx = 0

        self.clouds = [
            Entity(
                model='cube', 
                color=color.white33, 
                scale=(random.uniform(2, 6), random.uniform(0.5, 1.5), 1), 
                position=(random.uniform(-15, 15), random.uniform(-4, 4), 5), 
                unlit=True
            ) 
            for _ in range(12)
        ]
        self.entities.extend(self.clouds)

        self.popups = [Text(text='+1', scale=3, color=color.gold, enabled=False) for _ in range(5)]
        self.popup_idx = 0
        self.ui_elements.extend(self.popups)

        # ---------------- 2. GAME VARIABLES & ENTITIES ----------------
        self.bird = Entity(model='sphere', color=color.azure, scale=0.5, x=-3, y=0)
        self.entities.append(self.bird)

        self.velocity = 0
        self.gravity = -18
        self.jump_force = 7

        self.pipe_speed = 4
        self.spawn_timer = 0
        self.gap_size = 3

        self.score = 0
        self.score_text = Text(text='Score: 0', position=(-0.85, 0.45), scale=2)
        self.ui_elements.append(self.score_text)

        self.game_over = False
        self.game_over_text = Text(text="GAME OVER\nPress R", origin=(0, 0), scale=3, color=color.red, enabled=False)
        self.ui_elements.append(self.game_over_text)

        # Camera shake state
        self.shake_time = 0
        self.shake_amt = 0

    # =========================================================================
    # HIGH-PERFORMANCE GAME MECHANICS
    # =========================================================================
    def particle_burst(self, pos, amount=20, burst_color=None):
        if self.destroyed: return

        for _ in range(amount):
            p = self.particles_pool[self.p_idx]
            self.p_idx = (self.p_idx + 1) % self.MAX_PARTICLES
            
            p.enabled = True
            p.position = pos
            p.scale = random.uniform(.05, .15)
            p.color = burst_color if burst_color else random.choice([
                color.red, color.orange, color.yellow, color.lime, 
                color.azure, color.magenta, color.cyan, color.violet
            ])
            
            target_pos = p.position + Vec3(random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5), 0)
            p.animate_position(target_pos, duration=random.uniform(0.4, 0.7), curve=curve.out_expo)
            p.animate_scale(0, duration=0.6)
            p.animate_color(color.clear, duration=0.6)
            
            def disable_particle(particle=p):
                if not self.destroyed and particle:
                    particle.enabled = False
            invoke(disable_particle, delay=0.7)

    def spawn_pipe(self):
        if self.destroyed: return

        pair = self.pipe_pool[self.pipe_idx]
        self.pipe_idx = (self.pipe_idx + 1) % self.MAX_PIPES
        
        top, bottom = pair['top'], pair['bottom']
        top.enabled, bottom.enabled = True, True
        pair['passed'] = False
        
        gap_y = random.uniform(-2, 2)
        top.position = (8, gap_y + self.gap_size/2 + 4, 0)
        bottom.position = (8, gap_y - self.gap_size/2 - 4, 0)
        
        top.animate_scale((1, 8, 1), duration=0.4, curve=curve.out_back)
        bottom.animate_scale((1, 8, 1), duration=0.4, curve=curve.out_back)

    def reset_game(self):
        if self.destroyed: return

        self.velocity, self.spawn_timer, self.score = 0, 0, 0
        self.score_text.text = "Score: 0"
        self.game_over = False
        self.game_over_text.enabled = False
        self.shake_time = 0
        camera.x, camera.y = 0, 0

        self.bird.position = (-3, 0, 0)
        self.bird.rotation_z = 0
        self.bird.scale = 0.5

        for pair in self.pipe_pool:
            pair['top'].enabled = False
            pair['bottom'].enabled = False

    def end_game(self):
        if self.game_over or self.destroyed: return

        self.game_over = True
        self.velocity = 0

        # extreme squash on death
        self.bird.scale_x = 0.8
        self.bird.scale_y = 0.2

        # death explosion
        self.particle_burst(self.bird.position, 80)

        # Trigger heavy camera shake
        self.shake_time = 0.35
        self.shake_amt = 0.2

        self.game_over_text.enabled = True

    # =========================================================================
    # CORE ENGINE INTERFACE (INPUT & UPDATE)
    # =========================================================================
    def input(self, key):
        if self.destroyed: return

        if self.game_over and (key == 'r' or key == 'any'):
            self.reset_game()
            return

        if self.game_over: return

        if key == 'space' or key == 'left mouse down':
            self.velocity = self.jump_force

            # Squash and stretch
            self.bird.scale_x = 0.3
            self.bird.scale_y = 0.7

            self.particle_burst(self.bird.position, 15, color.white50)

            # Trigger slight camera shake
            self.shake_time = 0.05
            self.shake_amt = 0.05

    def update(self):
        if self.destroyed: return

        # --- HIGH-PERFORMANCE CAMERA SHAKE ---
        if self.shake_time > 0:
            self.shake_time -= time.dt
            camera.x = random.uniform(-self.shake_amt, self.shake_amt)
            camera.y = random.uniform(-self.shake_amt, self.shake_amt)
            if self.shake_time <= 0:
                camera.x, camera.y = 0, 0

        # --- CLOUD PARALLAX (POOLED) ---
        for c in self.clouds:
            c.x -= (self.pipe_speed * 0.3) * time.dt
            if c.x < -15:
                # Wrap around instead of destroying
                c.x = random.uniform(12, 18)
                c.y = random.uniform(-4, 4)
                c.scale = (random.uniform(2, 6), random.uniform(0.5, 1.5), 1)

        if self.game_over:
            if self.bird.y > -5:
                self.velocity += self.gravity * time.dt * 2
                self.bird.y += self.velocity * time.dt
                self.bird.rotation_z -= 200 * time.dt
            return

        # --- BIRD PHYSICS & ANIMATION ---
        self.velocity += self.gravity * time.dt
        self.bird.y += self.velocity * time.dt

        target_rotation = clamp(self.velocity * 4, -90, 35)
        self.bird.rotation_z += (target_rotation - self.bird.rotation_z) * 12 * time.dt
        
        self.bird.scale_x += (0.5 - self.bird.scale_x) * 10 * time.dt
        self.bird.scale_y += (0.5 - self.bird.scale_y) * 10 * time.dt

        # --- MANUAL TRAIL SYSTEM (ZERO LAG) ---
        td = self.trail_pool[self.trail_idx]
        self.trail_idx = (self.trail_idx + 1) % self.MAX_TRAILS
        td['ent'].enabled = True
        td['ent'].position = self.bird.position - Vec3(0.2, 0, 0)
        td['ent'].color = color.azure
        td['life'] = 0.4

        # Update active trails
        for t in self.trail_pool:
            if t['life'] > 0:
                t['life'] -= time.dt
                if t['life'] <= 0:
                    t['ent'].enabled = False
                else:
                    t['ent'].x -= (self.pipe_speed * 0.4) * time.dt
                    progress = 1 - (t['life'] / 0.4)
                    t['ent'].scale = 0.15 * (1 - progress)
                    t['ent'].alpha = t['life'] / 0.4 # Fade out

        # --- BOUNDS CHECK ---
        if self.bird.y > 5 or self.bird.y < -5:
            self.end_game()

        # --- PIPE LOGIC & MATH-BASED COLLISIONS ---
        self.spawn_timer += time.dt
        if self.spawn_timer >= 2:
            self.spawn_timer = 0
            self.spawn_pipe()

        bird_r = 0.2 # Bird collision radius (slightly forgiving)

        for pair in self.pipe_pool:
            top, bottom = pair['top'], pair['bottom']
            if not top.enabled: continue

            top.x -= self.pipe_speed * time.dt
            bottom.x -= self.pipe_speed * time.dt

            # Score logic
            if not pair['passed'] and top.x < self.bird.x:
                pair['passed'] = True
                self.score += 1
                self.score_text.text = f"Score: {self.score}"
                
                # Score popup
                pop = self.popups[self.popup_idx]
                self.popup_idx = (self.popup_idx + 1) % len(self.popups)
                pop.enabled = True
                pop.color = color.gold
                pop.world_position = self.bird.position + Vec3(.8, .5, 0)
                pop.animate_y(pop.y + .8, duration=.5, curve=curve.out_expo)
                pop.animate_scale(4, duration=.2)
                pop.animate_color(color.clear, duration=.5)
                
                def disable_popup(popup=pop):
                    if not self.destroyed and popup:
                        popup.enabled = False
                invoke(disable_popup, delay=.5)

            # LIGHTNING FAST MATH COLLISION
            if top.x - 0.5 < self.bird.x + bird_r and top.x + 0.5 > self.bird.x - bird_r:
                if self.bird.y + bird_r > top.y - 4 or self.bird.y - bird_r < bottom.y + 4:
                    self.end_game()

            # Cleanup offscreen pipes
            if top.x < -10:
                top.enabled = False
                bottom.enabled = False

    # =========================================================================
    # DETAILED CLEANUP (THE DESTRUCTION INTERFACE)
    # =========================================================================
    def destroy(self):
        """
        Safely clears all pre-allocated pools, entities, and UI elements.
        Halts updates and completely restores camera and engine settings.
        """
        self.destroyed = True
        self.game_over = True

        # Clear pooled references
        self.pipe_pool.clear()
        self.trail_pool.clear()
        self.particles_pool.clear()
        self.clouds.clear()

        # Destroy physical entities
        for entity in self.entities.copy():
            destroy(entity)
        self.entities.clear()

        # Destroy UI elements
        for ui in self.ui_elements.copy():
            destroy(ui)
        self.ui_elements.clear()

        # Restore original engine state
        window.color = self.old_window_color
        camera.orthographic = self.old_camera_orthographic
        camera.fov = self.old_camera_fov
        camera.parent = scene
        camera.position = self.old_camera_position
        camera.rotation = self.old_camera_rotation