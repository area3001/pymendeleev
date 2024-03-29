import asyncio
import logging
from urllib.parse import urlparse
from async_timeout import timeout
import serial
from serial_asyncio import create_serial_connection
from scapy.packet import Raw
import struct

from mendeleev.layers.mendeleev import MendeleevHeader

logger = logging.getLogger(__name__)

class MendeleevProtocol(asyncio.Protocol):
    _BUF_MAX = 240
    _PREAMBLE_LENGTH = 8
    _PREAMBLE_BYTE = b"\xA5"
    _PACKET_OVERHEAD = 9
    _BAUD_RATE = 38400

    def __init__(self, url, src_addr=0):
        super().__init__()
        self._url = urlparse(url)
        self._transport = None
        self._loop = None
        self._running = False
        self._buf = b''
        self._lock = None
        self._request_lock = None
        self._sent_pkt = None
        self._sequence_number = 0x0000
        self._src_addr = src_addr
        self.queue = asyncio.Queue()

    async def process_data(self, pkt):
        logger.debug("queuing: %s", pkt.show(dump=True))
        await self.queue.put(pkt)

    def data_received(self, data: bytes):
        self._transport.pause_reading()
        self._buf += data
        while len(self._buf) >= self._PREAMBLE_LENGTH + self._PACKET_OVERHEAD:
            if self._buf[:self._PREAMBLE_LENGTH] == (self._PREAMBLE_BYTE * self._PREAMBLE_LENGTH):
                # TODO check the other things before we look at the length?

                data_len = struct.unpack(">H", self._buf[13:15])[0]
                pkt_length = self._PREAMBLE_LENGTH + self._PACKET_OVERHEAD + data_len

                if pkt_length > self._BUF_MAX:
                    logger.warning("invalid packet length: %d" % (pkt_length))
                    self._buf = self._buf[1:]
                    continue

                if pkt_length > len(self._buf):
                    # not everything received yet
                    break

                pkt_bytes = self._buf[self._PREAMBLE_LENGTH:pkt_length]
                try:
                    pkt = MendeleevHeader(pkt_bytes)
                    asyncio.ensure_future(self.process_data(pkt))
                except Exception as e:
                    logger.error("Invalid packet received:")
                    logger.exception(e)
                self._buf = self._buf[pkt_length:]
            else:
                logger.error("Unknown byte: %02x" % (self._buf[0]))
                self._buf = self._buf[1:]

        self._transport.resume_reading()

    async def _send_recv(self, pkt, timeout=3):
        self._transport.write((self._PREAMBLE_BYTE * self._PREAMBLE_LENGTH) + bytes(pkt))
        answ_pkt = await asyncio.wait_for(self.queue.get(), timeout)
        if not answ_pkt.answers(pkt):
            logger.warning("%s does not answer %s", answ_pkt.show(dump=True), pkt.show(dump=True))
        return answ_pkt

    async def _recv(self, timeout=3):
        return await asyncio.wait_for(self.queue.get(), timeout)

    async def _broadcast(self, pkt, wait=.5):
        with_preamble_bytes = (self._PREAMBLE_BYTE * self._PREAMBLE_LENGTH) + bytes(pkt)
        self._transport.write(with_preamble_bytes)
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

    def _get_ota_fragments(self, data, size):
        result = []
        fragment_idx = 0
        frame_size = size - 1
        total = len(data)
        p = struct.pack("B", fragment_idx) + struct.pack('>I', total)
        fragment_idx += 1
        result.append(p)
        for i in range(0, total, frame_size):
            p = struct.pack("B", fragment_idx)
            fragment_idx += 1
            p += data[i:i+frame_size]
            result.append(p)
        return result

    async def send_ota(self, destination, data, timeout=3):
        async with self._request_lock:
            for d in self._get_ota_fragments(data, self._BUF_MAX-self._PACKET_OVERHEAD-self._PREAMBLE_LENGTH):
                request = MendeleevHeader(source=self._src_addr, destination=destination, sequence_nr=self._sequence_number, cmd="ota") / Raw(d)
                self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
                response = await self._send_recv(request, timeout)
                if response.cmd != request.cmd:
                    raise Exception("OTA to %s failed:", destination, response.show(dump=True))

    async def broadcast_ota(self, data, wait=.5):
        async with self._request_lock:
            for d in self._get_ota_fragments(data, self._BUF_MAX-self._PACKET_OVERHEAD-self._PREAMBLE_LENGTH):
                request = MendeleevHeader(source=self._src_addr, sequence_nr=self._sequence_number, cmd="ota") / Raw(d)
                self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
                await self._broadcast(request, wait)

    async def broadcast_cmd(self, command, data, wait=.5):
        async with self._request_lock:
            request = MendeleevHeader(source=self._src_addr, sequence_nr=self._sequence_number, cmd=command) / Raw(data)
            self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
            await self._broadcast(request, wait)

    async def receive(self, destination=0x00, timeout=None): # block until something received
        async with self._request_lock:
            pkt = await self._recv(timeout)
            if pkt.destination == destination or pkt.destination == 0xFF:
                return pkt

    async def send_cmd(self, destination, command, data, timeout=3):
        async with self._request_lock:
            request = MendeleevHeader(source=self._src_addr, destination=destination, sequence_nr=self._sequence_number, cmd=command) / Raw(data)
            self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
            response = await self._send_recv(request, timeout)
            if response.cmd == request.cmd:
                return response.payload
            else:
                raise Exception("Command %s to %s failed:", command, destination, response.show(dump=True))