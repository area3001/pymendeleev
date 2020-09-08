import asyncio
import logging
from urllib.parse import urlparse
from async_timeout import timeout
import serial
from serial_asyncio import create_serial_connection
from scapy.packet import Raw
import struct

from .mendeleev_packets import *

logger = logging.getLogger(__name__)

class MendeleevProtocol(asyncio.Protocol):
    _PREAMBLE_LENGTH = 8
    _PREAMBLE_BYTE = b"\xA5"
    _HEADER_LENGTH = 7
    _BAUD_RATE = 115200

    def __init__(self, url):
        super().__init__()
        self._url = urlparse(url)
        self._transport = None
        self._loop = None
        self._running = False
        self._buf = b''
        self._lock = None
        self._request_lock = None
        self._sent_pkt = None
        self._recv_future = None
        self._sequence_number = 0x0000

    def data_received(self, data: bytes):
        self._transport.pause_reading()
        self._buf += data
        while len(self._buf) > self._PREAMBLE_LENGTH + self._HEADER_LENGTH:
            if self._buf[:self._PREAMBLE_LENGTH] == (self._PREAMBLE_BYTE * self._PREAMBLE_LENGTH):

                # TODO check the other things before we look at the length?

                length = struct.unpack("<H", self._buf[13:15])[0]
                pkt_length = self._PREAMBLE_LENGTH + self._HEADER_LENGTH + length + 2

                if pkt_length > len(self._buf):
                    # not everything received yet
                    break

                pkt_bytes = self._buf[self._PREAMBLE_LENGTH:pkt_length]
                try:
                    pkt = MendeleevHeader(pkt_bytes)
                except:
                    logger.error("Invalid packet received")
                    self._buf[pkt_length:]
                    continue

                self._buf = self._buf[pkt_length:]

                if not self._recv_future or \
                   self._recv_future.done() or \
                   self._recv_future.cancelled():
                    continue

                if pkt.answers(self._sent_pkt):
                    self._recv_future.set_result(pkt)
                else:
                    logger.error("%s does not answer %s", pkt.show(dump=True), self._sent_pkt.show(dump=True))
                    self._recv_future.cancel()
            else:
                logger.error("Unknown byte: %02x" % (self._buf[0]))
                self._buf = self._buf[1:]

        self._transport.resume_reading()

    async def _send_recv(self, pkt, timeout=3):
        self._sent_pkt = pkt
        self._recv_future = self._loop.create_future()
        self._transport.write(bytes(pkt))
        return await asyncio.wait_for(self._recv_future, timeout)

    async def _broadcast(self, pkt, wait=1):
        self._transport.write(bytes(pkt))
        await asyncio.sleep(wait)

    def connection_lost(self, exc: Exception):
        logger.debug('port closed')
        if self._running and not self._lock.locked():
            asyncio.ensure_future(self._reconnect(), loop=self._loop)

    async def _create_connection(self):
        if self._url.scheme == 'socket':
            kwargs = {
                'host': self._url.hostname,
                'port': self._url.port,
            }
            coro = self._loop.create_connection(lambda: self, **kwargs)
        else:
            kwargs = {
                'url': self._url.geturl(),
                'baudrate': self._BAUD_RATE
            }
            coro = create_serial_connection(self._loop, lambda: self, **kwargs)
        return await coro

    async def _reconnect(self, delay: int = 10):
        async with self._lock:
            await self._disconnect()
            await asyncio.sleep(delay, loop=self._loop)
            try:
                async with timeout(5, loop=self._loop):
                    self._transport, _ = await self._create_connection()
            except (BrokenPipeError, ConnectionRefusedError,
                    serial.SerialException, asyncio.TimeoutError) as exc:
                logger.warning(exc)
                asyncio.ensure_future(self._reconnect(), loop=self._loop)
            else:
                logger.info('Connected to %s', self._url.geturl())

    async def connect(self, loop):
        if self._running:
            return

        self._loop = loop
        self._lock = asyncio.Lock(loop=loop)
        self._request_lock = asyncio.Lock(loop=loop)
        self._running = True
        await self._reconnect(delay=0)

    async def _disconnect(self):
        if self._transport:
            self._transport.abort()
            self._transport = None

    async def broadcast_cmd(self, command, data, wait=1):
        async with self._request_lock:
            request = MendeleevHeader(sequence_nr=self._sequence_number, command=command) / Raw(data)
            self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
            await self._broadcast(request, wait)

    async def send_cmd(self, destination, command, data):
        async with self._request_lock:
            request = MendeleevHeader(destination=destination, sequence_nr=self._sequence_number, command=command) / Raw(data)
            self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
            response = await self._send_recv(request)
            if response.command == request.command:
                return response.payload
            else:
                raise Exception("Command %s to %s failed:", command, destination, response.show(dump=True))
