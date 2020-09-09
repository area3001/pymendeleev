import paho.mqtt.client as mqtt
import socket
import logging
import asyncio
import sys, getopt

from mendeleev import MendeleevProtocol

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)

PREFIX = "mendeleev"

client_id = "mqtt2mendeleev_bridge"

PeriodicElement = {
       1: "ELEMENT_H",  # Hydrogen
       2: "ELEMENT_He", # Helium
       3: "ELEMENT_Li", # Lithium
       4: "ELEMENT_Be", # Beryllium
       5: "ELEMENT_B",  # Boron
       6: "ELEMENT_C",  # Carbon
       7: "ELEMENT_N",  # Nitrogen
       8: "ELEMENT_O",  # Oxygen
       9: "ELEMENT_F",  # Fluorine
      10: "ELEMENT_Ne", # Neon
      11: "ELEMENT_Na", # Sodium
      12: "ELEMENT_Mg", # Magnesium
      13: "ELEMENT_Al", # Aluminum
      14: "ELEMENT_Si", # Silicon
      15: "ELEMENT_P",  # Phosphorus
      16: "ELEMENT_S",  # Sulfur
      17: "ELEMENT_Cl", # Chlorine
      18: "ELEMENT_Ar", # Argon
      19: "ELEMENT_K",  # Potassium
      20: "ELEMENT_Ca", # Calcium
      21: "ELEMENT_Sc", # Scandium
      22: "ELEMENT_Ti", # Titanium
      23: "ELEMENT_V",  # Vanadium
      24: "ELEMENT_Cr", # Chromium
      25: "ELEMENT_Mn", # Manganese
      26: "ELEMENT_Fe", # Iron
      27: "ELEMENT_Co", # Cobalt
      28: "ELEMENT_Ni", # Nickel
      29: "ELEMENT_Cu", # Copper
      30: "ELEMENT_Zn", # Zinc
      31: "ELEMENT_Ga", # Gallium
      32: "ELEMENT_Ge", # Germanium
      33: "ELEMENT_As", # Arsenic
      34: "ELEMENT_Se", # Selenium
      35: "ELEMENT_Br", # Bromine
      36: "ELEMENT_Kr", # Krypton
      37: "ELEMENT_Rb", # Rubidium
      38: "ELEMENT_Sr", # Strontium
      39: "ELEMENT_Y",  # Yttrium
      40: "ELEMENT_Zr", # Zirconium
      41: "ELEMENT_Nb", # Niobium
      42: "ELEMENT_Mo", # Molybdenum
      43: "ELEMENT_Tc", # Technetium
      44: "ELEMENT_Ru", # Ruthenium
      45: "ELEMENT_Rh", # Rhodium
      46: "ELEMENT_Pd", # Palladium
      47: "ELEMENT_Ag", # Silver
      48: "ELEMENT_Cd", # Cadmium
      49: "ELEMENT_In", # Indium
      50: "ELEMENT_Sn", # Tin
      51: "ELEMENT_Sb", # Antimony
      52: "ELEMENT_Te", # Tellurium
      53: "ELEMENT_I",  # Iodine
      54: "ELEMENT_Xe", # Xenon
      55: "ELEMENT_Cs", # Cesium
      56: "ELEMENT_Ba", # Barium
      57: "ELEMENT_La", # Lanthanum
      58: "ELEMENT_Ce", # Cerium
      59: "ELEMENT_Pr", # Praseodymium
      60: "ELEMENT_Nd", # Neodymium
      61: "ELEMENT_Pm", # Promethium
      62: "ELEMENT_Sm", # Samarium
      63: "ELEMENT_Eu", # Europium
      64: "ELEMENT_Gd", # Gadolinium
      65: "ELEMENT_Tb", # Terbium
      66: "ELEMENT_Dy", # Dysprosium
      67: "ELEMENT_Ho", # Holmium
      68: "ELEMENT_Er", # Erbium
      69: "ELEMENT_Tm", # Thulium
      70: "ELEMENT_Yb", # Ytterbium
      71: "ELEMENT_Lu", # Lutetium
      72: "ELEMENT_Hf", # Hafnium
      73: "ELEMENT_Ta", # Tantalum
      74: "ELEMENT_W",  # Tungsten
      75: "ELEMENT_Re", # Rhenium
      76: "ELEMENT_Os", # Osmium
      77: "ELEMENT_Ir", # Iridium
      78: "ELEMENT_Pt", # Platinum
      79: "ELEMENT_Au", # Gold
      80: "ELEMENT_Hg", # Mercury
      81: "ELEMENT_Tl", # Thallium
      82: "ELEMENT_Pb", # Lead
      83: "ELEMENT_Bi", # Bismuth
      84: "ELEMENT_Po", # Polonium
      85: "ELEMENT_At", # Astatine
      86: "ELEMENT_Rn", # Radon
      87: "ELEMENT_Fr", # Francium
      88: "ELEMENT_Ra", # Radium
      89: "ELEMENT_Ac", # Actinium
      90: "ELEMENT_Th", # Thorium
      91: "ELEMENT_Pa", # Protactinium
      92: "ELEMENT_U",  # Uranium
      93: "ELEMENT_Np", # Neptunium
      94: "ELEMENT_Pu", # Plutonium
      95: "ELEMENT_Am", # Americium
      96: "ELEMENT_Cm", # Curium
      97: "ELEMENT_Bk", # Berkelium
      98: "ELEMENT_Cf", # Californium
      99: "ELEMENT_Es", # Einsteinium
     100: "ELEMENT_Fm", # Fermium
     101: "ELEMENT_Md", # Mendelevium
     102: "ELEMENT_No", # Nobelium
     103: "ELEMENT_Lr", # Lawrencium
     104: "ELEMENT_Rf", # Rutherfordium
     105: "ELEMENT_Db", # Dubnium
     106: "ELEMENT_Sg", # Seaborgium
     107: "ELEMENT_Bh", # Bohrium
     108: "ELEMENT_Hs", # Hassium
     109: "ELEMENT_Mt", # Meitnerium
     110: "ELEMENT_Ds", # Darmstadtium
     111: "ELEMENT_Rg", # Roentgenium
     112: "ELEMENT_Cp", # Copernicium
     113: "ELEMENT_Nh", # Nihonium
     114: "ELEMENT_Fl", # Flerovium
     115: "ELEMENT_Mc", # Moscovium
     116: "ELEMENT_Lv", # Livermorium
     117: "ELEMENT_Ts", # Tennessine
     118: "ELEMENT_Og", # Oganesson
}

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
    def __init__(self, loop, device, broker, prefix):
        self.loop = loop
        self.m = MendeleevProtocol(device)
        self.broker = broker
        self.prefix = prefix

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

        if ((element < 0) or (element > 118)) and (element != 0xFF):
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
                await self.m.broadcast_ota(msg.payload)
            else:
                await self.m.broadcast_cmd(cmd, msg.payload)
        else:
            logger.debug("Send command %s to %d...", cmd, element)
            if cmd == "ota":
                await self.m.send_ota(element, msg.payload)
            else:
                response = await self.m.send_cmd(element, cmd, msg.payload)
                logger.debug("reponse for command %s to %d: %s", cmd, element, response)

    async def main(self):
        self.disconnected = self.loop.create_future()
        self.got_message = None

        self.client = mqtt.Client(client_id=client_id)
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

def print_help():
    print('test.py -d <device> -b <broker> -p <prefix>')

def main(argv):
    broker = "localhost"
    prefix = "mendeleev"

    try:
        opts, args = getopt.getopt(argv,"hd:b:p:",["device=","broker=","prefix="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-d", "--device"):
            device = arg
        elif opt in ("-b", "--broker"):
            broker = arg
        elif opt in ("-p", "--prefix"):
            prefix = arg
    logger.info("Starting on %s and %s with prefix %s", device, broker, prefix)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MendeleevBridge(loop, device, broker, prefix).main())
    loop.close()
    logger.info("Finished")

if __name__ == "__main__":
    main(sys.argv[1:])

# loop = asyncio.get_event_loop()


# loop.run_until_complete(m.connect(loop))

# def update():
#     logger.debug("do an update")

# def sensor_test():
#     logger.debug("do a sensor test")

# # The callback for when the client receives a CONNACK response from the server.
# def on_connect(client, userdata, flags, rc):
#     logger.debug("Connected with result code "+str(rc))

#     # Subscribing in on_connect() means that if we lose the connection and
#     # reconnect then subscriptions will be renewed.
#     client.subscribe(PREFIX + "/+/+")

# # The callback for when a PUBLISH message is received from the server.
# def on_message(client, userdata, msg):
#     splitted_topic = msg.topic.split("/")

#     if len(splitted_topic) != 3:
#         logger.error("topic is not valid: %s", msg.topic)
#         return

#     try:
#         element = int(splitted_topic[1])
#     except ValueError as e:
#         logger.error("element index %s is not valid", splitted_topic[1])
#         return

#     cmd = splitted_topic[2]

#     if ((element < 0) or (element > 118)) and (element != 0xFF):
#         logger.error("element %d not valid", element)
#         return

#     if element == 0:
#         if cmd == "update":
#             update()
#         elif cmd == "sensortest":
#             sensor_test()
#         else:
#             logger.error("command %s is not valid for master", cmd)
#         return
#     elif element == 0xFF:
#         logger.debug("Broadcasting command %s: %s", cmd)
#         loop.run_until_complete(m.broadcast_cmd(cmd, msg.payload))
#     else:
#         logger.debug("Send command %s to %d...", cmd, element)
#         response = loop.run_until_complete(m.send_cmd(element, cmd, msg.payload))
#         logger.debug("reponse for command %s to %d: %s", cmd, element, response)

# client = mqtt.Client()
# client.on_connect = on_connect
# client.on_message = on_message

# client.connect(BROKER, 1883, 60)

# # Blocking call that processes network traffic, dispatches callbacks and
# # handles reconnecting.
# # Other loop*() functions are available that give a threaded interface and a
# # manual interface.
# loop.run_until_complete(client.loop_forever())
