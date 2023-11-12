import asyncio
import socket

from utils import config
from utils import securesocket


class NsLocal:
    def __init__(self, listen_address, remote_address):
        self.listen_address = listen_address
        self.remote_address = remote_address
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
                app_sock, address = await self.loop.sock_accept(listener)
                print('- Receive from %s:%d' % address)
                asyncio.create_task(self.handle(app_sock))

    async def handle(self, app_sock):
        def cleanUp(task):
            app_sock.close()
            print('- Finish application connection')

        remote_sock = await self.dialRemote()
        reflect = asyncio.create_task(self.secureSocket.encodeCopy(app_sock, remote_sock))
        reflect.add_done_callback(cleanUp)

    async def dialRemote(self):
        """
        Create a socket that connects to the Remote Server.
        """
        try:
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.setblocking(False)
            await self.loop.sock_connect(remote_sock, self.remote_address)
        except Exception as err:
            raise ConnectionError('- 连接远程服务器 %s:%d 失败:\n- %r' % (*self.remoteAddr, err))
        return remote_sock


def run_local_service():
    listen_address = (config.local_ip, config.local_port)  # 本地监听端口
    remote_address = (config.server_ip, config.server_port)  # 远程服务器端口

    server = NsLocal(listen_address, remote_address)

    asyncio.run(server.listen())


def main():
    run_local_service()


if __name__ == "__main__":
    main()
