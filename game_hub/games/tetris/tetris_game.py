from ursina import *
import random


class TetrisGame:
    '''
    TetrisGame is a classic Tetris game where the player can move and rotate falling pieces
    The pieces fall down the grid and the player can move them left and right and rotate them
    '''

    def __init__(self):

        self.entities = []
        self.ui_elements = []
        self.ghost_blocks = []
        self.game_dead = False

        # ---------------- WINDOW ----------------

        window.color = color.black

        # ---------------- GRID ----------------

        self.GRID_WIDTH = 30
        self.GRID_HEIGHT = 20


        # ---------------- CAMERA ----------------

        camera.parent = scene
        camera.orthographic = True
        camera.position = (0,0,-30)
        camera.rotation = (0,0,0)
        camera.fov = 22



        # ---------------- BACKGROUND ----------------

        self.background = Entity(
            model='quad',
            scale=(100,100),
            position=(0,0,5),
            color=color.rgba(0,0,255,0.08)
        )

        self.ui_elements.append(self.background)



        # ---------------- GRID ----------------

        offset_x = -self.GRID_WIDTH/2
        offset_y = -self.GRID_HEIGHT/2


        for x in range(self.GRID_WIDTH+1):

            line = Entity(
                model=Mesh(
                    vertices=[
                        (offset_x+x, offset_y,-0.5),
                        (offset_x+x, offset_y+self.GRID_HEIGHT,-0.5)
                    ],
                    mode='line'
                ),
                color=color.rgba(255,255,255,0.2)
            )

            self.entities.append(line)



        for y in range(self.GRID_HEIGHT+1):

            line = Entity(
                model=Mesh(
                    vertices=[
                        (offset_x,offset_y+y,-0.5),
                        (offset_x+self.GRID_WIDTH,offset_y+y,-0.5)
                    ],
                    mode='line'
                ),
                color=color.rgba(255,255,255,0.2)
            )

            self.entities.append(line)



        # ---------------- UI ----------------


        self.title = Text(
            text="TETRIS",
            y=.4,
            origin=(0,0),
            scale=2
        )

        self.info = Text(
            text="PRESS ENTER",
            y=.3,
            origin=(0,0)
        )

        self.score_text = Text(
            text="Score: 0",
            position=(-.85,.45)
        )


        self.ui_elements += [
            self.title,
            self.info,
            self.score_text
        ]



        # ---------------- PIECES ----------------


        self.board = []

        self.current_piece = []

        self.piece_x = 0
        self.piece_y = 0


        self.timer = 0
        self.speed = .5

        self.score = 0

        self.started = False

        self.game_over = False
        self.locked_blocks = []
        self.clearing = False


        # Shapes

        self.shapes = [

            # I
            [
                [1,1,1,1]
            ],


            # O
            [
                [1,1],
                [1,1]
            ],


            # T
            [
                [0,1,0],
                [1,1,1]
            ],


            # L
            [
                [1,0],
                [1,0],
                [1,1]
            ],


            # Z
            [
                [1,1,0],
                [0,1,1]
            ]

        ]




    # ---------------- START ----------------


    def start_game(self):

        self.started=True
        self.game_over=False

        self.title.enabled=False
        self.info.enabled=False

        for b in self.locked_blocks:
            destroy(b)

        self.locked_blocks=[]

        self.score=0
        self.score_text.text="Score: 0"

        self.board=[]

        for y in range(self.GRID_HEIGHT):
            self.board.append(
                [0]*self.GRID_WIDTH
            )

        self.spawn_piece()



    # ---------------- CREATE BLOCK ----------------


    def make_block(self, x, y, col):

        # Flip Y for drawing (Tetris uses Y-down, Ursina uses Y-up)
        draw_y = y

        block = Entity(
            model='cube',
            scale=.95,
            color=col,
            position=(
                x - self.GRID_WIDTH/2 + .5,
                draw_y - self.GRID_HEIGHT/2 + .5,
                -1
            )
        )

        self.entities.append(block)
        return block





    # ---------------- NEW PIECE ----------------


    def spawn_piece(self):
        if not self.game_dead:
                
            self.current_shape = random.choice(self.shapes)

            # spawn near the TOP of the grid (Y-down logic)
            self.piece_x = self.GRID_WIDTH // 2 - len(self.current_shape[0]) // 2
            self.piece_y = self.GRID_HEIGHT - len(self.current_shape)

            self.draw_piece()
        else:
            return


    def draw_ghost(self):
        if not self.game_dead:
            # delete old ghost
            for b in self.ghost_blocks:
                destroy(b)
            self.ghost_blocks = []

            ghost_y = self.piece_y

            # simulate falling
            while self.valid(self.piece_x, ghost_y - 1):
                ghost_y -= 1

            # draw ghost at lowest position
            for y, row in enumerate(self.current_shape):
                for x, value in enumerate(row):
                    if value:

                        block = Entity(
                            model='cube',
                            scale=.95,
                            color=color.rgba(0, 0, 255, 0.4),  # transparent blue
                            position=(
                                self.piece_x + x - self.GRID_WIDTH/2 + .5,
                                ghost_y + y - self.GRID_HEIGHT/2 + .5,
                                -1.2
                            )
                        )

                        self.ghost_blocks.append(block)

    def draw_piece(self):

        for b in self.current_piece:
            destroy(b)


        self.current_piece=[]


        for y,row in enumerate(self.current_shape):

            for x,value in enumerate(row):

                if value:

                    block=self.make_block(self.piece_x + x, self.piece_y + y, color.azure)

                    self.current_piece.append(block)
                    
        self.draw_ghost()

               

    # ---------------- MOVE CHECK ----------------


    def valid(self, nx, ny):

        for y, row in enumerate(self.current_shape):
            for x, value in enumerate(row):
                if value:
                    px = nx + x
                    py = ny + y

                    # left/right bounds
                    if px < 0 or px >= self.GRID_WIDTH:
                        return False

                    # bottom/top bounds (Y-down: 0..GRID_HEIGHT-1)
                    if py < 0 or py >= self.GRID_HEIGHT:
                        return False

                    # collision with locked blocks
                    if self.board[py][px]:
                        return False

        return True



    def redraw_board(self):

        for b in self.locked_blocks:
            destroy(b)

        self.locked_blocks = []

        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):

                if self.board[y][x]:

                    draw_y = y

                    block = Entity(
                        model='cube',
                        scale=.95,
                        color=self.board[y][x],
                        position=(
                            x - self.GRID_WIDTH/2 + .5,
                            draw_y - self.GRID_HEIGHT/2 + .5,
                            -1
                        )
                    )

                    self.locked_blocks.append(block)

    # ---------------- LOCK ----------------


    def lock_piece(self):

        # store piece
        for y, row in enumerate(self.current_shape):
            for x, value in enumerate(row):
                if value:
                    px = self.piece_x + x
                    py = self.piece_y +y
                    if 0 <= py < self.GRID_HEIGHT:
                        self.board[py][px] = color.azure

        for block in self.current_piece:
            destroy(block)

        self.current_piece = []

        # reset flag
        self.clearing = False

        # clear
        self.clear_lines()

        # if clearing happened → we do "cascade frame"
        if self.clearing:
            self.redraw_board()

        # spawn next
        self.spawn_piece()

        if not self.valid(self.piece_x, self.piece_y):
            self.game_over = True
            self.started = False
            self.info.text = "GAME OVER\nPRESS ENTER"
            self.info.enabled = True
            self.title.enabled = True



    # ---------------- CLEAR LINES ----------------


    def clear_lines(self):

        rows_removed = 0

        # check from bottom to top (important!)
        y = 0
        while y < len(self.board):

            if 0 not in self.board[y]:
                # remove full row
                del self.board[y]
                rows_removed += 1
            else:
                y += 1

        # add empty rows at top
        for _ in range(rows_removed):
            self.board.append([0] * self.GRID_WIDTH)

        # score
        if rows_removed:
            self.score += rows_removed * 100
            self.score_text.text = f"Score: {self.score}"

        self.redraw_board()

    

    # ---------------- INPUT ----------------


    def input(self,key):


        if key=="enter" and not self.started:

            self.start_game()


        if not self.started:
            return



        if held_keys['left arrow']:
                
            if self.valid(
                self.piece_x-1,
                self.piece_y
            ):

                self.piece_x-=1
                self.draw_piece()



        if held_keys['right arrow']:

            if self.valid(
                self.piece_x+1,
                self.piece_y
            ):

                self.piece_x+=1
                self.draw_piece()



        if held_keys['down arrow']:

            if self.valid(
                self.piece_x,
                self.piece_y-1
            ):

                self.piece_y-=1
                self.draw_piece()



        if key == "space":

            rotated = [
                list(x)
                for x in zip(
                    *self.current_shape[::-1]
                )
            ]

            old = self.current_shape

            self.current_shape = rotated

            if not self.valid(
                self.piece_x,
                self.piece_y
            ):
                self.current_shape = old



            self.draw_piece()


    # ---------------- UPDATE ----------------


    def update(self):

        if not self.started:
            return
        if self.game_dead:
            return

        self.timer+=time.dt

        if self.timer>self.speed:
            self.timer=0

            if self.valid(self.piece_x, self.piece_y-1):
                self.piece_y-=1
                self.draw_piece()

            else:
                self.lock_piece()



    # ---------------- DESTROY ----------------


    def destroy(self):
        self.game_dead = True

        for e in self.entities:
            destroy(e)

        for u in self.ui_elements:
            destroy(u)

        for c in self.current_piece:
            destroy(c)

        for g in self.ghost_blocks:
            destroy(g)

        for b in self.locked_blocks:
            destroy(b)



# app = Ursina()

# game = TetrisGame()


# def update():
#     game.update()


# def input(key):
#     game.input(key)


# app.run()