from scapy.data import ETHER_ANY
from scapy.fields import (ByteEnumField, ByteField, FieldListField, LenField,
                          LEShortEnumField, LEShortField, MACField, ShortField,
                          StrFixedLenField, XStrFixedLenField)
from scapy.layers.inet import UDP
from scapy.packet import Packet, bind_layers

ARTNET_MAX_PORTS = 4 # The maximum ports per node built into the ArtNet protocol. This is always 4. Don't change it unless you really know what your doing
ARTNET_SHORT_NAME_LENGTH = 18 # The length of the short name field. Always 18
ARTNET_LONG_NAME_LENGTH = 64 # The length of the long name field. Always 64
ARTNET_REPORT_LENGTH = 64 # The length of the report field. Always 64
ARTNET_DMX_LENGTH = 512 # The length of the DMX field. Always 512
ARTNET_RDM_UID_WIDTH = 6 # Number of bytes in a RDM UID
ARTNET_ESTA_SIZE = 2 # Length of the ESTA field
ARTNET_IP_SIZE = 4 # Length of the IP field

OPCODES = {
    0x2000: "OpPoll", # This is an ArtPoll packet, no other data is contained in this UDP packet.
    0x2100: "OpPollReply", # This is an ArtPollReply Packet. It contains device status information.
    0x2300: "OpDiagData", # Diagnostics and data logging packet.
    0x2400: "OpCommand", # Used to send text based parameter commands.
    0x5000: "OpDmx", # This is an ArtDmx data packet. It contains zero start code DMX512 information for a single Universe.
    0x5100: "OpNzs", # This is an ArtNzs data packet. It contains non-zero start code (except RDM) DMX512 information for a single Universe.
    0x5200: "OpSync", # This is an ArtSync data packet. It is used to force synchronous transfer of ArtDmx packets to a node’s output.
    0x6000: "OpAddress", # This is an ArtAddress packet. It contains remote programming information for a Node.
    0x7000: "OpInput", # This is an ArtInput packet. It contains enable – disable data for DMX inputs.
    0x8000: "OpTodRequest", # This is an ArtTodRequest packet. It is used to request a Table of Devices (ToD) for RDM discovery.
    0x8100: "OpTodData", # This is an ArtTodData packet. It is used to send a Table of Devices (ToD) for RDM discovery.
    0x8200: "OpTodControl", # This is an ArtTodControl packet. It is used to send RDM discovery control messages.
    0x8300: "OpRdm", # This is an ArtRdm packet. It is used to send all non discovery RDM messages.
    0x8400: "OpRdmSub", # This is an ArtRdmSub packet. It is used to send compressed, RDM Sub-Device data.
    0xa010: "OpVideoSetup", # This is an ArtVideoSetup packet. It contains video screen setup information for nodes that implement the extended video features.
    0xa020: "OpVideoPalette", # This is an ArtVideoPalette packet. It contains colour palette setup information for nodes that implement the extended video features.
    0xa040: "OpVideoData", # This is an ArtVideoData packet. It contains display data for nodes that implement the extended video features.
    0xf000: "OpMacMaster", # This packet is deprecated.
    0xf100: "OpMacSlave", # This packet is deprecated.
    0xf200: "OpFirmwareMaster", # This is an ArtFirmwareMaster packet. It is used to upload new firmware or firmware extensions to the Node.
    0xf300: "OpFirmwareReply", # This is an ArtFirmwareReply packet. It is returned by the node to acknowledge receipt of an ArtFirmwareMaster packet or ArtFileTnMaster packet.
    0xf400: "OpFileTnMaster", # Uploads user file to node.
    0xf500: "OpFileFnMaster", # Downloads user file from node.
    0xf600: "OpFileFnReply", # Server to Node acknowledge for download packets.
    0xf800: "OpIpProg", # This is an ArtIpProg packet. It is used to re-programme the IP address and Mask of the Node.
    0xf900: "OpIpProgReply", # This is an ArtIpProgReply packet. It is returned by the node to acknowledge receipt of an ArtIpProg packet.
    0x9000: "OpMedia", # This is an ArtMedia packet. It is Unicast by a Media Server and acted upon by a Controller.
    0x9100: "OpMediaPatch", # This is an ArtMediaPatch packet. It is Unicast by a Controller and acted upon by a Media Server.
    0x9200: "OpMediaControl", # This is an ArtMediaControl packet. It is Unicast by a Controller and acted upon by a Media Server.
    0x9300: "OpMediaContrlReply", # This is an ArtMediaControlReply packet. It is Unicast by a Media Server and acted upon by a Controller.
    0x9700: "OpTimeCode", # This is an ArtTimeCode packet. It is used to transport time code over the network.
    0x9800: "OpTimeSync", # Used to synchronise real time date and clock
    0x9900: "OpTrigger", # Used to send trigger macros
    0x9a00: "OpDirectory", # Requests a node's file list
    0x9b00: "OpDirectoryReply", # Replies to OpDirectory with file list
}

STYLE_CODES = {
    0x00: "StNode", # A DMX to / from Art-Net device
    0x01: "StController", # A lighting console.
    0x02: "StMedia", # A Media Server.
    0x03: "StRoute", # A network routing device.
    0x04: "StBackup", # A backup device.
    0x05: "StConfig", # A configuration or diagnostic tool.
    0x06: "StVisual", # A visualiser.
}

STATUS_CODES = {
    0x0000: "RcDebug", # Booted in debug mode (Only used in development)
    0x0001: "RcPowerOk", # Power On Tests successful
    0x0002: "RcPowerFail", # Hardware tests failed at Power On
    0x0003: "RcSocketWr1", # Last UDP from Node failed due to truncated length, Most likely caused by a collision.
    0x0004: "RcParseFail", # Unable to identify last UDP transmission. Check OpCode and packet length.
    0x0005: "RcUdpFail", # Unable to open Udp Socket in last transmission attempt
    0x0006: "RcShNameOk", # Confirms that Short Name programming via ArtAddress, was successful.
    0x0007: "RcLoNameOk", # Confirms that Long Name programming via ArtAddress, was successful.
    0x0008: "RcDmxError", # DMX512 receive errors detected.
    0x0009: "RcDmxUdpFull", # Ran out of internal DMX transmit buffers.
    0x000a: "RcDmxRxFull", # Ran out of internal DMX Rx buffers.
    0x000b: "RcSwitchErr", # Rx Universe switches conflict.
    0x000c: "RcConfigErr", # Product configuration does not match firmware.
    0x000d: "RcDmxShort", # DMX output short detected. See GoodOutput field.
    0x000e: "RcFirmwareFail", # Last attempt to upload new firmware failed.
    0x000f: "RcUserFail", # User changed switch settings when address locked by remote programming. User changes ignored.
    0x0010: "RcFactoryRes", # Factory reset has occurred.
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
        ByteEnumField("status", 0, STATUS_CODES),
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
        ByteEnumField("style", 0, STYLE_CODES),
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

class ArtNet_NZS(Packet):
    name = "NZS"
    fields_desc = [
        ByteField("sequence", 0), # to fix for out-of-order delivery. 0 is disable
        ByteField("startcode", 0),
        ByteField("physical", 0),
        LEShortField("universe", 0),
        LenField("data_length", None, fmt=">H") # should be always 512
    ]

bind_layers(ArtNet, ArtNet_NZS, opcode=0x5100)

# add other packets; https://github.com/OpenLightingProject/libartnet/blob/master/artnet/packets.h
