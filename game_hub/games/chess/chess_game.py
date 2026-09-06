from ursina import *
import math
import random
import time as pytime

class ChessGame:
    """
    ChessGame is a gameclass object which runs very simple 2 player chess game.
    Details:
    this has blue and a red side name text for every cube which are the pieces.
    It is mainly focused on laws of chess and the movement of pieces. It has a check and checkmate detection system.
    """

    # =========================================================================
    # TILE CLASS
    # =========================================================================
    class Tile(Button):
        def __init__(self, game, x, z, tile_color):
            self.game = game
            self.board_x = x
            self.board_z = z
            self.original_color = tile_color

            super().__init__(
                parent=scene,
                position=(x, 0, z),
                model='cube',
                texture='white_cube',
                scale=(1, 0.1, 1),
                color=tile_color,
                collider='box'
            )

        def input(self, key):
            if self.game.game_over:
                return

            if self.hovered and key == 'left mouse down':
                if not self.game.selected_piece:
                    return

                # Build legal move list
                valid_moves = []
                for move in self.game.selected_piece.get_valid_moves():
                    if not self.game.move_puts_king_in_check(self.game.selected_piece, move[0], move[1]):
                        valid_moves.append(move)

                # Not a legal move
                if (self.board_x, self.board_z) not in valid_moves:
                    return

                # Destination piece
                target = self.game.get_piece_at(self.board_x, self.board_z)

                # Cannot capture own piece
                if target and target.piece_color == self.game.selected_piece.piece_color:
                    return

                # Save original position
                old_x = self.game.selected_piece.board_x
                old_z = self.game.selected_piece.board_z

                # Capture enemy piece
                if target and target.piece_color != self.game.selected_piece.piece_color:
                    if target in self.game.pieces:
                        self.game.pieces.remove(target)
                    destroy(target)

                # Move selected piece
                self.game.selected_piece.position = (self.board_x, 0.6, self.board_z)
                self.game.selected_piece.board_x = self.board_x
                self.game.selected_piece.board_z = self.board_z
                self.game.selected_piece.has_moved = True

                # ------------------------
                # PAWN PROMOTION
                # ------------------------
                if (
                    self.game.selected_piece.piece_type == "pawn"
                    and (self.game.selected_piece.board_z == 7 or self.game.selected_piece.board_z == 0)
                ):
                    self.game.selected_piece.piece_type = "queen"
                    self.game.selected_piece.text_entity.text = "Q"

                # ------------------------
                # CASTLING (O-O / O-O-O)
                # ------------------------
                if self.game.selected_piece.piece_type == "king" and abs(self.board_x - old_x) == 2:
                    # KING SIDE (O-O)
                    if self.board_x == 6:
                        rook = self.game.get_piece_at(7, self.game.selected_piece.board_z)
                        if rook:
                            rook.board_x = 5
                            rook.position = (5, 0.6, self.game.selected_piece.board_z)
                            rook.has_moved = True

                    # QUEEN SIDE (O-O-O)
                    elif self.board_x == 2:
                        rook = self.game.get_piece_at(0, self.game.selected_piece.board_z)
                        if rook:
                            rook.board_x = 3
                            rook.position = (3, 0.6, self.game.selected_piece.board_z)
                            rook.has_moved = True

                # Restore piece color
                self.game.selected_piece.color = (
                    color.cyan
                    if self.game.selected_piece.piece_color == 'white'
                    else color.red
                )

                self.game.clear_highlights()

                # Check and Checkmate detection
                white_in_check = self.game.is_king_in_check("white")
                black_in_check = self.game.is_king_in_check("black")
                white_checkmate = self.game.is_checkmate("white")
                black_checkmate = self.game.is_checkmate("black")

                if white_checkmate:
                    self.game.is_check.text = "CHECKMATE! BLACK WINS"
                    self.game.is_check.enabled = True
                    self.game.highlight_king("white", True, True)
                elif white_in_check:
                    self.game.is_check.text = "WHITE KING IS IN CHECK"
                    self.game.is_check.enabled = True
                    self.game.highlight_king("white", True)
                else:
                    self.game.highlight_king("white", False)

                if black_checkmate:
                    self.game.is_check.text = "CHECKMATE! WHITE WINS"
                    self.game.is_check.enabled = True
                    self.game.highlight_king("black", True, True)
                elif black_in_check:
                    self.game.is_check.text = "BLACK KING IS IN CHECK"
                    self.game.is_check.enabled = True
                    self.game.highlight_king("black", True)
                else:
                    self.game.highlight_king("black", False)

                if not white_in_check and not black_in_check:
                    self.game.is_check.enabled = False

                self.game.selected_piece = None

    # =========================================================================
    # CHESS PIECE CLASS
    # =========================================================================
    class ChessPiece(Button):
        def __init__(self, game, piece_type, piece_color, x, z):
            self.game = game
            self.piece_type = piece_type
            self.piece_color = piece_color
            self.board_x = x
            self.board_z = z
            self.has_moved = False

            super().__init__(
                parent=scene,
                position=(x, 0.6, z),
                model='cube',
                texture='white_cube',
                scale=(0.7, 1.0, 0.7),
                color=color.cyan if piece_color == 'white' else color.red,
                collider='box'
            )

            self.text_entity = Text(
                text=piece_type[0].upper() if piece_type != "knight" else "N",
                parent=self,
                y=1.3,
                scale=5,
                billboard=True
            )

        def input(self, key):
            if self.game.game_over:
                return

            if self.hovered and key == 'left mouse down':
                if self.game.selected_piece:
                    self.game.selected_piece.color = (
                        color.cyan
                        if self.game.selected_piece.piece_color == 'white'
                        else color.red
                    )

                self.game.selected_piece = self
                self.color = color.yellow
                self.game.show_valid_moves(self)

        def get_valid_moves(self):
            moves = []

            # ==================================================
            # PAWN
            # ==================================================
            if self.piece_type == "pawn":
                if self.piece_color == "white":
                    direction = 1
                    start_row = 1
                else:
                    direction = -1
                    start_row = 6

                # Forward 1
                if self.game.get_piece_at(self.board_x, self.board_z + direction) is None:
                    moves.append((self.board_x, self.board_z + direction))

                    # Forward 2
                    if self.board_z == start_row:
                        if self.game.get_piece_at(self.board_x, self.board_z + direction * 2) is None:
                            moves.append((self.board_x, self.board_z + direction * 2))

                # Capture left
                target = self.game.get_piece_at(self.board_x - 1, self.board_z + direction)
                if target and target.piece_color != self.piece_color:
                    moves.append((self.board_x - 1, self.board_z + direction))

                # Capture right
                target = self.game.get_piece_at(self.board_x + 1, self.board_z + direction)
                if target and target.piece_color != self.piece_color:
                    moves.append((self.board_x + 1, self.board_z + direction))

                return moves

            # ==================================================
            # ROOK
            # ==================================================
            if self.piece_type == "rook":
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                for dx, dz in directions:
                    x = self.board_x + dx
                    z = self.board_z + dz
                    while 0 <= x < 8 and 0 <= z < 8:
                        target = self.game.get_piece_at(x, z)
                        if target is None:
                            moves.append((x, z))
                        else:
                            if target.piece_color != self.piece_color:
                                moves.append((x, z))
                            break
                        x += dx
                        z += dz
                return moves

            # ==================================================
            # KNIGHT
            # ==================================================
            if self.piece_type == "knight":
                knight_moves = [
                    (2, 1), (2, -1), (-2, 1), (-2, -1),
                    (1, 2), (1, -2), (-1, 2), (-1, -2)
                ]
                for dx, dz in knight_moves:
                    x = self.board_x + dx
                    z = self.board_z + dz
                    if 0 <= x < 8 and 0 <= z < 8:
                        target = self.game.get_piece_at(x, z)
                        if target is None or target.piece_color != self.piece_color:
                            moves.append((x, z))
                return moves

            # ==================================================
            # BISHOP
            # ==================================================
            if self.piece_type == "bishop":
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                for dx, dz in directions:
                    x = self.board_x + dx
                    z = self.board_z + dz
                    while 0 <= x < 8 and 0 <= z < 8:
                        target = self.game.get_piece_at(x, z)
                        if target is None:
                            moves.append((x, z))
                        else:
                            if target.piece_color != self.piece_color:
                                moves.append((x, z))
                            break
                        x += dx
                        z += dz
                return moves

            # ==================================================
            # QUEEN
            # ==================================================
            if self.piece_type == "queen":
                directions = [
                    (1, 0), (-1, 0), (0, 1), (0, -1),
                    (1, 1), (1, -1), (-1, 1), (-1, -1)
                ]
                for dx, dz in directions:
                    x = self.board_x + dx
                    z = self.board_z + dz
                    while 0 <= x < 8 and 0 <= z < 8:
                        target = self.game.get_piece_at(x, z)
                        if target is None:
                            moves.append((x, z))
                        else:
                            if target.piece_color != self.piece_color:
                                moves.append((x, z))
                            break
                        x += dx
                        z += dz
                return moves

            # ==================================================
            # KING
            # ==================================================
            if self.piece_type == "king":
                king_moves = [
                    (-1, -1), (-1, 0), (-1, 1),
                    (0, -1),           (0, 1),
                    (1, -1),  (1, 0),  (1, 1)
                ]
                enemy_color = "black" if self.piece_color == "white" else "white"

                for dx, dz in king_moves:
                    x = self.board_x + dx
                    z = self.board_z + dz
                    if not (0 <= x < 8 and 0 <= z < 8):
                        continue

                    target = self.game.get_piece_at(x, z)
                    if target and target.piece_color == self.piece_color:
                        continue

                    if self.game.square_is_attacked(x, z, enemy_color):
                        continue

                    moves.append((x, z))

                # ------------------------
                # KINGSIDE CASTLING (O-O)
                # ------------------------
                if not self.has_moved:
                    rook = self.game.get_piece_at(7, self.board_z)
                    if (
                        rook
                        and rook.piece_type == "rook"
                        and rook.piece_color == self.piece_color
                        and not rook.has_moved
                    ):
                        # Squares between king and rook must be empty
                        if (
                            self.game.get_piece_at(5, self.board_z) is None
                            and self.game.get_piece_at(6, self.board_z) is None
                        ):
                            # King may not castle out of, through, or into check
                            if (
                                not self.game.square_is_attacked(4, self.board_z, enemy_color)
                                and not self.game.square_is_attacked(5, self.board_z, enemy_color)
                                and not self.game.square_is_attacked(6, self.board_z, enemy_color)
                            ):
                                moves.append((6, self.board_z))

                # ------------------------
                # QUEENSIDE CASTLING (O-O-O)
                # ------------------------
                if not self.has_moved:
                    rook = self.game.get_piece_at(0, self.board_z)
                    if (
                        rook
                        and rook.piece_type == "rook"
                        and rook.piece_color == self.piece_color
                        and not rook.has_moved
                    ):
                        # Squares between king and rook must be empty
                        if (
                            self.game.get_piece_at(1, self.board_z) is None
                            and self.game.get_piece_at(2, self.board_z) is None
                            and self.game.get_piece_at(3, self.board_z) is None
                        ):
                            # King may not pass through check
                            if (
                                not self.game.square_is_attacked(4, self.board_z, enemy_color)
                                and not self.game.square_is_attacked(3, self.board_z, enemy_color)
                                and not self.game.square_is_attacked(2, self.board_z, enemy_color)
                            ):
                                moves.append((2, self.board_z))
                return moves

            # TEMPORARY FALLBACK
            for x in range(8):
                for z in range(8):
                    moves.append((x, z))
            return moves

        def get_attack_squares(self):
            attacks = []

            # PAWN
            if self.piece_type == "pawn":
                direction = 1 if self.piece_color == "white" else -1
                for dx in (-1, 1):
                    x = self.board_x + dx
                    z = self.board_z + direction
                    if 0 <= x < 8 and 0 <= z < 8:
                        attacks.append((x, z))
                return attacks

            # KNIGHT
            if self.piece_type == "knight":
                knight_moves = [
                    (2, 1), (2, -1),
                    (-2, 1), (-2, -1),
                    (1, 2), (1, -2),
                    (-1, 2), (-1, -2)
                ]
                for dx, dz in knight_moves:
                    x = self.board_x + dx
                    z = self.board_z + dz
                    if 0 <= x < 8 and 0 <= z < 8:
                        attacks.append((x, z))
                return attacks

            # KING
            if self.piece_type == "king":
                king_moves = [
                    (-1, -1), (-1, 0), (-1, 1),
                    (0, -1),           (0, 1),
                    (1, -1),  (1, 0),  (1, 1)
                ]
                for dx, dz in king_moves:
                    x = self.board_x + dx
                    z = self.board_z + dz
                    if 0 <= x < 8 and 0 <= z < 8:
                        attacks.append((x, z))
                return attacks

            # ROOK / BISHOP / QUEEN
            directions = []
            if self.piece_type == "rook":
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            elif self.piece_type == "bishop":
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            elif self.piece_type == "queen":
                directions = [
                    (1, 0), (-1, 0), (0, 1), (0, -1),
                    (1, 1), (1, -1), (-1, 1), (-1, -1)
                ]

            for dx, dz in directions:
                x = self.board_x + dx
                z = self.board_z + dz
                while 0 <= x < 8 and 0 <= z < 8:
                    attacks.append((x, z))
                    if self.game.get_piece_at(x, z):
                        break
                    x += dx
                    z += dz

            return attacks


    # =========================================================================
    # CHESS GAME INITIALIZATION
    # =========================================================================
    def __init__(self):
        # Collections to keep track of created entities for proper cleanup
        self.entities = []
        self.ui_elements = []
        self.board_tiles = {}
        self.pieces = []
        self.highlighted_tiles = []
        self.selected_piece = None
        self.game_over = False

        # Apply specific camera setup
        camera.parent = scene
        camera.position = (9.18558, 6.4944076, 3.7689738)
        camera.rotation_y = -89.66604614257812
        camera.rotation_x = 52.518341064453125
        camera.orthographic = False
        camera.fov = 90

        # # Create lighting
        # self.dir_light = DirectionalLight()
        # self.amb_light = AmbientLight(color=color.rgba(150, 150, 150, 1))
        # self.entities.extend([self.dir_light, self.amb_light])

        # Create Check notification display text
        self.is_check = Text(
            text="",
            parent=scene,
            position=(0, 0.5, 0),
            scale=2,
            enabled=False
        )
        self.ui_elements.append(self.is_check)

        # ---------------------------------
        # GENERATE BOARD TILES
        # ---------------------------------
        for x in range(8):
            for z in range(8):
                tile_color = color.white if (x + z) % 2 == 0 else color.black
                tile = self.Tile(self, x, z, tile_color)
                self.board_tiles[(x, z)] = tile
                self.entities.append(tile)

        # ---------------------------------
        # GENERATE CHESS PIECES
        # ---------------------------------
        # White backend layout
        white_back_row = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        for x, piece_name in enumerate(white_back_row):
            wp = self.ChessPiece(self, piece_name, "white", x, 0)
            self.pieces.append(wp)
            self.entities.append(wp)

        for x in range(8):
            wp = self.ChessPiece(self, "pawn", "white", x, 1)
            self.pieces.append(wp)
            self.entities.append(wp)

        # Black backend layout
        black_back_row = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        for x, piece_name in enumerate(black_back_row):
            bp = self.ChessPiece(self, piece_name, "black", x, 7)
            self.pieces.append(bp)
            self.entities.append(bp)

        for x in range(8):
            bp = self.ChessPiece(self, "pawn", "black", x, 6)
            self.pieces.append(bp)
            self.entities.append(bp)

    # =========================================================================
    # BOARD LOOKUPS & RULE VERIFICATION
    # =========================================================================
    def get_piece_at(self, x, z):
        for piece in self.pieces:
            if piece.board_x == x and piece.board_z == z:
                return piece
        return None

    def clear_highlights(self):
        for tile in self.highlighted_tiles:
            tile.color = tile.original_color
        self.highlighted_tiles.clear()

    def show_valid_moves(self, piece):
        self.clear_highlights()
        if not self.game_over:
            for move in piece.get_valid_moves():
                if self.move_puts_king_in_check(piece, move[0], move[1]):
                    continue

                tile = self.board_tiles.get(move)
                if tile:
                    tile.color = color.green
                    self.highlighted_tiles.append(tile)

    def get_king(self, color_val):
        for piece in self.pieces:
            if piece.piece_type == "king" and piece.piece_color == color_val:
                return piece
        return None

    def is_king_in_check(self, king_color):
        king = self.get_king(king_color)
        if not king:
            return False

        king_pos = (king.board_x, king.board_z)

        for piece in self.pieces:
            if piece.piece_color == king_color:
                continue

            if king_pos in piece.get_attack_squares():
                return True
        return False

    def is_checkmate(self, king_color):
        if not self.is_king_in_check(king_color):
            return False

        # Try every piece of that color
        for piece in self.pieces:
            if piece.piece_color != king_color:
                continue

            # Try every move that piece can make
            for move in piece.get_valid_moves():
                if not self.move_puts_king_in_check(piece, move[0], move[1]):
                    return False
        return True

    def square_is_attacked(self, x, z, by_color):
        for piece in self.pieces:
            if piece.piece_color != by_color:
                continue
            if (x, z) in piece.get_attack_squares():
                return True
        return False

    def move_puts_king_in_check(self, piece, target_x, target_z):
        old_x = piece.board_x
        old_z = piece.board_z

        captured_piece = self.get_piece_at(target_x, target_z)

        if captured_piece:
            if captured_piece in self.pieces:
                self.pieces.remove(captured_piece)

        piece.board_x = target_x
        piece.board_z = target_z

        in_check = self.is_king_in_check(piece.piece_color)

        piece.board_x = old_x
        piece.board_z = old_z

        if captured_piece:
            self.pieces.append(captured_piece)

        return in_check

    # =========================================================================
    # ANIMATIONS AND EFFECTS
    # =========================================================================
    def destroy_king(self, king):
        if hasattr(king, "dead") and king.dead:
            return

        king.dead = True

        offsets = [
            (-0.25, 0, -0.25),
            ( 0.25, 0, -0.25),
            (-0.25, 0,  0.25),
            ( 0.25, 0,  0.25)
        ]

        chunks = []
        for ox, oy, oz in offsets:
            chunk = Entity(
                model='cube',
                texture='white_cube',
                color=king.color,
                position=king.position + Vec3(ox, oy, oz),
                scale=(0.35, 0.5, 0.35)
            )
            chunks.append(chunk)
            self.entities.append(chunk)

        if king.text_entity:
            destroy(king.text_entity)
        king.visible = False

        for i, chunk in enumerate(chunks):
            ox, oy, oz = offsets[i]
            chunk.animate_position(
                chunk.position + Vec3(ox * 3, 1.5, oz * 3),
                duration=0.8,
                curve=curve.out_expo
            )
            chunk.animate_rotation(
                (
                    random.uniform(200, 500),
                    random.uniform(200, 500),
                    random.uniform(200, 500)
                ),
                duration=0.8
            )
        
        if king in self.pieces:
            self.pieces.remove(king)
        destroy(king)
        self.game_over = True

    def highlight_king(self, color_name, danger=False, mate=False):
        king = self.get_king(color_name)
        if not king:
            return

        if mate:
            king.color = color.red
            self.destroy_king(king)
            return

        if danger:
            king.color = color.yellow
            king.scale = (0.8, 1.2, 0.8)
        else:
            king.color = color.cyan if color_name == "white" else color.red
            king.scale = (0.7, 1.0, 0.7)

    # =========================================================================
    # CORE ENGINE INTERFACE (INPUT, UPDATE & DESTROY)
    # =========================================================================
    def input(self, key):
        # Quick Camera Hotkeys
        if key == 'r':
            camera.position = (9.18558, 6.4944076, 3.7689738)
            camera.rotation_y = -90
            camera.rotation_x = 52.518341064453125
        elif key == 'h':
            camera.position = (3.5, 6.9457364, 9.406334)
            camera.rotation_y = -180
            camera.rotation_x = 51.788047790527344
        elif key == 'b':
            camera.position = (3.5, 6.8196425, -1.8307383)
            camera.rotation_y = -360
            camera.rotation_x = 55

        # Handle child key inputs manually since globals are gone
        for entity in self.entities:
            if hasattr(entity, 'input'):
                entity.input(key)

    def update(self):
        # Camera adjustments
        speed = 5 * time.dt
        if held_keys['w']:
            camera.z += speed
        if held_keys['s']:
            camera.z -= speed
        if held_keys['a']:
            camera.x -= speed
        if held_keys['d']:
            camera.x += speed
        if held_keys['u']:
            camera.y += speed
        if held_keys['o']:
            camera.y -= speed
        if held_keys['q']:
            camera.rotation_x -= 30 * time.dt
        if held_keys['e']:
            camera.rotation_x += 30 * time.dt
        if held_keys['c']:
            camera.rotation_y -= 30 * time.dt
        if held_keys['v']:
            camera.rotation_y += 30 * time.dt
        
        #print(f"Camera Position: {camera.position}, Rotation: ({camera.rotation_x}, {camera.rotation_y})")

        # Checked king warning pulsing effect
        t = pytime.time()
        for piece in self.pieces:
            if piece.piece_type == "king" and self.is_king_in_check(piece.piece_color):
                piece.color = color.color(1, 1, 0.5 + math.sin(t * 10) * 0.3)

    def destroy(self):
        """
        Cleans up and removes all Chess game elements.
        """
        self.game_over = True

        # Clear references
        self.pieces.clear()
        self.board_tiles.clear()
        self.highlighted_tiles.clear()
        self.selected_piece = None

        # Destroy all tracked game entities (including lights)
        for entity in self.entities.copy():
            destroy(entity)
        self.entities.clear()

        for ui in self.ui_elements.copy():
            destroy(ui)
        self.ui_elements.clear()

        # Restore default camera position
        camera.parent = scene
        camera.rotation_x = 0
        camera.rotation_y = 0
        camera.rotation_z = 0
        camera.position = (0, 0, -20)
        camera.orthographic = False
        camera.fov = 90
