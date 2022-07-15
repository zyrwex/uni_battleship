#!/usr/bin/python3

import argparse
import threading
import time

import boats
import constants
import game
import networking
import ui


def ranged_int(min_val, max_val):
    def int_range_checker(arg):
        try:
            val = int(arg)
        except ValueError:
            raise argparse.ArgumentTypeError('Nur ganze Zahlen erlaubt')
        if val not in range(min_val, max_val):
            raise argparse.ArgumentError(
                f'Die Eingabe muss im Intervall [{min_val}, ..., {max_val}] liegen')
        return val

    return int_range_checker


nw_mgr = networking.network_manager()


def main():
    global nw_mgr

    parser = argparse.ArgumentParser(
        description=constants.DESCRIPTION, epilog=constants.COPYRIGHT, add_help=False)

    parser.add_argument('-h', '--help', action='help',
                        default=argparse.SUPPRESS, help='Zeige diese Nachricht')
    parser.add_argument('-n', '--name', help='Name des Spielers',
                        default=constants.DEFAULT_PLAYER_NAME)
    # TODO: Zug-Countdown implementieren
    # parser.add_argument('-m', '--movecountdown',
    #                     help='Zufälliger Zug nach n Sekunden (default: %(default)s) [0=deaktiviert]', default=constants.MOVE_COUNTDOWN)
    parser.add_argument('-xaxis', type=ranged_int(constants.MIN_SIZE, constants.MAX_SIZE),
                        help='Höhe der X-Achse des Bretts', default=constants.DEFAULT_BOARD_SIZE)
    parser.add_argument('-yaxis', type=ranged_int(constants.MIN_SIZE, constants.MAX_SIZE),
                        help='Höhe der Y-Achse des Bretts', default=constants.DEFAULT_BOARD_SIZE)

    args = vars(parser.parse_args())

    def connect_nw_mgr(nw_mgr):
        nw_mgr.connect()

    connect_thread = threading.Thread(target=connect_nw_mgr, args=(nw_mgr,))
    connect_thread.start()

    first_connected = True

    try:
        ui_mgr = ui.ui_manager()
        while True:
            if nw_mgr.state == networking.network_states.error:
                ui_mgr.cleanup()
                break

            ctx = game.game_context(
                state=nw_mgr.state, desired_action='Warten...', ships=boats.BOATS, is_host=nw_mgr.is_host)

            if nw_mgr.state == networking.network_states.connected:
                if first_connected:
                    first_connected = False
                    connect_thread.join()
                    # Wir sind der Host, also setzen wir unser Brett zuerst auf
                    if nw_mgr.is_host:
                        def make_board():
                            board = []
                            for _ in range(args['yaxis']):
                                r = []
                                for _ in range(args['xaxis']):
                                    r.append(game.tiles.water)
                                board.append(r)
                            return board
                        ctx.boards = {k: game.board(
                            make_board()) for k in game.players}
                        ctx.phase = game.game_phases.setup_host

                        ctx = ui_mgr.place_ships(ctx)

                        ctx.phase = game.game_phases.setup_guest
                        ctx.desired_action = 'Warten...'
                        nw_mgr.send(ctx)
                else:
                    new_ctx = nw_mgr.receive()
                    if new_ctx is None:
                        ctx.state = networking.network_states.not_connected
                        ctx.desired_action = 'Netzwerkfehler'
                        ctx.phase = game.game_phases.ended
                    else:
                        ctx = new_ctx
                        if not nw_mgr.is_host and ctx.phase == game.game_phases.setup_guest:
                            ctx = ui_mgr.place_ships(ctx)

                            ctx.desired_action = 'Warten...'

                            ctx.phase = game.game_phases.play_host
                            nw_mgr.send(ctx)
                        elif new_ctx.phase == game.game_phases.ended:
                            ui_mgr.draw(ctx)
                        elif nw_mgr.is_host and new_ctx.phase == game.game_phases.play_host:
                            ctx = ui_mgr.handle_shot(ctx)
                            ctx.phase = game.game_phases.play_guest

                            if ctx.boards[game.players.guest].has_lost():
                                ctx.winner = game.players.host
                                ctx.desired_action = 'Spiel beendet'
                                ctx.phase = game.game_phases.ended

                            nw_mgr.send(ctx)
                        elif not nw_mgr.is_host and new_ctx.phase == game.game_phases.play_guest:
                            ui_mgr.draw(ctx)
                            ctx = ui_mgr.handle_shot(ctx)
                            ctx.phase = game.game_phases.play_host

                            if ctx.boards[game.players.host].has_lost():
                                ctx.winner = game.players.guest
                                ctx.desired_action = 'Spiel beendet'
                                ctx.phase = game.game_phases.ended

                            nw_mgr.send(ctx)
                        elif nw_mgr.is_host and new_ctx.phase == game.game_phases.play_guest:
                            ctx.desired_action = 'Warten...'
                        elif not nw_mgr.is_host and new_ctx.phase == game.game_phases.play_host:
                            ctx.desired_action = 'Warten...'

            ui_mgr.draw(ctx)
            time.sleep(0.5)
    except:
        pass

    return 0


if __name__ == '__main__':
    exit(main())
