
import dataclasses
import datetime
import enum

import networking


class tiles(str, enum.Enum):
    water = '~'
    ship = 's'
    blast = 'b'
    hit = 'x'
    new_ship = 'n'
    crosshair = '+'


@dataclasses.dataclass
class board:
    content: list[list[tiles]] = dataclasses.field(default_factory=list)

    def get_hit_count(self):
        return sum([row.count(tiles.hit) for row in self.content])

    def get_ship_count(self):
        return sum([row.count(tiles.ship) for row in self.content])

    def has_lost(self):
        for row in self.content:
            for col in row:
                if col == tiles.ship:
                    return False
        return True


class game_phases(str, enum.Enum):
    setup_host = 'Setup (Host)'
    setup_guest = 'Setup (Gast)'
    play_host = 'Gefecht (Host)'
    play_guest = 'Gefecht (Gast)'
    ended = 'Zu Ende'


class players(str, enum.Enum):
    __order__ = 'host guest'
    host = 'h'
    guest = 'g'


@dataclasses.dataclass
class game_context:
    # Name des Spielers -> Brett des Spielers
    boards: dict[str, board] = dataclasses.field(default_factory=dict)

    player_names: dict[players, str] = dataclasses.field(default_factory=dict)

    # Name des ziehenden Spielers
    next_move: players = players.host

    desired_action: str = ''

    is_host: bool = False

    winner: players = None

    # Liste aller Züge als Tupel der Form (Name des Spielers, Position X, Position Y, Datum + Uhrzeit)
    moves: list[tuple[players, int, int, datetime.datetime]
                ] = dataclasses.field(default_factory=list)

    state: str = networking.network_states.not_connected

    phase: game_phases = game_phases.setup_host

    ships: dict[str, dict[str, int]] = dataclasses.field(default_factory=dict)
