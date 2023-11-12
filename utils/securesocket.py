import asyncio
from utils import config


class SecureSocket:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    async def read(self, sock):
        while True:
            data = await self.loop.sock_recv(sock, config.BUFFER_SIZE)
            if not data:
                break
            print(data)

    async def encodeCopy(self, app_sock, remote_sock):
        print('\t- encodeCopy start {}:{} => {}:{}'.format(*app_sock.getsockname(), *remote_sock.getsockname()))
        while True:
            data = await self.loop.sock_recv(app_sock, config.BUFFER_SIZE)
            if not data:
                break
            await self.loop.sock_sendall(remote_sock, data)
        print('\t- encodeCopy finished {}:{} => {}:{}'.format(*app_sock.getsockname(), *remote_sock.getsockname()))
