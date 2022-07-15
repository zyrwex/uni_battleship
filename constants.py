import datetime

COPYRIGHT = f'© {datetime.date.today().year} An Trinh  <an.trinh@web.de>'
DESCRIPTION = 'Schiffe versenken in der Shell'
DEFAULT_PLAYER_NAME = 'Spieler'
MOVE_COUNTDOWN = 0

MIN_SIZE = 8
MAX_SIZE = 20

DEFAULT_BOARD_SIZE = 12

GAME_PORT = 1337

MAX_RECV = 1024 * 1024

WINNER_TEXT = """

  ██████  ███████ ██     ██  ██████  ███    ██ ███    ██ ███████ ███    ██
 ██       ██      ██     ██ ██    ██ ████   ██ ████   ██ ██      ████   ██
 ██   ███ █████   ██  █  ██ ██    ██ ██ ██  ██ ██ ██  ██ █████   ██ ██  ██
 ██    ██ ██      ██ ███ ██ ██    ██ ██  ██ ██ ██  ██ ██ ██      ██  ██ ██
  ██████  ███████  ███ ███   ██████  ██   ████ ██   ████ ███████ ██   ████

"""

LOSER_TEXT = """

 ██    ██ ███████ ██████  ██       ██████  ██████  ███████ ███    ██
 ██    ██ ██      ██   ██ ██      ██    ██ ██   ██ ██      ████   ██
 ██    ██ █████   ██████  ██      ██    ██ ██████  █████   ██ ██  ██
  ██  ██  ██      ██   ██ ██      ██    ██ ██   ██ ██      ██  ██ ██
   ████   ███████ ██   ██ ███████  ██████  ██   ██ ███████ ██   ████

"""
