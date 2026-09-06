from ursina import *
import random

class SnakeGame:
    '''
    A simple Nokia-style snake like in the good ol' days!
    '''

    def __init__(self):

        # ---------------- ENTITY STORAGE ----------------

        self.entities = []
        self.ui_elements = []

        #------------------ WINDOW ----------------------

        window.color = color.black

        # ---------------- GRID SETTINGS ----------------

        self.GRID_WIDTH = 30
        self.GRID_HEIGHT = 20

        # ---------------- COLORS ----------------

        self.SNAKE_COLOR = color.green
        self.FOOD_COLOR = color.red
        self.GRID_COLOR = color.rgba(255, 255, 255, 0.2)
        self.HEAD_COLOR = color.olive

        # ---------------- CAMERA ----------------

        camera.parent = scene
        camera.orthographic = True
        camera.position = (0, 0, -30)
        camera.rotation = (0, 0, 0)
        camera.fov = 22
        
        # ---------------- BACKGROUND ----------------


        self.background = Entity(
            model='quad',
            scale=(100, 100),
            position=(0, 0, 5),
            color=color.rgba(0, 0, 255, 0.08)
        )

        self.entities.append(self.background)

        # ---------------- GRID LINES ----------------
        
        GRID_OFFSET_X = -self.GRID_WIDTH / 2
        GRID_OFFSET_Y = -self.GRID_HEIGHT / 2

        for x in range(self.GRID_WIDTH + 1):

            line = Entity(
                model=Mesh(
                    vertices=[
                        (GRID_OFFSET_X + x, GRID_OFFSET_Y, -0.5),
                        (GRID_OFFSET_X + x, GRID_OFFSET_Y + self.GRID_HEIGHT, -0.5)
                    ],
                    mode='line'
                ),
                color=self.GRID_COLOR
            )

            self.entities.append(line)
            
        # Horizontal lines
        for y in range(self.GRID_HEIGHT + 1):
            
            line = Entity(
                model=Mesh(
                    vertices=[
                        (GRID_OFFSET_X, GRID_OFFSET_Y + y, -0.5),
                        (GRID_OFFSET_X + self.GRID_WIDTH, GRID_OFFSET_Y + y, -0.5)
                    ],
                    mode='line'
                ),
                color=self.GRID_COLOR
            )
            
            self.entities.append(line)

        # ---------------- UI ELEMENTS ----------------
        
        self.title_text = Text(text='Choose Speed (1-5)',
            y=0.35,
            origin=(0, 0),
            scale=2,
            color=color.white)
        self.ui_elements.append(self.title_text)

        self.speed_text = Text(
            text='Current Speed: 10',
            y=0.25,
            origin=(0, 0),
            scale=1.5,
            color=color.azure)
        self.ui_elements.append(self.speed_text)

        self.info_text = Text(
            text='Press ENTER to Start',
            y=0.15,
            origin=(0, 0),
            scale=1.2,
            color=color.white)
        self.ui_elements.append(self.info_text)

        self.score_text = Text(
            text='Score: 0',
            position=(-0.85, 0.45),
            scale=1.2,
            color=color.white)
        self.ui_elements.append(self.score_text)
    
        self.game_over_text = Text(
            text='',
            origin=(0, 0),
            scale=2,
            color=color.red,
            enabled=False)
        self.ui_elements.append(self.game_over_text)

        # ---------------- GAME VARIABLES ----------------
        
        self.snake = []

        self.direction = Vec3(1, 0, 0)
        self.next_direction = Vec3(1, 0, 0)

        self.food = None

        self.snake_length = 1

        self.speed_value = 7
        self.game_speed = 0.1

        self.move_timer = 0

        self.game_started = False
        self.game_over = False

    def create_snake(self):

        head = Entity(
            model='cube',
            color=self.HEAD_COLOR,
            scale=0.95,
            position=(0.5, 0.5, -1)
        )

        self.snake = [head]

        self.entities.append(head)

    def spawn_food(self):

        if self.food:

            if self.food in self.entities:
                self.entities.remove(self.food)

            destroy(self.food)

        while True:

            x = random.randint(-self.GRID_WIDTH // 2, self.GRID_WIDTH // 2 - 1)
            y = random.randint(-self.GRID_HEIGHT // 2, self.GRID_HEIGHT // 2 - 1)

            occupied = False

            for segment in self.snake[:-1]:  # exclude head

                segment_x = int(segment.x - 0.5)
                segment_y = int(segment.y - 0.5)

                if segment_x == x and segment_y == y:
                    occupied = True
                    break

            if not occupied:
                break

        food = Entity(
            model='cube',
            color=self.FOOD_COLOR,
            scale=0.95,
            position=(x + 0.5, y + 0.5, -1)
        )
        self.food = food
        self.entities.append(food)

    def start_game(self):

        self.game_started = True
        self.game_over = False

        self.snake_length = 1

        self.direction = Vec3(1, 0, 0)
        self.next_direction = Vec3(1, 0, 0)

        self.game_speed = 1 / self.speed_value

        self.title_text.enabled = False
        self.speed_text.enabled = False
        self.info_text.enabled = False

        self.score_text.text = 'Score: 0'

        for segment in self.snake:

            if segment in self.entities:
                self.entities.remove(segment)

            destroy(segment)

        self.snake.clear()
        
        self.create_snake()
        self.spawn_food()

    def trigger_game_over(self):

        self.game_over = True

        self.game_over_text.text = f'GAME OVER\nScore: {self.snake_length - 1}'
        self.game_over_text.enabled = True

    def input(self, key):

        if key == 'escape':
            return
        if not self.game_started:
            if key == '1':
                self.speed_value = 2
            elif key == '2':
                self.speed_value = 6
            elif key == '3':
                self.speed_value = 10
            elif key == '4':
                self.speed_value = 14
            elif key == '5':
                self.speed_value = 18

            self.speed_text.text = f'Current Speed: {self.speed_value}'

            if key == 'enter':
                self.start_game()
                return

        if key == 'left arrow' and self.direction.x == 0:
            self.next_direction = Vec3(-1, 0, 0)
        elif key == 'right arrow' and self.direction.x == 0:
            self.next_direction = Vec3(1, 0, 0)
        elif key == 'up arrow' and self.direction.y == 0:
            self.next_direction = Vec3(0, 1, 0)
        elif key == 'down arrow' and self.direction.y == 0:
            self.next_direction = Vec3(0, -1, 0)

    def update(self):
            
        if not self.game_started or self.game_over:
            return

        self.move_timer += time.dt

        if self.move_timer < self.game_speed:
            return

        self.move_timer = 0

        self.direction = self.next_direction

        head = self.snake[-1]

        head_x = int(head.x - 0.5)
        head_y = int(head.y - 0.5)

        new_x = head_x + self.direction.x
        new_y = head_y + self.direction.y

        # ---------------- WRAP AROUND ----------------

        if new_x >= self.GRID_WIDTH // 2:
            new_x = -self.GRID_WIDTH // 2

        elif new_x < -self.GRID_WIDTH // 2:
            new_x = self.GRID_WIDTH // 2 - 1

        if new_y >= self.GRID_HEIGHT // 2:
            new_y = -self.GRID_HEIGHT // 2

        elif new_y < -self.GRID_HEIGHT // 2:
            new_y = self.GRID_HEIGHT // 2 - 1

        # ---------------- SELF COLLISION ----------------

        for segment in self.snake:

            segment_x = int(segment.x - 0.5)
            segment_y = int(segment.y - 0.5)

            if segment_x == int(new_x) and segment_y == int(new_y):
                self.trigger_game_over()
                return

        # ---------------- NEW HEAD ----------------

        # old head becomes body
        head.color = self.SNAKE_COLOR

        # create new head
        new_head = Entity(
            model='cube',
            color=self.HEAD_COLOR,
            scale=0.95,
            position=(new_x + 0.5, new_y + 0.5, -1)
            )
        
        self.snake.append(new_head)
        self.entities.append(new_head)

        # ---------------- REMOVE TAIL ----------------

        if len(self.snake) > self.snake_length:
            tail = self.snake.pop(0)
            if tail in self.entities:
                self.entities.remove(tail)

            destroy(tail)

        # ---------------- EAT FOOD ----------------

        food_x = int(self.food.x - 0.5)
        food_y = int(self.food.y - 0.5)

        if int(new_x) == food_x and int(new_y) == food_y:

            self.snake_length += 1

            self.score_text.text = f'Score: {self.snake_length - 1}'

            self.spawn_food()

    def destroy(self):

        for entity in self.entities.copy():
            destroy(entity)

        for ui in self.ui_elements.copy():
            destroy(ui)

        self.food = None
        self.snake.clear()
        self.entities.clear()
        self.ui_elements.clear()
        camera.parent = scene
        camera.rotation_x = 0
        camera.rotation_y = 0
        camera.rotation_z = 0
        camera.position = (0, 0, 0)
