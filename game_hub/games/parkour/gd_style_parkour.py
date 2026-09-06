from ursina import *
import random
import math
import time as pytime

class NeonCyberDash:
    '''
    NeonCyberDash is a high-performance lag-free infinite parkour within ursina.
    its a fast-paced, 2D Geometry-Dash inspired parkour game
    '''
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
        camera.fov = 14
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)

        # ---------------- 1. OBJECT POOLS (ZERO LAG ARCHITECTURE) ----------------
        # Pre-allocate all entities. We will enable/disable instead of create/destroy.
        self.pool_platforms = [Entity(model='cube', texture='white_cube', color=color.white, enabled=False) for _ in range(120)]
        self.pool_spikes = [Entity(model='cube', color=color.red, rotation_z=45, enabled=False) for _ in range(100)]
        self.pool_coins = [Entity(model='circle', color=color.yellow, enabled=False) for _ in range(80)]
        self.pool_pads = [Entity(model='sphere', color=color.magenta, enabled=False) for _ in range(30)]
        
        self.pool_trails = [Entity(model='cube', enabled=False) for _ in range(40)]
        self.pool_particles = [Entity(model='cube', enabled=False) for _ in range(200)]
        self.pool_lines = [Entity(model='quad', enabled=False) for _ in range(40)]
        self.pool_shockwaves = [Entity(model='circle', enabled=False) for _ in range(15)]
        
        self.pool_danger = [Entity(model='cube', color=color.rgba(255,0,0,80), enabled=False) for _ in range(10)]

        # Active trackers
        self.active_platforms = []
        self.active_spikes = []
        self.active_coins = []
        self.active_pads = []
        self.active_danger = []
        
        self.fx_trails = []
        self.fx_particles = []
        self.fx_lines = []
        self.fx_shockwaves = []
        
        # ---------------- UI & SCORE ----------------
        self.score = 0
        self.coins_collected = 0
        self._last_score = -1
        self._last_speed = -1
        self._last_coins = -1
        
        self.ui_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,180), scale=(0.52, 0.12), position=(-0.6, 0.44))
        self.score_text = Text(text='SCORE: 0 | COINS: 0', position=(-0.83, 0.47), scale=1.5, color=color.cyan)
        self.speed_text = Text(text='SPEED: 1.0x', position=(-0.83, 0.41), scale=1.2, color=color.yellow)
        self.game_over_text = Text(text='CRITICAL FAILURE', position=(0, 0), scale=4, color=color.red, origin=(0,0), enabled=False)
        
        # ---------------- PLAYER ----------------
        self.player = Entity(model='cube', texture='white_cube', color=color.cyan, scale=(1, 1, 1), position=(0, 5, 0))
        
        # ---------------- PHYSICS & MOVEMENT ----------------
        self.base_speed = 13.0
        self.speed = self.base_speed
        self.jump_power = 21.0
        self.gravity = 82.0
        
        self.y_velocity = 0.0
        self.on_ground = False
        self.jump_buffer = 0.0
        self.is_dead = False
        self.death_timer = 0.0
        
        # Mechanics
        self.max_jumps = 2
        self.jumps_left = self.max_jumps
        
        self.dash_cooldown = 0.0
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_power = 34.0
        
        # ---------------- VISUALS & EFFECTS ----------------
        self.trail_timer = 0.0
        self.speed_lines_timer = 0.0
        self.bg_hue = 0.0
        
        self.world_end = 0.0
        self.build_world()

    def get_from_pool(self, pool_list):
        """Ultra-fast O(N) pool fetcher."""
        if self.destroyed:
            return None
        for e in pool_list:
            if not e.enabled:
                e.enabled = True
                return e
        return None 

    def build_world(self):
        """Resets game and pools safely without invoking destroy()"""
        if self.destroyed:
            return
        self.is_dead = False
        self.game_over_text.enabled = False
        camera.fov = 14
        
        # Release all active entities back to their pools
        for lst in (self.active_platforms, self.active_spikes, self.active_coins, self.active_pads, self.active_danger):
            for item in lst:
                item.enabled = False
            lst.clear()
            
        for lst in (self.fx_trails, self.fx_particles, self.fx_lines, self.fx_shockwaves):
            for item in lst:
                item['e'].enabled = False
            lst.clear()
        
        # Reset Player
        if self.player:
            self.player.position = (0, 5, 0)
            self.player.rotation = (0, 0, 0)
            self.player.color = color.cyan
            self.player.enabled = True
        
        self.y_velocity = 0.0
        self.on_ground = False
        self.jumps_left = self.max_jumps
        self.dash_cooldown = 0.0
        self.is_dashing = False
        self.score = 0
        self.coins_collected = 0
        self._last_score = -1 # Force UI refresh
        self.update_ui()
        
        self.world_end = 17.0
        
        # Safe Initial Platform
        self.make_plat(5, -1, 25, 2)
        
        for _ in range(8):
            self.generate_chunk()

    # ---------------- POOLED LEVEL GENERATORS ----------------
    def make_plat(self, x, y, w, h):
        p = self.get_from_pool(self.pool_platforms)
        if not p: return
        p.position = (x, y, 0)
        p.scale = (w, h, 1)
        hx, hy = w / 2.0, h / 2.0
        p.static_bounds = (x - hx, x + hx, y - hy, y + hy)
        self.active_platforms.append(p)

    def make_spike(self, x, y):
        s = self.get_from_pool(self.pool_spikes)
        if not s: return
        s.position = (x, y + 0.35, 0)
        s.scale = (0.7, 0.7, 1)
        hx = (0.7 / 2.0) - 0.18
        hy = (0.7 / 2.0) - 0.18
        s.static_bounds = (s.x - hx, s.x + hx, s.y - hy, s.y + hy)
        self.active_spikes.append(s)

    def create_coin(self, x, y):
        c = self.get_from_pool(self.pool_coins)
        if not c: return
        c.position = (x, y, 0)
        c.scale = 0.6
        c.static_bounds = (x - 0.3, x + 0.3, y - 0.3, y + 0.3)
        c.base_y = y
        c.time_offset = random.uniform(0, 10)
        self.active_coins.append(c)

    def create_jump_pad(self, x, y, radius=1):
        pad = self.get_from_pool(self.pool_pads)
        if not pad: return
        pad.position = (x, y, 0)
        pad.scale = radius * 2
        pad.radius = radius
        pad.boost = 2.5
        pad.cooldown = 0
        self.active_pads.append(pad)

    def generate_chunk(self):
        choice = random.randint(1, 10)
        start_x = self.world_end
        
        if choice == 1:
            self.make_plat(start_x + 5, -1, 10, 2)
            self.create_coin(start_x + 3, 1)
            self.create_coin(start_x + 7, 1)
            self.world_end += 10
        elif choice == 2:
            self.make_plat(start_x + 6, -1, 12, 2)
            self.make_spike(start_x + 4, 0)
            self.make_spike(start_x + 8, 0)
            self.world_end += 12
        elif choice == 3:
            self.make_plat(start_x + 2, -1, 4, 2)
            self.make_plat(start_x + 11, -1, 6, 2)
            self.create_coin(start_x + 6.5, 1.5)
            self.world_end += 14
        elif choice == 4:
            self.make_plat(start_x + 2, -1, 4, 2)
            self.create_jump_pad(start_x + 2, 0)
            self.make_plat(start_x + 12, 4, 6, 2)
            self.create_coin(start_x + 12, 6)
            self.world_end += 15
        elif choice == 5:
            self.make_plat(start_x + 2, 2, 4, 2)
            self.make_plat(start_x + 7, 0.5, 3, 2)
            self.make_plat(start_x + 12, -1, 4, 2)
            self.world_end += 14
        elif choice == 6:
            self.make_plat(start_x + 7, -1, 14, 2)
            self.make_spike(start_x + 5, 0)
            self.make_spike(start_x + 6.5, 0)
            self.make_spike(start_x + 8, 0)
            self.create_coin(start_x + 6.5, 3)
            self.world_end += 14
        elif choice == 7:
            self.make_plat(start_x + 2, -1, 4, 2)
            self.make_plat(start_x + 8, 1, 4, 1.5)
            self.make_plat(start_x + 14, -1, 4, 2)
            self.world_end += 16
        elif choice == 8:
            self.make_plat(start_x + 6, -1, 12, 2)
            self.make_plat(start_x + 6, 5, 12, 2)
            self.make_spike(start_x + 6, 0)
            self.create_coin(start_x + 6, 2)
            self.world_end += 12
        elif choice == 9:
            self.make_plat(start_x + 2, 5, 4, 2)
            self.make_plat(start_x + 12, 1, 5, 2)
            self.create_jump_pad(start_x + 12, 2, radius=4)
            self.make_plat(start_x + 24, 7, 6, 2)
            self.world_end += 27
        elif choice == 10:
            self.make_plat(start_x + 2, -1, 4, 2)
            self.make_plat(start_x + 15, -1, 4, 2)
            self.create_coin(start_x + 8.5, 2)
            
            d = self.get_from_pool(self.pool_danger)
            if d:
                d.position = (start_x + 8.5, -5, 1)
                d.scale = (8, 1, 1)
                self.active_danger.append(d)
                
            self.world_end += 17

    # ---------------- OPTIMIZED UI ----------------
    def update_ui(self):
        """Throttles mesh updates to only when data changes (Fixes UI frame drops)"""
        if self.destroyed:
            return
        speed_mult = round(self.speed / self.base_speed, 2)
        target_score = int(self.score)
        
        if speed_mult != self._last_speed or target_score != self._last_score or self.coins_collected != self._last_coins:
            self.score_text.text = f'SCORE: {target_score:05d} | COINS: {self.coins_collected}'
            self.speed_text.text = f'SPEED: {speed_mult}x'
            
            if speed_mult > 1.3: self.speed_text.color = color.red
            elif speed_mult > 1.1: self.speed_text.color = color.orange
            else: self.speed_text.color = color.yellow
            
            self._last_score = target_score
            self._last_speed = speed_mult
            self._last_coins = self.coins_collected

    # ---------------- POOLED EFFECT GENERATORS ----------------
    def spawn_particles(self, position, color_choice, count=15, speed=5.0, scale=0.3):
        if self.destroyed:
            return
        for _ in range(count):
            p = self.get_from_pool(self.pool_particles)
            if not p: break
            p.position = position
            p.color = color_choice
            self.fx_particles.append({
                'e': p, 'life': 0.6, 'max_life': 0.6, 'scale': scale,
                'dx': random.uniform(-1, 1) * speed, 'dy': random.uniform(-1, 1) * speed,
                'rx': random.uniform(-300, 300), 'ry': random.uniform(-300, 300), 'rz': random.uniform(-300, 300)
            })

    def spawn_shockwave(self, position, clr):
        if self.destroyed:
            return
        sw = self.get_from_pool(self.pool_shockwaves)
        if sw:
            sw.position = position
            sw.color = clr
            self.fx_shockwaves.append({'e': sw, 'life': 0.3})

    def die(self):
        if self.is_dead or self.destroyed: return
        self.is_dead = True
        self.spawn_particles(self.player.position, self.player.color, count=40, speed=12, scale=0.5)
        self.player.enabled = False
        self.game_over_text.enabled = True
        self.death_timer = 1.0 

    def get_player_bounds(self, shrink_x=0.0, shrink_y=0.0):
        """Calculates dynamic bounds for the player"""
        if self.destroyed or not self.player:
            return (0, 0, 0, 0)
        hx = (self.player.scale_x / 2.0) - shrink_x
        hy = (self.player.scale_y / 2.0) - shrink_y
        px, py = self.player.x, self.player.y
        return (px - hx, px + hx, py - hy, py + hy)

    def check_overlap(self, b1, b2):
        """Lightning fast AABB intersection math"""
        return not (b1[1] <= b2[0] or b1[0] >= b2[1] or b1[3] <= b2[2] or b1[2] >= b2[3])

    def do_jump(self):
        if self.destroyed or not self.player:
            return
        self.y_velocity = self.jump_power
        self.jumps_left -= 1
        self.jump_buffer = 0.0
        
        if self.jumps_left < self.max_jumps - 1:
            self.spawn_shockwave(self.player.position - Vec3(0, 0.5, 0), color.cyan)
            self.player.rotation_z -= 90

    def input(self, key):
        if self.is_dead or self.destroyed: return
            
        if key == 'space' or key == 'up arrow' or key == 'left mouse down':
            if self.jumps_left > 0:
                self.do_jump()
            else:
                self.jump_buffer = 0.15
                
        if key == 'shift' or key == 'right mouse down':
            if self.dash_cooldown <= 0 and not self.is_dashing:
                self.is_dashing = True
                self.dash_timer = 0.15 
                self.dash_cooldown = 1.0 
                self.y_velocity = 0.0
                self.spawn_shockwave(self.player.position, color.azure)
                
                # Visual Thrust replacement using particle pool directly (no quad instantiations!)
                for _ in range(5):
                    p = self.get_from_pool(self.pool_particles)
                    if not p: break
                    p.position = self.player.position
                    p.color = color.white
                    self.fx_particles.append({
                        'e': p, 'life': 0.2, 'max_life': 0.2, 'scale': 0.8,
                        'dx': -15.0, 'dy': random.uniform(-5, 5),
                        'rx': 0, 'ry': 0, 'rz': 0
                    })

    def update(self):
        if self.destroyed:
            return

        raw_dt = time.dt
        if raw_dt > 0.1: raw_dt = 0.1 # Clamp to prevent physics tunneling
            
        if self.is_dead:
            self.bg_hue += raw_dt * 50
            window.color = color.hsv(self.bg_hue % 360, 0.7, 0.08)
            self.process_effects(raw_dt)
            self.death_timer -= raw_dt
            if self.death_timer <= 0:
                self.build_world()
            return

        self.bg_hue += raw_dt * 15
        window.color = color.hsv(self.bg_hue % 360, 0.7, 0.1)

        # ---------------- SPATIAL PARTITIONING (MASSIVE PERFORMANCE GAIN) ----------------
        px = self.player.x
        near_plats = [p for p in self.active_platforms if p.static_bounds[1] > px - 5 and p.static_bounds[0] < px + 15] 
        near_spikes = [s for s in self.active_spikes if s.static_bounds[1] > px - 5 and s.static_bounds[0] < px + 15]
        near_coins = [c for c in self.active_coins if c.static_bounds[1] > px - 5 and c.static_bounds[0] < px + 15]
        near_pads = [pad for pad in self.active_pads if pad.x + pad.radius > px - 5 and pad.x - pad.radius < px + 15]

        # Sub-stepping Physics Engine
        sub_steps = 4
        sub_dt = raw_dt / sub_steps
        for _ in range(sub_steps):
            if not self.is_dead and not self.destroyed:
                self.physics_step(sub_dt, near_plats, near_spikes, near_coins, near_pads)

        # Smooth Camera & FOV
        target_fov = 14 + (self.speed - self.base_speed) * 0.4
        camera.fov = lerp(camera.fov, target_fov, raw_dt * 2)
        target_cam_y = max(3.5, self.player.y * 0.45 + 1.5)
        camera.x = self.player.x + 6
        camera.y = lerp(camera.y, target_cam_y, raw_dt * 5)
        camera.z = -20
        
        if self.player.y < -9:
            self.die()
            return

        # Player Rotation Mechanics
        if not self.on_ground and not self.is_dashing:
            self.player.rotation_z -= 450 * raw_dt
        elif self.is_dashing:
            self.player.rotation_z -= 1000 * raw_dt
        else:
            self.player.rotation_z = round(self.player.rotation_z / 90) * 90
            
        # Spawn Trails
        self.trail_timer -= raw_dt
        if self.trail_timer <= 0:
            t = self.get_from_pool(self.pool_trails)
            if t:
                t.position = self.player.position
                t.rotation_z = self.player.rotation_z
                t.color = self.player.color
                self.fx_trails.append({'e': t, 'life': 0.3})
            self.trail_timer = 0.05 if not self.is_dashing else 0.02

        # Spawn Speed Lines
        self.speed_lines_timer -= raw_dt
        if self.speed_lines_timer <= 0:
            line = self.get_from_pool(self.pool_lines)
            if line:
                line.position = (self.player.x + 30, random.uniform(-2, 12), 5)
                line.scale = (random.uniform(2, 6), 0.1)
                line.color = color.rgba(255,255,255,40)
                self.fx_lines.append({'e': line, 'life': 1.0})
            self.speed_lines_timer = 0.12 / (self.speed / self.base_speed)

        # Level Generation and Garbage Collector
        if self.player.x > self.world_end - 45:
            self.generate_chunk()
            
        self.cleanup_offscreen_entities()
        self.process_effects(raw_dt)
        self.update_ui()

    def process_effects(self, dt):
        """Batches mathematical animation of all VFX outside of heavy background sequences."""
        if self.destroyed:
            return
        # Active Coins (Sway Animation)
        c_time = time.time() * 5
        for c in self.active_coins:
            c.scale = 0.6 + math.sin(c_time + c.time_offset) * 0.1

        # Trails
        for t in self.fx_trails[:]:
            t['life'] -= dt
            if t['life'] <= 0:
                t['e'].enabled = False
                if t in self.fx_trails:
                    self.fx_trails.remove(t)
            else:
                prog = t['life'] / 0.3
                t['e'].scale = Vec3(prog*0.7, prog*0.7, prog*0.7)
                c = t['e'].color
                t['e'].color = color.rgba(c[0], c[1], c[2], int(prog * 255))
        
        # Particles
        for p in self.fx_particles[:]:
            p['life'] -= dt
            if p['life'] <= 0:
                p['e'].enabled = False
                if p in self.fx_particles:
                    self.fx_particles.remove(p)
            else:
                prog = p['life'] / p['max_life']
                e = p['e']
                e.x += p['dx'] * dt
                e.y += p['dy'] * dt
                e.rotation_x += p['rx'] * dt
                e.rotation_y += p['ry'] * dt
                e.rotation_z += p['rz'] * dt
                e.scale = Vec3(prog * p['scale'], prog * p['scale'], prog * p['scale'])
                
        # Shockwaves
        for s in self.fx_shockwaves[:]:
            s['life'] -= dt
            if s['life'] <= 0:
                s['e'].enabled = False
                if s in self.fx_shockwaves:
                    self.fx_shockwaves.remove(s)
            else:
                prog = 1.0 - (s['life'] / 0.3)
                s['e'].scale = Vec3(prog * 3.0, prog * 3.0, prog * 3.0)
                c = s['e'].color
                s['e'].color = color.rgba(c[0], c[1], c[2], int((1.0 - prog) *10))

        # Speed Lines
        for line in self.fx_lines[:]:
            line['life'] -= dt
            if line['life'] <= 0:
                line['e'].enabled = False
                if line in self.fx_lines:
                    self.fx_lines.remove(line)
            else:
                line['e'].x -= 45 * dt

    def physics_step(self, dt, near_plats, near_spikes, near_coins, near_pads):
        """Utilizes spatial-partitioned arrays and pre-calculated AABBs"""
        if self.is_dead or self.destroyed: return

        if self.jump_buffer > 0: self.jump_buffer -= dt
        if self.dash_cooldown > 0: self.dash_cooldown -= dt
        
        self.speed = min(self.base_speed + (self.score / 280), 28.0)

        # --- STEP 1: X-AXIS MOVEMENT ---
        current_x_speed = self.dash_power if self.is_dashing else self.speed
        
        if self.is_dashing:
            self.dash_timer -= dt
            self.player.color = color.azure
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.player.color = color.cyan
        
        self.player.x += current_x_speed * dt
        self.score += current_x_speed * dt * 0.15
        
        player_bounds_x = self.get_player_bounds(shrink_x=0.02, shrink_y=0.1)
        
        for p in near_plats:
            if self.check_overlap(player_bounds_x, p.static_bounds):
                player_bottom = self.player.y - (self.player.scale_y / 2.0)
                platform_top = p.static_bounds[3]
                ledge_height = 1.5 

                if player_bottom >= platform_top - ledge_height:
                    self.player.y = platform_top + self.player.scale_y / 2
                    self.y_velocity = 0
                    self.on_ground = True
                    self.jumps_left = self.max_jumps
                else:
                    self.die()
                    return

        # --- STEP 2: Y-AXIS MOVEMENT ---
        if not self.is_dashing:
            self.y_velocity -= self.gravity * dt
            
        self.player.y += self.y_velocity * dt
        self.on_ground = False
        
        player_bounds_y = self.get_player_bounds(shrink_x=0.1, shrink_y=0.0)
        
        launched = False
        player_radius = self.player.scale_x / 2

        for pad in near_pads:
            pad.cooldown -= dt
            dx, dy = self.player.x - pad.x, self.player.y - pad.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance <= player_radius + pad.radius and pad.cooldown <= 0:
                pad.cooldown = 0.15
                self.player.y = pad.y + pad.radius + player_radius + 0.05
                self.y_velocity = abs(self.jump_power * pad.boost)
                self.on_ground = False
                self.jumps_left = self.max_jumps
                self.spawn_shockwave(pad.position, color.magenta)
                self.spawn_particles(pad.position, color.magenta, count=12)
                launched = True
                break

        if not launched:
            for p in near_plats:
                if self.check_overlap(player_bounds_y, p.static_bounds):
                    if self.y_velocity <= 0: 
                        self.player.y = p.static_bounds[3] + (self.player.scale_y / 2.0)
                        self.y_velocity = 0.0
                        self.on_ground = True
                        self.jumps_left = self.max_jumps
                    elif self.y_velocity > 0:
                        self.player.y = p.static_bounds[2] - (self.player.scale_y / 2.0)
                        self.y_velocity = 0.0

        if self.on_ground and self.jump_buffer > 0:
            self.do_jump()

        # --- STEP 3: HAZARDS ---
        player_bounds_spike = self.get_player_bounds(shrink_x=0.25, shrink_y=0.2)
        for s in near_spikes:
            if self.check_overlap(player_bounds_spike, s.static_bounds):
                self.die()
                return

        # --- STEP 4: COLLECTIBLES ---
        player_bounds_coin = self.get_player_bounds()
        for c in near_coins[:]:
            if self.check_overlap(player_bounds_coin, c.static_bounds):
                self.spawn_particles(c.position, color.yellow, count=8, speed=3)
                
                # Zero-Garbage Cleanup
                c.enabled = False
                if c in near_coins: near_coins.remove(c)
                if c in self.active_coins: self.active_coins.remove(c)
                
                self.coins_collected += 1
                self.score += 50
                
                # Visual Flash managed carefully to avoid overlaps
                self.player.color = color.white
                def reset_col():
                    if not self.is_dead and not self.destroyed and self.player:
                        self.player.color = color.azure if self.is_dashing else color.cyan
                invoke(reset_col, delay=0.1) # Safe invoke using guards

    def cleanup_offscreen_entities(self):
        """Returns entities to the pool instead of destroying them."""
        if self.destroyed:
            return
        cleanup_x = self.player.x - 25.0
        
        for lst in (self.active_platforms, self.active_spikes, self.active_coins, self.active_pads, self.active_danger):
            for item in lst[:]:
                check_pos = item.x + (item.scale_x/2.0 if hasattr(item, 'static_bounds') else 0)
                if check_pos < cleanup_x:
                    item.enabled = False
                    lst.remove(item)

    # =========================================================================
    # DETAILED CLEANUP (THE DESTRUCTION INTERFACE)
    # =========================================================================
    def destroy(self):
        """
        Wipes out all pre-allocated pooled entities, cleans dynamic UI,
        stops all delayed function invokes, and fully restores default camera views.
        """
        # Set absolute lifecycle exit guard
        self.destroyed = True
        self.is_dead = True

        # Cleanly empty trackers
        self.active_platforms.clear()
        self.active_spikes.clear()
        self.active_coins.clear()
        self.active_pads.clear()
        self.active_danger.clear()
        
        self.fx_trails.clear()
        self.fx_particles.clear()
        self.fx_lines.clear()
        self.fx_shockwaves.clear()

        # Sweep and destroy ALL object pools pre-allocated on initialization
        for pool in (self.pool_platforms, self.pool_spikes, self.pool_coins, 
                     self.pool_pads, self.pool_trails, self.pool_particles, 
                     self.pool_lines, self.pool_shockwaves, self.pool_danger):
            for entity in pool:
                destroy(entity)
            pool.clear()

        # Destroy Player model
        if self.player:
            destroy(self.player)
            self.player = None

        # Clean up screen-space UI elements
        for ui in (self.ui_bg, self.score_text, self.speed_text, self.game_over_text):
            if ui:
                destroy(ui)

        # Restore original engine state to avoid breaking main menus
        window.color = self.old_window_color
        camera.orthographic = self.old_camera_orthographic
        camera.fov = self.old_camera_fov
        camera.parent = scene
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)