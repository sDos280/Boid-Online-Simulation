import enum

SERVER_IP = "127.0.0.1"
SERVER_SETUP_PORT = 5000

MAX_PACKET_SIZE = 0xFFFF  # max packet size in bytes (the maximum size of allowed transferable data, AKA ALL DATA)
# the size field the responsible for representing the amount of application data and packet type data in the packet
PACKET_SIZE_FIELD_LENGTH = 2  # the length of the field size in bytes, 2 bytes <= 0xFFFF
PACKET_TYPE_FIELD_LENGTH = 1  # the length of the field type in bytes, 1 byte == 0xFF


class PackageKind(enum.IntEnum):
    EXIT_KIND = 0xFF
