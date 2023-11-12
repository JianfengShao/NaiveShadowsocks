import asyncio
from utils import config
from utils import cipher


class SecureSocket:
    def __init__(self, loop: asyncio.AbstractEventLoop, password):
        self.loop = loop
        self.cipher = cipher.Cipher.newCipher(password)

    async def read(self, sock):
        while True:
            data = await self.decodeRead(sock)
            if not data:
                break
            print(data)

    async def decodeRead(self, local_sock):
        data = await self.loop.sock_recv(local_sock, config.BUFFER_SIZE)
        bs = bytearray(data)
        self.cipher.decode(bs)

        return bs

    async def encodeWrite(self, remote_sock, data: bytes):
        bs = bytearray(data)
        self.cipher.encode(bs)

        await self.loop.sock_sendall(remote_sock, bs)

    async def encodeCopy(self, src_sock, dest_sock):
        print('\t- encodeCopy start {}:{} => {}:{}'.format(*src_sock.getsockname(), *dest_sock.getsockname()))
        while True:
            data = await self.loop.sock_recv(src_sock, config.BUFFER_SIZE)
            if not data:
                break
            await self.encodeWrite(dest_sock, data)
        print('\t- encodeCopy finished {}:{} => {}:{}'.format(*src_sock.getsockname(), *dest_sock.getsockname()))

    async def decodeCopy(self, src_sock, dest_sock):
        print('\t- decodeCopy start {}:{} => {}:{}'.format(*src_sock.getsockname(), *dest_sock.getsockname()))
        while True:
            bs = await self.decodeRead(src_sock)
            if not bs:
                break
            await self.loop.sock_sendall(dest_sock, bs)
        print('\t- decodeCopy start {}:{} => {}:{}'.format(*src_sock.getsockname(), *dest_sock.getsockname()))
