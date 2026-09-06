from ursina import *
import random

class TicTacToeGame():
    '''
    TicTacToeGame is a simple tic-tac-toe game where the player can play against an AI opponent.
    '''

    def __init__(self):
        
        
        
        self.WINS = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]

        self.board = [" "] * 9
        self.buttons = []
        self.ui = []
        self.game_over = False
        self.ui.append(Sky(texture='sky_sunset'))  # add sky to UI for easy cleanup

        # ⭐ BIG WIN TEXT (very visible)
        self.win_text = Text(
            "",
            scale=4,
            origin=(0, 0),
            color=color.yellow,
            # background=True
        )
        self.win_text.position = (0, 0.35)
        self.ui.append(self.win_text)
        
        self.spacing = 0.18
        self.offset = 0.18
        self.grid_y_offset = 0.12  # adjust this value if you want higher/lower

        for i in range(9):
            btn = Button(
                text="",
                color=color.azure,
                scale=0.16,  # smaller squares = tighter look
                position=(
                    (i % 3 - 1) * self.spacing,
                    (1 - i // 3 - 1) * self.spacing + self.grid_y_offset
                ),
                highlight_color=color.cyan,
                pressed_color=color.white
            )
            btn.on_click = Func(self.on_click, i)
            self.buttons.append(btn)


        # RESET BUTTON (cleaner placement)
        self.ui.append(Button(
            text="RESET",
            color=color.lime,
            scale=(0.2, 0.08),
            position=(0, -0.4),
            on_click=self.reset_game
        ))

        
    def check_win(self, sym):
        return any(self.board[a] == self.board[b] == self.board[c] == sym for a, b, c in self.WINS)
    
    def reset_game(self):
        self.board = [" "] * 9
        self.game_over = False
        self.win_text.text = ""

        for b in self.buttons:
            b.text = ""
            b.color = color.azure
    
    def ai_move(self):
        self.moves = [i for i in range(9) if self.board[i] == " "]

        # try win
        for m in self.moves:
            self.board[m] = "O"
            if self.check_win("O"):
                return m
            self.board[m] = " "

        # try block
        for m in self.moves:
            self.board[m] = "X"
            if self.check_win("X"):
                self.board[m] = "O"
                return m
            self.board[m] = " "

        return random.choice(self.moves)
    
    def end_check(self):
        if self.check_win("X"):
            self.win_text.text = "YOU WIN!"
            self.win_text.color = color.lime
            self.game_over = True
            return True

        if self.check_win("O"):
            self.win_text.text = "AI WINS!"
            self.win_text.color = color.red
            self.game_over = True
            return True

        if " " not in self.board:
            self.win_text.text = "DRAW!"
            self.win_text.color = color.white
            self.game_over = True
            return True

        return False
    
    def on_click(self, i):
        if self.game_over or self.board[i] != " ":
            return

        self.board[i] = "X"
        self.buttons[i].text = "X"
        self.buttons[i].color = color.red

        if self.end_check():
            return

        ai = self.ai_move()
        self.board[ai] = "O"
        self.buttons[ai].text = "O"
        self.buttons[ai].color = color.orange

        self.end_check()

    def destroy(self):
        for b in self.buttons:
            destroy(b)
        for u in self.ui:
            destroy(u)
        self.buttons.clear()
        self.ui.clear()