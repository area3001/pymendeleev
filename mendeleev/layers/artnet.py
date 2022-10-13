from scapy.packet import Packet, bind_layers
from scapy.fields import StrFixedLenField, MACField, XStrFixedLenField, FieldListField, LEShortField, LEShortEnumField, ShortField, LenField, ByteField
from scapy.layers.inet import UDP
from scapy.data import ETHER_ANY

ARTNET_MAX_PORTS = 4 # The maximum ports per node built into the ArtNet protocol. This is always 4. Don't change it unless you really know what your doing
ARTNET_SHORT_NAME_LENGTH = 18 # The length of the short name field. Always 18
ARTNET_LONG_NAME_LENGTH = 64 # The length of the long name field. Always 64
ARTNET_REPORT_LENGTH = 64 # The length of the report field. Always 64
ARTNET_DMX_LENGTH = 512 # The length of the DMX field. Always 512
ARTNET_RDM_UID_WIDTH = 6 # Number of bytes in a RDM UID
ARTNET_MAC_SIZE = 6 # Length of the hardware address
ARTNET_ESTA_SIZE = 2 # Length of the ESTA field
ARTNET_IP_SIZE = 4 # Length of the IP field

OPCODES = {
    0x2000: "POLL",
    0x2100: "REPLY",
    0x5000: "DMX",
    0x6000: "ADDRESS",
    0x7000: "INPUT",
    0x8000: "TODREQUEST",
    0x8100: "TODDATA",
    0x8200: "TODCONTROL",
    0x8300: "RDM",
    0xa010: "VIDEOSTEUP",
    0xa020: "VIDEOPALETTE",
    0xa040: "VIDEODATA",
    0xf000: "MACMASTER",
    0xf100: "MACSLAVE",
    0xf200: "FIRMWAREMASTER",
    0xf300: "FIRMWAREREPLY",
    0xf800: "IPPROG",
    0xf900: "IPREPLY",
    0x9000: "MEDIA",
    0x9200: "MEDIAPATCH",
    0x9300: "MEDIACONTROLREPLY"
}

# https://art-net.org.uk/how-it-works/streaming-packets/artdmx-packet-definition/
class ArtNet(Packet):
    name = "ARTNET"
    fields_desc = [
        StrFixedLenField("header", b"Art-Net\x00", 8),
        LEShortEnumField("opcode", 0, OPCODES),
        ShortField("protocolVersion", 14),
    ]

bind_layers(UDP, ArtNet, dport=6454)

class ArtNet_POLL(Packet):
    name = "POLL"
    fields_desc = [
        ByteField("ttm", 0),
        ByteField("pad", 0),
    ]

bind_layers(ArtNet, ArtNet_POLL, opcode=0x2000)

class ArtNet_REPLY(Packet):
    name = "REPLY"
    fields_desc = [
        LEShortField("sub", 0),
        LEShortField("oem", 0),
        ByteField("ubea", 0),
        ByteField("status", 0),
        FieldListField("etsaman", [], ByteField("", None), count_from=lambda x: 2),
        StrFixedLenField("shortname", "", ARTNET_SHORT_NAME_LENGTH),
        StrFixedLenField("longname", "", ARTNET_LONG_NAME_LENGTH),
        StrFixedLenField("nodereport", "", ARTNET_REPORT_LENGTH),
        LEShortField("numbports", 0),
        FieldListField("porttypes", [], ByteField("", None), count_from=lambda x: ARTNET_MAX_PORTS),
        FieldListField("goodinput", [], ByteField("", None), count_from=lambda x: ARTNET_MAX_PORTS),
        FieldListField("goodoutput", [], ByteField("", None), count_from=lambda x: ARTNET_MAX_PORTS),
        FieldListField("swin", [], ByteField("", None), count_from=lambda x: ARTNET_MAX_PORTS),
        FieldListField("swout", [], ByteField("", None), count_from=lambda x: ARTNET_MAX_PORTS),
        ByteField("swvideo", 0),
        ByteField("swmacro", 0),
        ByteField("swremote", 0),
        ByteField("sp1", 0),
        ByteField("sp2", 0),
        ByteField("sp3", 0),
        ByteField("style", 0),
        MACField("mac", ETHER_ANY),
        XStrFixedLenField("filler", "", 32),
    ]

bind_layers(ArtNet, ArtNet_REPLY, opcode=0x2100)

class ArtNet_DMX(Packet):
    name = "DMX"
    fields_desc = [
        ByteField("sequence", 0), # to fix for out-of-order delivery. 0 is disable
        ByteField("physical", 0),
        LEShortField("universe", 0),
        LenField("data_length", None, fmt=">H") # should be always 512
    ]

bind_layers(ArtNet, ArtNet_DMX, opcode=0x5000)