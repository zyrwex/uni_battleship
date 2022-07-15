

import atexit
import dataclasses
import enum
import pickle
import socket

import constants


class network_states(str, enum.Enum):
    not_connected = 'Nicht verbunden'
    error = 'Fehler'
    server_started = 'Server gestartet'
    client_started = 'Client gestartet'
    connected = 'Verbunden'


@dataclasses.dataclass
class network_manager():
    sock: socket.socket = None
    client_sock: socket.socket = None
    state: str = network_states.not_connected
    is_host: bool = False
    initialized: bool = False

    def __init__(self) -> None:
        atexit.register(self.cleanup)

    def does_host_exist(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', constants.GAME_PORT))
            s.close()
            return False
        except:
            return True

    def connect(self):
        does_host_exist = self.does_host_exist()

        # Wenn sowohl Client als auch Host existieren läuft bereits ein Spiel
        self.is_host = not does_host_exist

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            if self.is_host:
                self.sock.bind(('127.0.0.1', constants.GAME_PORT))
                self.sock.listen()
                self.state = network_states.server_started
            else:
                self.sock.connect(('127.0.0.1', constants.GAME_PORT))
                self.state = network_states.client_started
        except Exception as e:
            self.state = network_states.error
            return

        if self.is_host:
            # Wir warten auf eine Verbindung vom Client
            while True:
                (client_sock, client_addr) = self.sock.accept()
                self.client_sock = client_sock
                self.state = network_states.connected
                break

        self.state = network_states.connected

    def cleanup(self):
        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_WR)
                self.sock.close()
            except:
                pass
        if self.client_sock is not None:
            try:
                self.client_sock.shutdown(socket.SHUT_WR)
                self.client_sock.close()
            except:
                pass

    def receive(self):
        sock = self.client_sock if self.is_host else self.sock

        data = sock.recv(constants.MAX_RECV)

        # Socket timeout
        if data == b'':
            return None

        res = pickle.loads(data)
        res.is_host = self.is_host

        return res

    def send(self, data):
        sock = self.client_sock if self.is_host else self.sock

        data.is_host = self.is_host

        outstr = pickle.dumps(data)
        sock.send(outstr)
