import asyncio
import socket

from utils import config
from utils import securesocket


class NsServer:
    def __init__(self, listen_address):
        self.listen_address = listen_address
        self.loop = None
        self.secureSocket = None

    async def listen(self):
        self.loop = asyncio.get_running_loop()
        self.secureSocket = securesocket.SecureSocket(self.loop)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(self.listen_address)
            listener.listen(socket.SOMAXCONN)
            listener.setblocking(False)

            print('- Listen to %s:%d\n' % self.listen_address)

            while True:
                local_sock, address = await self.loop.sock_accept(listener)
                print('- Receive from %s:%d' % address)
                asyncio.create_task(self.handle(local_sock))

    async def handle(self, local_sock):
        def cleanUp(task):
            local_sock.close()
            print('- Finish connection')

        reflect = asyncio.create_task(self.secureSocket.read(local_sock))
        reflect.add_done_callback(cleanUp)


def run_server_service():
    listen_address = ("0.0.0.0", config.server_port)

    server = NsServer(listen_address)

    asyncio.run(server.listen())


def main():
    run_server_service()


if __name__ == "__main__":
    main()
