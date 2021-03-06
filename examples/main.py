import paho.mqtt.client as mqtt
import socket
import logging
import asyncio
import sys
import argparse

from mendeleev import MendeleevProtocol

logger = logging.getLogger(__name__)

PREFIX = "mendeleev"
NUM_ELEMENTS = 118
CLIENT_ID = "mqtt2mendeleev_bridge"

def update():
    logger.info("update")

def sensor_test():
    logger.info('sensor test')

class TopicException(Exception):
    pass

class AsyncioHelper:
    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    def on_socket_open(self, client, userdata, sock):
        logger.debug("Socket opened")

        def cb():
            logger.debug("Socket is readable, calling loop_read")
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        logger.debug("Socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        logger.debug("Watching socket for writability.")

        def cb():
            logger.debug("Socket is writable, calling loop_write")
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        logger.debug("Stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        logger.debug("misc_loop started")
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
        logger.debug("misc_loop finished")

class MendeleevBridge:
    def __init__(self, loop, device, broker, prefix, timeout, broadcasttimeout):
        self.loop = loop
        self.m = MendeleevProtocol(device)
        self.broker = broker
        self.prefix = prefix
        self.timeout = timeout
        self.broadcasttimeout = broadcasttimeout

    def on_connect(self, client, userdata, flags, rc):
        logger.info("Subscribing")
        client.subscribe(self.prefix + "/+/+")

    def on_message(self, client, userdata, msg):
        if self.got_message:
            self.got_message.set_result(msg)
        else:
            logger.warning("got_message not set!")

    def on_disconnect(self, client, userdata, rc):
        self.disconnected.set_result(rc)

    async def process_msg(self, msg):
        splitted_topic = msg.topic.split("/")

        if len(splitted_topic) != 3:
            raise TopicException("topic format is not correct: %s" % (msg.topic))

        try:
            element = int(splitted_topic[1])
        except ValueError as e:
            raise TopicException("element index %s is not valid" % (splitted_topic[1]))

        cmd = splitted_topic[2]

        if ((element < 0) or (element > NUM_ELEMENTS)) and (element != 0xFF):
            raise TopicException("element %d not valid" % (element))

        if element == 0:
            if cmd == "update":
                update()
            elif cmd == "sensortest":
                sensor_test()
            else:
                raise TopicException("command %s is not valid for master" % (cmd))
        elif element == 0xFF:
            logger.debug("Broadcasting command %s", cmd)
            if cmd == "ota":
                await self.m.broadcast_ota(msg.payload, self.broadcasttimeout)
            else:
                await self.m.broadcast_cmd(cmd, msg.payload, self.broadcasttimeout)
        else:
            logger.debug("Send command %s to %d...", cmd, element)
            if cmd == "ota":
                await self.m.send_ota(element, msg.payload, self.timeout)
            else:
                response = await self.m.send_cmd(element, cmd, msg.payload, self.timeout)
                logger.debug("reponse for command %s to %d: %s", cmd, element, response)

    async def main(self):
        self.disconnected = self.loop.create_future()
        self.got_message = None

        self.client = mqtt.Client(client_id=CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        aioh = AsyncioHelper(self.loop, self.client)

        await self.m.connect(self.loop)

        self.client.connect(self.broker, 1883, 60)
        self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

        while True:
            self.got_message = self.loop.create_future()
            msg = await self.got_message
            try:
                result = await self.process_msg(msg)
            except asyncio.TimeoutError:
                logger.warning("timeout waiting for response for %s", msg.topic)
                self.client.publish(msg.topic + "/nack", qos=1)
            except TopicException as te:
                logger.error("Invalid MQTT request")
                logger.exception(te)
                self.client.publish(msg.topic + "/nack", qos=1)
            except Exception as e:
                logger.error("error when processing %s", msg.topic)
                logger.exception(e)
                self.client.publish(msg.topic + "/nack", qos=1)
            else:
                self.client.publish(msg.topic + "/ack", result, qos=1)
            self.got_message = None

        self.client.disconnect()
        logger.info("Disconnected: {}".format(await self.disconnected))

def main(argv):
    parser = argparse.ArgumentParser(description="Set up Mendeleev MQTT bridge")
    parser.add_argument("-d", "--device", required=True, help='The RS485 tty device')
    parser.add_argument("-b", "--broker", default="localhost", help='The MQTT broker')
    parser.add_argument("-p", "--prefix", default="mendeleev", help='The MQTT topic prefix')
    parser.add_argument("-t", "--timeout", type=int, default=1, help='The timeout to wait for responses')
    parser.add_argument("-w", "--broadcastwait", type=int, default=.5, help='The time to wait between broadcast messages')

    args = parser.parse_args(argv)

    logger.info("Starting on %s and %s with prefix %s", args.device, args.broker, args.prefix)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MendeleevBridge(loop, args.device, args.broker, args.prefix, args.timeout, args.broadcastwait).main())
    loop.close()
    logger.info("Finished")

if __name__ == "__main__":
    main(sys.argv[1:])