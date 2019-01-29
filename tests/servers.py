import time
import socket
import multiprocessing as mp

class SimpleTCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.run = True
        self.sock = None
        self.main_handler = None
        self.client_handlers = {}

    def start_listening(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.main_handler = mp.Process(target=self.accept_client)
        self.main_handler.start()

    def accept_client(self):
        while self.run:
            client, addr = self.sock.accept()
            client_handler = mp.Process(target=self.handle_client, args=(client,))
            self.client_handlers[client] = client_handler
            client_handler.start()

    def handle_client(self, client):
        # Server will just close the connection after it opens it
        client.close()
        return

    def stop(self):
        self.run = False

    def terminate(self):
        self.run = False
        for client_handler in self.client_handlers:
            if client_handler.is_alive():
                client_handler.join(0)
        if not self.main_handler is None:
            self.main_handler.join(1)

        for client_handler in self.client_handlers:
            if client_handler.is_alive():
                client_handler.terminate()
        self.client_handlers = []
        if not self.main_handler is None:
            self.main_handler.terminate()
            self.main_handler = None
