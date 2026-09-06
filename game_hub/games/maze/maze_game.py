from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math

class MazeGame:
    """
    MazeGame class designed for a modular mini-game engine.
    Encapsulates the FirstPersonController safely, handles level generation, 
    stamina systems, crystal collections, and performs a deep clean of the 
    engine's camera and fog states upon destruction.
    """

    # 1 = Wall, 0 = Empty path, 2 = Exit block
    LEVELS = [
        # Easy Level 1: The Zig-Zag (Very straightforward, no dead ends)
        [
            [1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,1,0,1],
            [1,0,1,0,0,0,0,0,0,1],
            [1,0,1,0,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,2,1],
            [1,1,1,1,1,1,1,1,1,1]
        ],
        
        # Easy Level 2: The Open Courtyard (Lots of space to run, highly visible exit)
        [
            [1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,0,1,1,0,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,0,1,1,0,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1]
        ],

        # Easy Level 3: The Quick Loop (A simple circle with a clear path to the center)
        [
            [1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,1,0,0,0,0,1],
            [1,0,1,1,0,1,0,1,1,0,1],
            [1,0,1,2,0,0,0,1,1,0,1],
            [1,0,1,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1]
        ],
        # Level 4: Starter Maze
        [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
            [1,1,1,0,1,0,1,1,1,0,1,0,1,1,1],
            [1,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,0,1,1,1,1,1,0,1,1,1],
            [1,0,1,0,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,1,0,1,1,1,1,1,0,1,1,1,0,1],
            [1,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
            [1,1,1,0,1,0,1,0,1,1,1,0,1,0,1],
            [1,0,0,0,0,0,1,0,0,0,1,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,0,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,1,0,0,0,0,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ],
        # Level 5: Expanded Maze
        [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],
            [1,1,1,0,1,0,1,1,1,0,1,0,1,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0,1],
            [1,0,1,1,1,1,1,0,1,1,1,1,1,1,1,0,1,1,0,1],
            [1,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
            [1,0,1,0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1],
            [1,0,1,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1],
            [1,0,1,0,1,0,1,1,1,1,1,0,1,1,1,1,1,1,0,1],
            [1,0,1,0,1,0,1,0,0,0,1,0,0,0,0,0,0,1,0,1],
            [1,0,1,0,1,1,1,0,1,0,1,1,1,1,1,1,0,1,0,1],
            [1,0,1,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1],
            [1,0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,0,1,0,1],
            [1,0,1,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1,0,1],
            [1,0,0,0,1,1,1,1,0,1,1,1,1,1,0,0,0,1,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ],
        # Level 6: The Twisted Labyrinth
        [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,2,1],
            [1,0,1,1,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1],
            [1,0,0,0,1,0,1,0,1,0,1,0,0,0,1,0,0,0,0,1],
            [1,1,1,0,1,0,1,1,1,0,1,1,1,1,1,0,1,1,0,1],
            [1,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,1,0,0,1],
            [1,0,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,0,1],
            [1,0,0,0,0,0,1,0,1,0,0,0,1,0,0,0,0,1,0,1],
            [1,1,1,1,1,0,1,0,1,0,1,0,1,1,1,1,0,1,0,1],
            [1,0,0,0,1,0,0,0,1,0,1,0,0,0,0,1,0,1,0,1],
            [1,0,1,0,1,1,1,1,1,0,1,1,1,1,0,1,0,1,1,1],
            [1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,0,1,0,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ],
        # Level 7: The Final Citadel
        [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,2,1],
            [1,0,1,1,1,0,1,0,1,1,1,0,1,0,1,1,1,0,1,0,1,1,1,1,1],
            [1,0,1,0,0,0,0,0,1,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,1],
            [1,0,1,0,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,1,1,0,1],
            [1,0,1,0,1,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,1,0,1],
            [1,0,1,0,1,0,1,1,1,1,1,1,1,0,1,0,1,0,1,1,1,0,1,0,1],
            [1,0,0,0,1,0,1,0,0,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1],
            [1,1,1,0,1,0,1,0,1,1,1,0,1,1,1,1,1,0,1,0,1,1,1,1,1],
            [1,0,0,0,1,0,1,0,1,0,1,0,0,0,0,0,1,0,1,0,0,0,0,0,1],
            [1,0,1,1,1,0,1,0,1,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1],
            [1,0,0,0,0,0,1,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ]
    ]

    def __init__(self):
        # ---------------- ENGINE LIFECYCLE TRACKING ----------------
        self.destroyed = False

        # Save caller engine's original camera parameters
        self.old_camera_parent = camera.parent
        self.old_camera_position = camera.position
        self.old_camera_rotation = camera.rotation
        self.old_camera_fov = camera.fov
        
        # Save environment settings
        self.old_fog_color = getattr(scene, 'fog_color', color.clear)
        self.old_fog_density = getattr(scene, 'fog_density', (0, 0))

        # Apply specific atmospheric conditions
        scene.fog_density = 0.08
        scene.fog_color = color.black

        # Tracker collections for memory-safe cleanups
        self.entities = []
        self.ui_elements = []
        
        # Dynamic active level items
        self.maze_blocks = []
        self.crystals = []
        self.exit_block = None

        # Game states
        self.current_level_idx = 0
        self.score = 0
        self.scale_factor = 2.0
        self.game_over = False
        
        # Transitions / Timers
        self.transitioning = False
        self.transition_timer = 0.0
        self.score_pop_target = Vec3(1.5, 1.5, 1.5)

        # Player stats
        self.max_stamina = 100.0
        self.current_stamina = self.max_stamina

        # ---------------- ENVIRONMENT BUILD ----------------
        self.sky = Sky(color=color.black)
        self.entities.append(self.sky)

        self.ground = Entity(
            model='plane', scale=(200, 1, 200), color=color.gray, 
            texture='noise', texture_scale=(50, 50), collider='box'
        )
        self.entities.append(self.ground)

        self.ceiling = Entity(
            model='plane', scale=(200, 1, 200), color=color.black, 
            position=(0, 5.5, 0), texture='noise', rotation_x=180
        )
        self.entities.append(self.ceiling)

        # ---------------- PLAYER (First Person Controller) ----------------
        self.player = FirstPersonController()
        self.player.cursor.visible = True
        self.player.cursor.color = color.yellow
        self.player.speed = 6
        self.player.jump_height = 0  

        # ---------------- UI BUILD ----------------
        self.build_ui()

        # Load first map
        self.load_level(self.current_level_idx)

    def build_ui(self):
        self.win_text = Text(text='', origin=(0, 0), scale=3, color=color.gold, shadow=True)
        self.ui_elements.append(self.win_text)

        self.level_text = Text(text='', position=(-0.85, 0.45), scale=2, color=color.white, shadow=True)
        self.ui_elements.append(self.level_text)

        self.score_text = Text(text='Score: 0', position=(-0.85, 0.40), scale=1.5, color=color.cyan, shadow=True)
        self.ui_elements.append(self.score_text)

        # Stamina Bar
        self.stamina_bg = Entity(parent=camera.ui, model='quad', color=color.dark_gray, scale=(0.4, 0.03), position=(0, -0.4))
        self.stamina_bar = Entity(parent=camera.ui, model='quad', color=color.green, scale=(0.39, 0.02), position=(0, -0.4))
        self.ui_elements.extend([self.stamina_bg, self.stamina_bar])

    def load_level(self, idx):
        """Generates the maze architecture and places collectibles/exit."""
        if self.destroyed: return

        self.transitioning = False
        self.win_text.text = ''
        
        # Clean up dynamic previous level assets
        for e in self.maze_blocks:
            if e in self.entities: self.entities.remove(e)
            destroy(e)
        self.maze_blocks.clear()
        
        for c in self.crystals:
            if c in self.entities: self.entities.remove(c)
            destroy(c)
        self.crystals.clear()
        
        if self.exit_block:
            if self.exit_block in self.entities: self.entities.remove(self.exit_block)
            destroy(self.exit_block)
            self.exit_block = None

        maze_map = self.LEVELS[idx]
        
        # Dynamic styling palettes per level
        wall_palettes = [
            (color.hex('#2E4053'), 'brick'),         # Level 1: Dark Slate
            (color.hex('#641E16'), 'brick'),         # Level 2: Blood Brick
            (color.hex('#145A32'), 'white_cube'),    # Level 3: Mossy Green
            (color.hex('#4A235A'), 'brick'),         # Level 4: Deep Purple
            (color.hex('#7E5109'), 'brick'),         # Level 5: Burnt Amber
            (color.hex('#0E6251'), 'white_cube'),    # Level 6: Deep Teal
            (color.hex('#515A5A'), 'brick')          # Level 7: Charcoal Gray
        ]
        active_color, active_texture = wall_palettes[idx % len(wall_palettes)]
        
        # Matrix Generation
        for z, row in enumerate(maze_map):
            for x, val in enumerate(row):
                posX = x * self.scale_factor
                posZ = z * self.scale_factor
                
                if val == 1: # Wall
                    wall = Entity(
                        model='cube', 
                        texture=active_texture,
                        color=active_color, 
                        position=(posX, 2.75, posZ), 
                        scale=(self.scale_factor, 5.5, self.scale_factor), 
                        collider='box'
                    )
                    self.maze_blocks.append(wall)
                    self.entities.append(wall)
                    
                elif val == 2: # Exit Door
                    self.exit_block = Entity(
                        model='cube',
                        texture='white_cube',
                        color=color.green, 
                        position=(posX, 1.5, posZ), 
                        scale=(self.scale_factor, 3, self.scale_factor), 
                        collider='box'
                    )
                    self.entities.append(self.exit_block)
                    
                elif val == 0: # Empty path (Crystal spawn chance)
                    if (x > 2 or z > 2) and random.random() < 0.15: 
                        crystal = Entity(
                            model='sphere',
                            texture='white_cube',
                            color=color.cyan,
                            position=(posX, 1.5, posZ),
                            scale=0.4,
                            collider='box'
                        )
                        self.crystals.append(crystal)
                        self.entities.append(crystal)
                    
        # Reset player position to start point safely
        if self.player:
            self.player.position = Vec3(2.1, 0, 1.8)
            self.player.rotation = Vec3(0, 0, 0)
        
        self.level_text.text = f'Level: {idx + 1} / {len(self.LEVELS)}'

    # =========================================================================
    # CORE ENGINE UPDATE LOOP
    # =========================================================================
    def update(self):
        if self.destroyed or self.game_over: return
        
        # Smooth UI pops using safe vector lerping
        current_scale = self.score_text.scale if isinstance(self.score_text.scale, Vec3) else Vec3(self.score_text.scale, self.score_text.scale, self.score_text.scale)
        self.score_text.scale = lerp(current_scale, self.score_pop_target, time.dt * 10)

        # Transition Timer System
        if self.transitioning:
            self.transition_timer -= time.dt
            if self.transition_timer <= 0:
                self.load_level(self.current_level_idx)
            return 

        # --- ANIMATIONS ---
        if self.exit_block:
            self.exit_block.rotation_y += 30 * time.dt
            self.exit_block.scale_y = 3 + math.sin(time.time() * 5) * 0.2
            
        # Rotate crystals and perform manual distance check
        for crystal in self.crystals[:]:
            crystal.rotation_y += 50 * time.dt
            crystal.y = 1.5 + math.sin(time.time() * 3 + crystal.x) * 0.2 
            
            # Crystal collection
            if self.player and distance(self.player.position, crystal.position) < 1.5:
                if crystal in self.crystals: self.crystals.remove(crystal)
                if crystal in self.entities: self.entities.remove(crystal)
                destroy(crystal)
                
                self.score += 10
                self.score_text.text = f'Score: {self.score}'
                # Trigger smooth score popup animation vector
                self.score_text.scale = Vec3(2.5, 2.5, 2.5)
                self.score_pop_target = Vec3(1.5, 1.5, 1.5)

        # --- SPRINT & STAMINA SYSTEM ---
        if self.player:
            if held_keys['shift']:
                if self.current_stamina > 0:
                    self.player.speed = 12
                    self.current_stamina -= 30 * time.dt 
                    self.stamina_bar.color = color.orange
            else:
                self.player.speed = 6
                if self.current_stamina < self.max_stamina:
                    self.current_stamina += 15 * time.dt 
                    self.stamina_bar.color = color.green
                
        # Update Stamina UI Bar rendering
        self.current_stamina = clamp(self.current_stamina, 0, self.max_stamina)
        stamina_ratio = self.current_stamina / self.max_stamina
        self.stamina_bar.scale_x = 0.39 * stamina_ratio
        self.stamina_bar.x = self.stamina_bg.x - (0.39 - self.stamina_bar.scale_x) / 2 

        # --- LEVEL COMPLETION LOGIC ---
        if self.exit_block and self.player and distance(self.player.position, self.exit_block.position) < 2.6:
            self.current_level_idx += 1
            
            if self.current_level_idx < len(self.LEVELS):
                self.win_text.text = f'Level {self.current_level_idx} Cleared!'
                self.win_text.color = color.green
                self.transitioning = True
            else:
                self.game_over = True
                self.win_text.text = f'VICTORY!\nFinal Score: {self.score}'
                self.win_text.color = color.gold
                self.player.disable() 

    # =========================================================================
    # THE FIRST PERSON CONTROLLER TEARDOWN
    # =========================================================================
    def destroy(self):
        if self.destroyed:
            return

        self.destroyed = True
        self.game_over = True
        self.transitioning = False

        # Stop controller first
        if self.player:
            player = self.player
            self.player = None
            player.enabled = False
            destroy(player)

        # Restore global mouse state
        mouse.locked = False
        mouse.visible = True

        # Destroy maze entities
        for entity in self.entities.copy():
            destroy(entity)

        self.entities.clear()
        self.maze_blocks.clear()
        self.crystals.clear()
        self.exit_block = None

        # Destroy UI
        for ui in self.ui_elements.copy():
            destroy(ui)

        self.ui_elements.clear()

        # Restore camera
        camera.parent = self.old_camera_parent
        camera.position = self.old_camera_position
        camera.rotation = self.old_camera_rotation
        camera.fov = self.old_camera_fov

        # Restore fog
        scene.fog_color = self.old_fog_color
        scene.fog_density = self.old_fog_density