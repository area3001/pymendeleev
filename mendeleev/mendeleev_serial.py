import asyncio
import logging
# import serial.rs485
from serial_asyncio import open_serial_connection
import struct

from mendeleev.layers.mendeleev import MendeleevHeader

logger = logging.getLogger(__name__)

class MendeleevSerial:
    _BUF_MAX = 240
    _PREAMBLE_LENGTH = 8
    _PREAMBLE_BYTE = b"\xA5"
    _PACKET_OVERHEAD = 9
    _BAUD_RATE = 38400

    def __init__(self, device, src_addr=0):
        self._device = device
        self._src_addr = src_addr
        self._sequence_number = 0x0000

    async def connect(self):
        self._reader, self._writer = await open_serial_connection(url=self._device, baudrate=self._BAUD_RATE)

    async def send(self, pkt):
        self._writer.write((self._PREAMBLE_BYTE * self._PREAMBLE_LENGTH) + bytes(pkt))

    async def _recv_pkt(self):
        buf = bytes()
        while len(buf) < self._PREAMBLE_LENGTH:
            c = await self._reader.readexactly(1)
            if c == self._PREAMBLE_BYTE:
                buf += c
            else:
                buf = bytes()

        hdr_bytes = await self._reader.readexactly(self._PACKET_OVERHEAD)
        data_length = struct.unpack('>H', hdr_bytes[5:7])[0]
        if data_length > (self._BUF_MAX - self._PREAMBLE_LENGTH - self._PACKET_OVERHEAD):
            raise Exception("invalid data length: %d" % (data_length))
        data_bytes = await self._reader.readexactly(data_length)
        print((hdr_bytes + data_bytes).hex())
        return MendeleevHeader(hdr_bytes + data_bytes)

    async def receive(self, destination=0x00, timeout=2.0):
        pkt = await asyncio.wait_for(self._recv_pkt(), timeout=timeout)
        if pkt.destination == destination or pkt.destination == 0xFF:
            return pkt
        # else:

    async def _send_recv(self, pkt, timeout=3):
        await self.send(pkt)
        answ_pkt = await self.receive(timeout=timeout)
        if not answ_pkt.answers(pkt):
            logger.warning("%s does not answer %s", answ_pkt.show(dump=True), pkt.show(dump=True))
        return answ_pkt

    async def send_cmd(self, destination, command, data, timeout=3):
        request = MendeleevHeader(source=self._src_addr, destination=destination, sequence_nr=self._sequence_number, cmd=command) / data
        self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
        response = await self._send_recv(request, timeout)
        if response.cmd != request.cmd:
            raise Exception("command %s to %d failed:", command, destination, response.show(dump=True))
        return response.payload

    async def _broadcast(self, pkt, wait=.5):
        await self.send(pkt)
        await asyncio.sleep(wait)

    async def broadcast_cmd(self, command, data, wait=.5):
        request = MendeleevHeader(
            source=self._src_addr,
            destination=0xFF,
            sequence_nr=self._sequence_number,
            cmd=command) / data
        self._sequence_number = ((self._sequence_number + 1) & 0xFFFF)
        await self._broadcast(request, wait)

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
        for d in self._get_ota_fragments(data, self._BUF_MAX-self._PACKET_OVERHEAD-self._PREAMBLE_LENGTH):
            await self.send_cmd(destination, "ota", d, timeout=timeout)

    async def broadcast_ota(self, data, wait=.5):
        for d in self._get_ota_fragments(data, self._BUF_MAX-self._PACKET_OVERHEAD-self._PREAMBLE_LENGTH):
            await self.broadcast_cmd(self, "ota", d, wait=wait)