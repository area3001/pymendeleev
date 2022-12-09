#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
import struct
import aioconsole

from mendeleev.mendeleev_serial import MendeleevSerial

logger = logging.getLogger(__name__)

NUM_ELEMENTS = 118

async def address_iterator(default=1):
    return int((await aioconsole.ainput('which address do you want to set? [%d]' % (default))) or default)

class AddressingProcedure:
    def __init__(self, device, broadcasttimeout, automode):
        self.m = MendeleevSerial(device)
        self.broadcasttimeout = broadcasttimeout
        self.automode = automode

    async def start_setup(self, start=True):
        await self.m.broadcast_cmd("setup", b"\x00" if start else b"\x03", self.broadcasttimeout)

    async def set_address(self, next_addr, timeout):
        if next_addr <= 0 or next_addr > NUM_ELEMENTS:
            raise Exception("invalid address to set: %d" % (next_addr))
        # wait indefinitely for a setup_ready broadcast
        print("Please touch the element to set address %d" % (next_addr))
        result = await self.m.receive(destination=0xFF, timeout=timeout)
        if result is None or result.cmd != 0x06 or result.payload.load[0] != 0x01:
            raise Exception("expected to receive a setup_ready response")
        print("received setup_ready from %d" % (result.source))

        # wait a bit
        await asyncio.sleep(.2)

        # send the new address
        await self.m.broadcast_cmd("setup", b"\x02" + struct.pack("B", next_addr), self.broadcasttimeout)
        print("sent address %d" % (next_addr))

    async def main(self):
        await self.m.connect()
        await self.start_setup(True)

        elem = 1
        while True:
            if self.automode:
                if elem > NUM_ELEMENTS:
                    break
                next_address = elem
            else:
                next_address = await address_iterator(elem)
            try:
                await self.set_address(next_address, timeout=None)
            except asyncio.exceptions.TimeoutError:
                print("timed out, try again")
                continue
            except Exception as e:
                logger.exception(e)
                break
            else:
                elem = next_address + 1

        await self.start_setup(False)

def main(argv):
    parser = argparse.ArgumentParser(description="Set up Mendeleev MQTT bridge")
    parser.add_argument("-d", "--device", required=True, help="The RS485 tty device")
    parser.add_argument("-w", "--broadcastwait", type=int, default=.5, help="The time to wait between broadcast messages")
    parser.add_argument("-l", "--log", default="INFO", dest="logLevel", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the logging level")
    parser.add_argument("-f", "--logfile", default=None, help="set logfile")
    parser.add_argument("-a", "--auto", action='store_true', help="automatic mode")
    parser.add_argument("--no-auto", dest='auto', action='store_false', help="manual mode")
    parser.set_defaults(auto=True)

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.getLevelName(args.logLevel), filename=args.logfile, format="%(asctime)s - %(levelname)-8s - %(message)s")

    logger.info("Starting on %s", args.device)
    loop = asyncio.get_event_loop()
    p = AddressingProcedure(args.device, args.broadcastwait, args.auto)
    try:
        loop.run_until_complete(p.main())
    except KeyboardInterrupt:
        loop.run_until_complete(p.start_setup(False))
    loop.close()
    logger.info("Finished")

if __name__ == "__main__":
    main(sys.argv[1:])
