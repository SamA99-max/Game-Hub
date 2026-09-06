



'''
main thing to strucure check bfore running the programm 
structure of files and folders should be like this (i have displayed it not in alphabetic order): 

game_hub/
│
├── main.py
├── No_Cache.gitignore
│
├── game_engine_core/
│   ├── __init__.py
│
├── games/
│   ├── __init__.py
│   │
|   ├── __pycache__/
│   │   └── __init__.cpython-311.pyc
|   |
│   ├── snake/
│   │   ├── __init__.py
│   │   └── snake_game.py
│   │
│   ├── parkour/
│   |   ├── __init__.py
│   |   ├── easy_parkour.py
│   |   ├── hard_parkour.py
|   |   └── gd_style_parkour.py
|   |
│   ├── minecraft/
|   |    ├── __init__.py
|   |    ├── minecraft_game.py          # main controller (ONLY orchestrates)
|   |    ├── player.py                  # FirstPersonController wrapper
|   |    ├── world.py                   # blocks, placement, terrain
|   |    ├── enemies.py                 # zombies/skeletons logic
|   |    ├── items.py                   # power cube, pickups
|   |    ├── fluids.py                 # lava/water systems
|   |    ├── ui.py                     # health bar, text, HUD
|   |    ├── save_system.py            # JSON save/load
|   |    ├── assets.py                 # central asset loader (sounds/models)
|   |    │
|   |    └── assets/
|   |        
|   ├── infinitecraft/
|   |    ├── __init__.py
|   |    └── minecraft_with_chunks.py
|   |
|   ├── space_shooter/
|   |    ├── __init__.py
|   |    └── space_shooter_game.py
|   |
│   ├── tic_tac_toe/
│   |   ├── __init__.py
│   |   └── tic_tac_toe_game.py
|   |
│   ├── tetris/
│   |   ├── __init__.py
│   |   └── tetris_game.py
|   |
│   ├── chess/
│   |   ├── __init__.py
│   |   └── chess_game.py
|   |
│   ├── pong/
│   |   ├── __init__.py
│   |   └── pong_game.py
|   |
│   ├── breakout/
│   |   ├── __init__.py
│   |   └── breakout_game.py
|   |
|   ├── pac_man/
│   |   ├── __init__.py
│   |   └── pac_man_game.py
|   |
|   ├── flappy_birds/
│   |   ├── __init__.py
│   |   └── flappy_birds_game.py
|   |
|   ├── dodge/
│   |   ├── __init__.py
│   |   └── dodge_game.py
|   |
|   └── maze/
|        ├── __init__.py
|        └── maze_game.py

'''

from ursina import *

from games.snake.snake_game import SnakeGame
from games.parkour.easy_parkour import EasyParkour
from games.parkour.hard_parkour import HardParkour
from games.minecraft.minecraft_game import MinecraftGame
from games.infinitecraft.minecraft_with_chunks import InfiniteCraft 
from games.tic_tac_toe.tic_tac_toe_game import TicTacToeGame
from games.space_shooter.space_shooter_game import SpaceShooter 
from games.tetris.tetris_game import TetrisGame
from games.chess.chess_game import ChessGame
from games.pong.pong_game import PongGame
from games.breakout.breakout_game import BreakoutGame
from games.parkour.gd_style_parkour import NeonCyberDash
from games.pac_man.pac_man_game import PacmanGame
from games.astroids.astroids_game import AsteroidsGame
from games.flappy_birds.flappy_birds_game import FlappyBirdGame
from games.dodge.dodge_game import DodgeGame
from games.maze.maze_game import MazeGame



app = Ursina(title= 'game hub', borderless=True, fullscreen=False, vsync=True, exit_button='escape', icon='icon.ico')


# ---------------- CURRENT GAME ----------------

current_game = None

# ---------------- MENUS ----------------

main_buttons = []
parkour_buttons = []
minecraft_buttons = []
state = 'main_menu'

# ---------------- CAMERA RESET ----------------

def reset_camera():
    camera.parent = scene
    camera.position = (0, 0, -20)
    camera.rotation = (0, 0, 0)
    camera.orthographic = False
    camera.fov = 90
    window.color = color.dark_gray


# ---------------- DESTROY CURRENT GAME ----------------

def destroy_current_game():

    global current_game

    if current_game:
        current_game.destroy()
        current_game = None
    

    reset_camera()


# ---------------- MAIN MENU ----------------

def show_main_menu():

    global state

    state = 'main_menu'

    reset_camera()

    snake_button = Button(
        text='Snake',
        scale=(0.3, 0.1),
        y=0.4,
        color=color.green
    )

    parkour_button = Button(
        text='Parkour',
        scale=(0.3, 0.1),
        y=0.2,
        color=color.azure
    )

    minecraft_button = Button(
        text='Minecraft',
        scale=(0.3, 0.1),
        y=0,
        color=color.hex("#724B1E")
    )
    
    tic_tac_toe_button = Button(
        text='Tic Tac Toe',
        scale=(0.3, 0.1),
        x=0.4,
        y=0.4,
        color=color.hex("#00FFD5")
    )
    
    space_shooter_button = Button(
        text='Space Shooter',
        scale=(0.3, 0.1),
        x=0.4,
        y=0.2,
        color=color.hex("#15008B")
    )
    
    tetris_button = Button(
        text='Tetris',
        scale=(0.3, 0.1),
        x=0.4,
        y=0,
        color=color.hex("#15B337")
    )

    chess_button = Button(
        text='Chess',
        scale=(0.3, 0.1),
        x=-0.4,
        y=0.4,
        color=color.hex("#8B4513")
    )

    pong_button = Button(
        text='Pong',
        scale=(0.3, 0.1),
        x=-0.4,
        y=0.2,
        color=color.hex("#FFD700")
    )

    breakout_button = Button(
        text='Breakout',
        scale=(0.3, 0.1),
        x=-0.4,
        y=0,
        color=color.hex("#FF4500")
    )

    pac_man_button = Button(
        text = 'Pac man',
        scale = (0.3, 0.1),
        x=-0.4,
        y=-0.2,
        color = color.hex("#30568F")
    )

    astroids_button = Button(
        text = 'astroids',
        scale = (0.3, 0.1),
        y = -0.2,
        color = color.hex("#0A0DC2")
    )

    flappy_birds_button = Button(
        text = 'Flappy Birds',
        scale = (0.3, 0.1),
        x = 0.4,
        y = -0.2,
        color = color.hex("#FF0000")
    )

    dodge_button = Button(
        text = 'Dodge',
        scale = (0.3, 0.1),
        y = -0.4,
        color = color.hex("#524B52")
    )

    maze_button = Button(
        text = 'Maze',
        scale = (0.3, 0.1),
        x = -0.4,
        y = -0.4,
        color = color.hex("#8B4513")
    )

    snake_button.on_click = start_snake
    parkour_button.on_click = show_parkour_menu
    minecraft_button.on_click = show_minecraft_world
    tic_tac_toe_button.on_click = start_tic_tac_toe
    space_shooter_button.on_click = start_space_shooter
    tetris_button.on_click = start_tetris
    chess_button.on_click = start_chess
    pong_button.on_click = start_pong
    breakout_button.on_click = start_breakout
    pac_man_button.on_click = start_pac_man
    astroids_button.on_click = start_astroids
    flappy_birds_button.on_click = start_flappy_birds
    dodge_button.on_click = start_dodge_game
    maze_button.on_click = start_maze

    main_buttons.extend([
        snake_button,
        parkour_button,
        minecraft_button,
        tic_tac_toe_button,
        space_shooter_button,
        tetris_button,
        chess_button,
        pong_button,
        breakout_button,
        pac_man_button,
        astroids_button,
        flappy_birds_button,
        dodge_button,
        maze_button
    ])


def hide_main_menu():

    for b in main_buttons.copy():
        destroy(b)

    main_buttons.clear()


# ---------------- PARKOUR MENU ----------------

def show_parkour_menu():

    global state

    hide_main_menu()

    state = 'parkour_menu'

    reset_camera()

    easy_button = Button(
        text='Easy Parkour',
        scale=(0.4, 0.1),
        y=0.15,
        color=color.lime
    )

    hard_button = Button(
        text='Hard Parkour',
        scale=(0.4, 0.1),
        y=0,
        color=color.orange
    )

    gd_button = Button(
        text='Gd Parkour(extreme hard and 2D)',
        scale=(0.4, 0.1),
        y=-0.15,
        color=color.hex("#0400FF")
    )

    back_button = Button(
        text='Back',
        scale=(0.25, 0.08),
        y=-0.35,
        color=color.red
    )


    easy_button.on_click = start_easy_parkour
    hard_button.on_click = start_hard_parkour
    back_button.on_click = back_to_main_menu
    gd_button.on_click = start_neon_cyber_dash

    parkour_buttons.extend([
        easy_button,
        hard_button,
        gd_button,
        back_button
    ])


def hide_parkour_menu():

    for b in parkour_buttons.copy():
        destroy(b)

    parkour_buttons.clear()


# ---------------- MINECRAFT MENU ----------------

def show_minecraft_world():

    global state

    hide_main_menu()

    state = 'minecraft_menu'

    reset_camera()

    classic_button = Button(
        text='Minecraft',
        scale=(0.4, 0.1),
        y=0.15,
        color=color.lime
    )

    infinite_button = Button(
        text='infinite Minecraft',
        scale=(0.4, 0.1),
        y=0,
        color=color.orange
    )

    back_button = Button(
        text='Back',
        scale=(0.25, 0.08),
        y=-0.2,
        color=color.red
    )

    classic_button.on_click = start_minecraft
    infinite_button.on_click = start_infinite_craft
    back_button.on_click = back_to_main_menu

    minecraft_buttons.extend([
        classic_button,
        infinite_button,
        back_button
    ])


def hide_minecraft_menu():

    for b in minecraft_buttons.copy():
        destroy(b)

    minecraft_buttons.clear()


# ---------------- START GAMES ----------------

def start_snake():

    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = SnakeGame()


def start_easy_parkour():

    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = EasyParkour()


def start_hard_parkour():

    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = HardParkour()


def start_minecraft():

    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'
    try:
        current_game = MinecraftGame()
    except Exception as e:
        print(f"Error starting Minecraft: {e}")
        back_to_main_menu()

def start_infinite_craft():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'
    try:
        current_game = InfiniteCraft()
    except Exception as e:
        print(f"Error starting InfiniteCraft: {e}")
        back_to_main_menu()

def start_tic_tac_toe():

    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = TicTacToeGame()

def start_space_shooter():

    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = SpaceShooter()

def start_tetris():
    global current_game, state
    destroy_current_game()
    
    hide_main_menu()
    hide_minecraft_menu()
    hide_parkour_menu()
    
    reset_camera()
    
    state = 'playing'
    
    current_game = TetrisGame()

def start_chess():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = ChessGame()

def start_pong():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = PongGame()

def start_breakout():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = BreakoutGame()

def start_neon_cyber_dash():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = NeonCyberDash()

def start_pac_man():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = PacmanGame()

def start_astroids():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = AsteroidsGame()

def start_flappy_birds():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = FlappyBirdGame()

def start_dodge_game():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = DodgeGame()

def start_maze():
    global current_game, state

    destroy_current_game()

    hide_main_menu()
    hide_parkour_menu()
    hide_minecraft_menu()

    reset_camera()

    state = 'playing'

    current_game = MazeGame()

# ---------------- BACK TO MAIN MENU ----------------

def back_to_main_menu():

    destroy_current_game()

    hide_parkour_menu()
    hide_main_menu()
    hide_minecraft_menu()

    show_main_menu()


# ---------------- UPDATE ----------------

def update():
    if current_game and hasattr(current_game, 'update'):
        current_game.update()


# ---------------- INPUT ----------------

def input(key):

    global current_game

    if key == 'escape':

        destroy_current_game()

        hide_main_menu()
        hide_parkour_menu()
        hide_minecraft_menu()

        show_main_menu()
        
        if hasattr(current_game, 'save_chunk_data'):
            current_game.save_chunk_data()

        return

    if current_game:
        if hasattr(current_game, 'input'):
            current_game.input(key)


# ---------------- START ----------------

reset_camera()
show_main_menu()

app.run()