import atexit
import copy
import curses
import curses.textpad
import datetime
import math
import time

import constants
import game


class ui_manager():
    def cleanup(self):
        curses.endwin()

    def draw_board(self, top, board, hide_ships):
        if len(board.content) == 0:
            return

        start_row = self.rect_height + 1 if top else self.mid_row + 1
        board_width = len(board.content[0])
        for i, row in enumerate(board.content):
            start_x = self.mid_col - board_width
            representation = ' '.join(row).strip()

            # Auf dem gegnerischen Brett zeigen wir nur Treffer, leere Schüsse und Wasser an
            # Und verstecken alle noch nicht getroffenen Schiffe
            if hide_ships:
                representation = representation.replace(
                    game.tiles.ship, game.tiles.water)

            self.screen.addstr(start_row + i, start_x, representation)

    def find_empty_space(self, board_content, size):
        # Wir prüfen, ob es eine Reihe mit genug freien Feldern für unser Schiff gibt (horizontal)
        for row_idx, row_str in enumerate([''.join(r) for r in board_content]):
            if (idx := row_str.find(game.tiles.water * size)) != -1:
                return row_idx, idx, row_idx, idx + size - 1

        cols = [[row[i] for row in board_content]
                for i in range(len(board_content))]

        # Wir prüfen, ob es eine Spalte mit genug freien Feldern für unser Schiff gibt (vertikal)
        for col_idx, col_str in enumerate([''.join(r) for r in cols]):
            if (idx := col_str.find(game.tiles.water * size)) != -1:
                return idx, col_idx, idx + size - 1, col_idx

    def is_space_occupied(self, board, ship_tl_x, ship_tl_y, ship_br_x, ship_br_y):
        if len(board) == 0:
            return True

        width = len(board[0]) - 1
        height = len(board) - 1

        # min() und max() falls das Schiff "auf dem Kopf" steht
        min_y = min(ship_tl_y, ship_br_y)
        max_y = max(ship_tl_y, ship_br_y)

        min_x = min(ship_tl_x, ship_br_x)
        max_x = max(ship_tl_x, ship_br_x)

        # Überprüfen, ob die Indizes in unserem Brett liegen
        if any([v < 0 or v > height for v in [min_y, max_y]]) or any([v < 0 or v > width for v in [min_x, max_x]]):
            return True

        # Falls im Bereich des zu platzierenden Schiffs bereits ein Schiff existiert werten wir
        # die Stelle als "besetzt"
        if min_y == max_y and any([board[min_y][col] == game.tiles.ship for col in range(min_x, max_x + 1)]):
            return True
        elif any([board[row][min_x] == game.tiles.ship for row in range(min_y, max_y + 1)]):
            return True

        return False

    def move_ship(self, board, ship_tl_x, ship_tl_y, ship_br_x, ship_br_y, old=None, place=False):
        # Alte Position überschreiben
        if old is not None:
            min_y = min(old[1], old[3])
            max_y = max(old[1], old[3])

            min_x = min(old[0], old[2])
            max_x = max(old[0], old[2])

            if min_y == max_y:
                for col in range(min_x, max_x + 1):
                    board[min_y][col] = game.tiles.water
            else:
                for row in range(min_y, max_y + 1):
                    board[row][min_x] = game.tiles.water

        # min() und max() falls das Schiff "auf dem Kopf" steht
        # Wir ersetzen an jeder Position des Schiffs das Feld mit dem Wert Wasser durch ein neues Schiff
        min_y = min(ship_tl_y, ship_br_y)
        max_y = max(ship_tl_y, ship_br_y)

        min_x = min(ship_tl_x, ship_br_x)
        max_x = max(ship_tl_x, ship_br_x)

        # Falls place, dann platzieren wir das Schiff endgültig
        if min_y == max_y:
            for col in range(min_x, max_x + 1):
                board[min_y][col] = game.tiles.ship if place else game.tiles.new_ship
        else:
            for row in range(min_y, max_y + 1):
                board[row][min_x] = game.tiles.ship if place else game.tiles.new_ship

        return game.board(copy.deepcopy(board))

    def place_ships(self, game_ctx):
        self.screen.clear()

        ships = game_ctx.ships
        for ship_name, ship_data in ships.items():
            for count in range(ship_data['count']):
                game_ctx.desired_action = f'Platziere Schiff: {ship_name} [{count + 1}/{ship_data["count"]}]'
                self.screen.clear()
                self.draw_default(game_ctx)

                board_idx = game.players.host if game_ctx.is_host else game.players.guest

                ship_size = ship_data['size']

                curr_board = game_ctx.boards[board_idx]

                ship_tl_x, ship_tl_y, ship_br_x, ship_br_y = self.find_empty_space(
                    curr_board.content, ship_size)

                # Schiff an der ersten Position einsetzen
                game_ctx.boards[board_idx] = self.move_ship(
                    curr_board.content, ship_tl_x, ship_tl_y, ship_br_x, ship_br_y)
                self.screen.clear()
                self.draw_default(game_ctx)
                self.screen.refresh()

                while True:
                    old = [ship_tl_x, ship_tl_y, ship_br_x, ship_br_y]

                    inp = self.screen.getch()
                    curses.flushinp()

                    # Schiff wird platziert
                    # 10 = ASCII "\n" (Enter-Taste)
                    if inp == 10:
                        break
                    # Schiff drehen
                    elif inp == ord('r'):
                        # Mittelpunkt der alten Linie bestimmen
                        center_x = math.floor(
                            ((ship_tl_x + ship_br_x) // 2) - 0.001) + 1
                        center_y = math.floor(
                            ((ship_tl_y + ship_br_y) // 2) - 0.001) + 1

                        # Länge des Schiffs bestimmen
                        length = abs(
                            ship_br_y - ship_tl_y) if ship_tl_x == ship_br_x else abs(ship_br_x - ship_tl_x)

                        left = length // 2
                        right = left

                        # Beide Seiten sind nicht gleich lang, eine Seite ist länger
                        if length % 2 == 1:
                            right += 1

                        # Ist das alte Schiff vertikal -> Neue Linie horizontal
                        if ship_tl_x == ship_br_x:
                            line_tl_x = center_x - left
                            line_br_x = center_x + right
                            line_tl_y = center_y
                            line_br_y = center_y
                        else:
                            line_tl_y = center_y - left
                            line_br_y = center_y + right
                            line_tl_x = center_x
                            line_br_x = center_x

                        if not self.is_space_occupied(curr_board.content, line_tl_x, line_tl_y, line_br_x, line_br_y):
                            ship_tl_x = line_tl_x
                            ship_tl_y = line_tl_y
                            ship_br_x = line_br_x
                            ship_br_y = line_br_y

                    # Schiff nach oben verschieben
                    elif inp == ord('w'):
                        if not self.is_space_occupied(curr_board.content, ship_tl_x, ship_tl_y - 1, ship_br_x, ship_br_y - 1):
                            ship_tl_y -= 1
                            ship_br_y -= 1
                    # Schiff nach links verschieben
                    elif inp == ord('a'):
                        if not self.is_space_occupied(curr_board.content, ship_tl_x - 1, ship_tl_y, ship_br_x - 1, ship_br_y):
                            ship_tl_x -= 1
                            ship_br_x -= 1
                    # Schiff nach unten verschieben
                    elif inp == ord('s'):
                        if not self.is_space_occupied(curr_board.content, ship_tl_x, ship_tl_y + 1, ship_br_x, ship_br_y + 1):
                            ship_tl_y += 1
                            ship_br_y += 1
                    # Schiff nach rechts verschieben
                    elif inp == ord('d'):
                        if not self.is_space_occupied(curr_board.content, ship_tl_x + 1, ship_tl_y, ship_br_x + 1, ship_br_y):
                            ship_tl_x += 1
                            ship_br_x += 1
                    else:
                        continue

                    game_ctx.boards[board_idx] = self.move_ship(
                        curr_board.content, ship_tl_x, ship_tl_y, ship_br_x, ship_br_y, old)
                    self.screen.clear()
                    self.draw_default(game_ctx)
                    self.screen.refresh()
                game_ctx.boards[board_idx] = self.move_ship(
                    curr_board.content, ship_tl_x, ship_tl_y, ship_br_x, ship_br_y, old, True)
                self.screen.clear()
                self.draw_default(game_ctx)
                self.screen.refresh()

        return game_ctx

    def place_crosshair(self, board, nx, ny, old=None, save=False):
        if len(board) == 0 or len(old) == 0:
            return game.board([])

        x, y = None, None

        for row_idx, row_str in enumerate([''.join(r) for r in board]):
            if (idx := row_str.find(game.tiles.crosshair)) != -1:
                y, x = row_idx, idx
                break

        cols = [[row[i] for row in board]
                for i in range(len(board))]

        for col_idx, col_str in enumerate([''.join(r) for r in cols]):
            if (idx := col_str.find(game.tiles.crosshair)) != -1:
                y, x = idx, col_idx
                break

        board[ny][nx] = game.tiles.crosshair

        if x is not None and y is not None:
            board[y][x] = old[y][x]

        if save:
            board[ny][nx] = game.tiles.hit if board[ny][nx] == game.tiles.ship or board[ny][nx] == game.tiles.hit else game.tiles.blast

        return game.board(copy.deepcopy(board))

    def is_in_bounds(self, board, x, y):
        if len(board) == 0:
            return True

        width = len(board[0]) - 1
        height = len(board) - 1

        # Überprüfen, ob die Indizes in unserem Brett liegen
        return y < 0 or y > height or x < 0 or x > width

    def handle_shot(self, game_ctx):
        self.screen.clear()

        game_ctx.desired_action = f'Wähle Ziel'

        self.screen.clear()
        self.draw_default(game_ctx)
        self.screen.refresh()

        board_idx = game.players.guest if game_ctx.is_host else game.players.host

        old_board = copy.deepcopy(game_ctx.boards[board_idx].content)
        curr_board = copy.deepcopy(game_ctx.boards[board_idx].content)

        ch_x = 0
        ch_y = 0

        game_ctx.boards[board_idx] = self.place_crosshair(
            curr_board, ch_x, ch_y, old_board, False)
        self.screen.clear()
        self.draw_default(game_ctx)
        self.screen.refresh()

        while True:
            inp = self.screen.getch()
            curses.flushinp()

            # 10 = ASCII "\n" (Enter-Taste)
            if inp == 10:
                break
            # Schiff nach oben verschieben
            elif inp == ord('w') and not self.is_in_bounds(curr_board, ch_x, ch_y - 1):
                ch_y -= 1
            # Schiff nach links verschieben
            elif inp == ord('a') and not self.is_in_bounds(curr_board, ch_x - 1, ch_y):
                ch_x -= 1
            # Schiff nach unten verschieben
            elif inp == ord('s') and not self.is_in_bounds(curr_board, ch_x, ch_y + 1):
                ch_y += 1
            # Schiff nach rechts verschieben
            elif inp == ord('d') and not self.is_in_bounds(curr_board, ch_x + 1, ch_y):
                ch_x += 1
            else:
                continue

            game_ctx.boards[board_idx] = self.place_crosshair(
                curr_board, ch_x, ch_y, old_board, False)

            self.screen.clear()
            self.draw_default(game_ctx)
            self.screen.refresh()

        game_ctx.boards[board_idx] = self.place_crosshair(
            curr_board, ch_x, ch_y, old_board, True)
        game_ctx.moves.append(
            (game.players.host if game_ctx.is_host else game.players.guest, ch_x, ch_y, datetime.datetime.now()))

        self.screen.clear()
        self.draw_default(game_ctx)
        self.screen.refresh()

        return game_ctx

    def draw_text_large(self, text):
        text = text.split('\n')[1:-1]
        y, x = self.screen.getyx()

        start_row = y // 2
        start_col = x // 2  # - (len(text[0]) // 2)

        for i, row in enumerate(text):
            representation = ''.join(row).strip()

            self.screen.addstr(start_row + i, start_col, representation)
            time.sleep(2)
            self.screen.refresh()

    def draw_default(self, game_ctx):
        self.screen.border()

        self.screen.hline(self.mid_row, 0, '-', self.cols)

        curses.textpad.rectangle(
            self.screen, 0, self.mid_col - self.rect_width, self.rect_height, self.mid_col + self.rect_width)
        self.screen.addstr(1, self.mid_col -
                           self.rect_width + 1, f'battleship.py [{"Host" if game_ctx.is_host else "Gast"}]')

        self.screen.addstr(2, self.mid_col -
                           self.rect_width + 1, game_ctx.state)
        self.screen.addstr(3, self.mid_col - self.rect_width +
                           1, game_ctx.desired_action)
        self.screen.addstr(4, self.mid_col - self.rect_width +
                           1, game_ctx.phase)

        if game_ctx.phase in [game.game_phases.play_host, game.game_phases.play_guest]:
            board_idx = game.players.guest if game_ctx.is_host else game.players.host
            board = game_ctx.boards[board_idx]
            hit_count = board.get_hit_count()
            ship_count = board.get_ship_count()

            self.screen.addstr(4, self.mid_col - self.rect_width +
                               1, f'Felder mit Schiff: {hit_count}/{ship_count + hit_count} [x/s]')

        # Unser Brett wird immer unten dargestellt
        try:
            if game_ctx.is_host:
                self.draw_board(True, game_ctx.boards.get(
                    game.players.guest, game.board([])), True)

                self.draw_board(False, game_ctx.boards.get(
                    game.players.host, game.board([])), False)
            else:
                self.draw_board(True, game_ctx.boards.get(
                    game.players.host, game.board([])), True)

                self.draw_board(False, game_ctx.boards.get(
                    game.players.guest, game.board([])), False)
        except Exception as e:
            self.screen.refresh()
            print(e)
            time.sleep(200)

        if game_ctx.winner is not None:
            us = game.players.host if game_ctx.is_host else game.players.guest
            self.draw_text_large(
                constants.WINNER_TEXT if game_ctx.winner == us else constants.LOSER_TEXT)

    def draw(self, game_ctx):
        self.screen.clear()

        self.draw_default(game_ctx)

        self.screen.refresh()

    def __init__(self) -> None:
        self.screen = curses.initscr()
        curses.noecho()

        self.rows, self.cols = self.screen.getmaxyx()
        self.mid_col = self.cols // 2 + 1
        self.mid_row = self.rows // 2

        self.rect_height = 6
        self.rect_width = 20

        atexit.register(self.cleanup)
