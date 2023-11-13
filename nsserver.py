import asyncio
import socket

from utils import config
from utils import securesocket
from utils import cipher


class NsServer:
    def __init__(self, listen_address):
        self.listen_address = listen_address
        self.loop = None
        self.secureSocket = None

    async def listen(self):
        self.loop = asyncio.get_running_loop()
        self.secureSocket = securesocket.SecureSocket(self.loop, cipher.load_password())

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
        """
        Handle the connection from NsLocal.
        """
        """
        SOCKS Protocol Version 5 https://www.ietf.org/rfc/rfc1928.txt
        The localConn connects to the dst_server, and sends a ver
        identifier/method selection message:
                    +----+----------+----------+
                    |VER | NMETHODS | METHODS  |
                    +----+----------+----------+
                    | 1  |    1     | 1 to 255 |
                    +----+----------+----------+
        The VER field is set to X'05' for this ver of the protocol.  The
        NMETHODS field contains the number of method identifier octets that
        appear in the METHODS field.
        """
        buf = await self.secureSocket.decodeRead(local_sock)
        if not buf or buf[0] != 0x05:
            local_sock.close()
            return
        """
        The dst_server selects from one of the methods given in METHODS, and
        sends a METHOD selection message:
                    +----+--------+
                    |VER | METHOD |
                    +----+--------+
                    | 1  |   1    |
                    +----+--------+
        If the selected METHOD is X'FF', none of the methods listed by the
        client are acceptable, and the client MUST close the connection.

        The values currently defined for METHOD are:

                o  X'00' NO AUTHENTICATION REQUIRED
                o  X'01' GSSAPI
                o  X'02' USERNAME/PASSWORD
                o  X'03' to X'7F' IANA ASSIGNED
                o  X'80' to X'FE' RESERVED FOR PRIVATE METHODS
                o  X'FF' NO ACCEPTABLE METHODS

        The client and server then enter a method-specific sub-negotiation.
        """
        await self.secureSocket.encodeWrite(local_sock, bytearray((0x05, 0x00)))
        """
        The SOCKS request is formed as follows:
            +----+-----+-------+------+----------+----------+
            |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
            +----+-----+-------+------+----------+----------+
            | 1  |  1  | X'00' |  1   | Variable |    2     |
            +----+-----+-------+------+----------+----------+
        Where:

          o  VER    protocol version: X'05'
          o  CMD
             o  CONNECT X'01'
             o  BIND X'02'
             o  UDP ASSOCIATE X'03'
          o  RSV    RESERVED
          o  ATYP   address type of following address
             o  IP V4 address: X'01'
             o  DOMAINNAME: X'03'
             o  IP V6 address: X'04'
          o  DST.ADDR       desired destination address
          o  DST.PORT desired destination port in network octet
             order
        """
        buf = await self.secureSocket.decodeRead(local_sock)
        if len(buf) < 7:
            local_sock.close()
            return

        if buf[1] != 0x01:
            local_sock.close()
            return

        dst_ip = None

        dst_port = buf[-2:]
        dst_port = int(dst_port.hex(), 16)

        dst_family = None

        if buf[3] == 0x01:
            # ipv4
            dst_ip = socket.inet_ntop(socket.AF_INET, buf[4:4 + 4])
            # dst_address = net.Address(ip=dst_ip, port=dst_port)
            dst_address = (dst_ip, dst_port)
            dst_family = socket.AF_INET
        elif buf[3] == 0x03:
            # domain
            dst_ip = buf[5:-2].decode()
            # dst_address = net.Address(ip=dst_ip, port=dst_port)
            dst_address = (dst_ip, dst_port)
        elif buf[3] == 0x04:
            # ipv6
            dst_ip = socket.inet_ntop(socket.AF_INET6, buf[4:4 + 16])
            dst_address = (dst_ip, dst_port, 0, 0)
            dst_family = socket.AF_INET6
        else:
            local_sock.close()
            return

        dst_server = None
        if dst_family:
            try:
                dst_server = socket.socket(
                    family=dst_family, type=socket.SOCK_STREAM)
                dst_server.setblocking(False)
                await self.loop.sock_connect(dst_server, dst_address)
            except OSError:
                if dst_server is not None:
                    dst_server.close()
                    dst_server = None
        else:
            host, port = dst_address
            for res in await self.loop.getaddrinfo(host, port):
                dst_family, socktype, proto, _, dst_address = res
                try:
                    dst_server = socket.socket(dst_family, socktype, proto)
                    dst_server.setblocking(False)
                    await self.loop.sock_connect(dst_server, dst_address)
                    break
                except OSError:
                    if dst_server is not None:
                        dst_server.close()
                        dst_server = None

        if dst_family is None:
            return
        """
        The SOCKS request information is sent by the client as soon as it has
        established a connection to the SOCKS server, and completed the
        authentication negotiations.  The server evaluates the request, and
        returns a reply formed as follows:

                +----+-----+-------+------+----------+----------+
                |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
                +----+-----+-------+------+----------+----------+
                | 1  |  1  | X'00' |  1   | Variable |    2     |
                +----+-----+-------+------+----------+----------+

            Where:

                o  VER    protocol version: X'05'
                o  REP    Reply field:
                    o  X'00' succeeded
                    o  X'01' general SOCKS server failure
                    o  X'02' connection not allowed by ruleset
                    o  X'03' Network unreachable
                    o  X'04' Host unreachable
                    o  X'05' Connection refused
                    o  X'06' TTL expired
                    o  X'07' Command not supported
                    o  X'08' Address type not supported
                    o  X'09' to X'FF' unassigned
                o  RSV    RESERVED
                o  ATYP   address type of following address
        """
        await self.secureSocket.encodeWrite(local_sock,
                                            bytearray((0x05, 0x00, 0x00, 0x01, 0x00, 0x00,
                                                       0x00, 0x00, 0x00, 0x00)))

        local2dist = asyncio.create_task(self.secureSocket.decodeCopy(local_sock, dst_server))
        dist2local = asyncio.create_task(self.secureSocket.encodeCopy(dst_server, local_sock))

        task = await asyncio.gather(
            local2dist,
            dist2local,
            return_exceptions=True
        )

        dst_server.close()
        local_sock.close()


def run_server_service():
    listen_address = ("0.0.0.0", config.server_port)

    server = NsServer(listen_address)

    asyncio.run(server.listen())


def main():
    run_server_service()


if __name__ == "__main__":
    main()
