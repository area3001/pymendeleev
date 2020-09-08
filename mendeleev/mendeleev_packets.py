from scapy.packet import Packet
from scapy.fields import *

ELEMENTS = {
       0: "Master",
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
     255: "Broadcast"
}

COMMANDS = {
    0x00: "setcolor",
    0x01: "setmode",
    0x02: "ota",
    0x03: "version",
    0x04: "setoutput",
    0x05: "reboot"
}

MODES = {
    0x01: "guest",
    0x02: "teacher"
}

class MendeleevHeader(Packet):
    name = 'Mendeleev header'
    fields_desc = [
        ByteEnumField("destination", 0xFF, ELEMENTS),
        ByteEnumField("source", 0, ELEMENTS),
        LEShortField("sequence_nr", None),
        ByteEnumField("command", 0, COMMANDS),
        LEShortField("length", None),
        XLEShortField("crc", None) # CRC-16/KERMIT
    ]

    @staticmethod
    def compute_crc16(data, poly=0x8408):
        '''
        CRC-16-CCITT Algorithm
        '''
        data = bytearray(data)
        crc = 0xFFFF
        for b in data:
            cur_byte = 0xFF & b
            for _ in range(0, 8):
                if (crc & 0x0001) ^ (cur_byte & 0x0001):
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
                cur_byte >>= 1
        crc = (~crc & 0xFFFF)
        crc = (crc << 8) | ((crc >> 8) & 0xFF)

        return crc & 0xFFFF

    def post_build(self, p, pay):
        # Switch payload and crc
        length = p[5:7] if self.length is not None else struct.pack('<H', len(pay))
        crc = p[-2:]
        p = p[:5] + length + pay
        p += crc if self.crc is not None else struct.pack('<H', self.compute_crc16(p))
        return p

    def post_dissect(self, s):
        self.raw_packet_cache = None  # Reset packet to allow post_build
        return s

    def pre_dissect(self, s):
        # Switch payload and crc
        length = struct.unpack('<H', s[5:7])[0]
        data, s = s[:length+7], s[length+7:]
        crc = struct.unpack('<H', data[-2:])[0]
        calc_crc = self.compute_crc16(data[:-2])
        if crc != calc_crc:
            raise Scapy_Exception("Wrong checksum: %d != %d" % (crc, calc_crc))
        return data[:7] + data[-2:] + data[7:-2] + s

    def answers(self, other):

        if ((self.command == other.command) or \
            (self.command == (~other.command & 0xFF))) and \
            self.sequence_nr == other.sequence_nr:
            return self.payload.answers(other.payload)
        return 0
