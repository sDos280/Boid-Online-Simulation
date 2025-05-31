import enum
import socket
import traceback
from logger_utils import create_formatted_logger  # Make sure this is the correct import path
from network_vars import PackageKind

logger = create_formatted_logger()

# The length of the network package field (in bytes), used for defining a network package
NETWORK_PACKAGE_LENGTH_FIELD_SIZE = 32 // 8  # 32 bit / 8 bit per char
NETWORK_PACKAGE_KIND_FIELD_SIZE = 1  # 1 byte == 0xFF


class Package:
    def __init__(self, kind: PackageKind, payload: bytes | str):
        self.kind = kind
        self.payload = payload.encode() if isinstance(payload, str) else payload


class ProtocolStatusCodes(enum.IntEnum):
    ALL_GOOD = 0
    GENERAL_ERROR = 1
    NONE_INTEGER_LENGTH_FIELD = 2
    INCOMPATIBLE_LENGTH_FIELD = 3
    NONE_INTEGER_KIND_FIELD = 4
    MESSAGE_TOO_LARGE = 5
    TOO_MANY_KINDS = 6
    SOCKET_CONNECTION_ERROR = 7
    SOCKET_DISCONNECTED = 8


def get_max_package_length():
    return 10 ** NETWORK_PACKAGE_LENGTH_FIELD_SIZE - 1


class Network:
    @staticmethod
    def log_transmission(direction: str, byte_data: bytes | str, tid: int = -1):
        prefix = f"{tid} " if tid >= 0 else ""
        direction_str = "Sent >>>" if direction == 'sent' else "Received <<<"
        logger.info(f'{prefix}S LOG:{direction_str} {byte_data}')

    @staticmethod
    def send_data(sock: socket.socket, package: Package, tid: int = -1, log: bool = True) -> tuple[ProtocolStatusCodes, str]:
        if len(package.payload) + NETWORK_PACKAGE_LENGTH_FIELD_SIZE + NETWORK_PACKAGE_KIND_FIELD_SIZE > get_max_package_length():
            return ProtocolStatusCodes.MESSAGE_TOO_LARGE, f"The message is too large, len={len(package.payload)}"

        if package.kind // 0xFF > NETWORK_PACKAGE_KIND_FIELD_SIZE:
            return ProtocolStatusCodes.MESSAGE_TOO_LARGE, f"The kind field is too large, len={package.kind // 0xFF}, value={package.kind}"

        header = (len(package.payload) + NETWORK_PACKAGE_LENGTH_FIELD_SIZE + NETWORK_PACKAGE_KIND_FIELD_SIZE).to_bytes(NETWORK_PACKAGE_LENGTH_FIELD_SIZE)
        header += package.kind.to_bytes(NETWORK_PACKAGE_KIND_FIELD_SIZE, byteorder='big')
        bytearray_data = header + package.payload

        try:
            sock.send(bytearray_data)
        except socket.error as err:
            logger.error(f'Socket Error send_data: {err}')
            return ProtocolStatusCodes.SOCKET_CONNECTION_ERROR, str(err)
        except Exception as err:
            logger.error(f'General Error send_data: {err}\n{traceback.format_exc()}')
            return ProtocolStatusCodes.GENERAL_ERROR, str(err)

        if log:
            Network.log_transmission('sent', bytearray_data, tid)

        return ProtocolStatusCodes.ALL_GOOD, ""

    @staticmethod
    def receive_data(sock: socket.socket, tid: int = -1, log: bool = True) -> tuple[ProtocolStatusCodes, Package] | None:
        def receive_data_main() -> tuple[ProtocolStatusCodes, Package, bytes] | None:
            try:
                all_bytes = b""
                length_field = sock.recv(NETWORK_PACKAGE_LENGTH_FIELD_SIZE)
                all_bytes += length_field

                if length_field == b"":
                    return ProtocolStatusCodes.SOCKET_DISCONNECTED, Package(PackageKind(0), b""), all_bytes

                try:
                    length_field = int.from_bytes(length_field, byteorder='big')
                except ValueError as err:
                    return ProtocolStatusCodes.NONE_INTEGER_LENGTH_FIELD, Package(PackageKind(0), str(err).encode()), all_bytes

                if length_field < 0:
                    return ProtocolStatusCodes.NONE_INTEGER_LENGTH_FIELD, Package(PackageKind(0), f"length_field={length_field}".encode()), all_bytes

                kind_field = sock.recv(NETWORK_PACKAGE_KIND_FIELD_SIZE)
                all_bytes += kind_field
                try:
                    kind_field = int.from_bytes(kind_field, byteorder='big')
                except ValueError as err:
                    return ProtocolStatusCodes.NONE_INTEGER_KIND_FIELD, Package(PackageKind(0), str(err).encode()), all_bytes

                payload_length = length_field - NETWORK_PACKAGE_LENGTH_FIELD_SIZE - NETWORK_PACKAGE_KIND_FIELD_SIZE
                received_data = b""

                if payload_length > 0:
                    received_data = sock.recv(payload_length)
                    all_bytes += received_data

                    if received_data == b"":
                        return ProtocolStatusCodes.SOCKET_DISCONNECTED, Package(PackageKind(kind_field), b""), all_bytes

                while len(received_data) != payload_length:
                    new_data = sock.recv(payload_length - len(received_data))
                    all_bytes += new_data

                    if new_data == b"":
                        return ProtocolStatusCodes.SOCKET_DISCONNECTED, Package(PackageKind(kind_field), received_data), all_bytes

                    received_data += new_data

                return ProtocolStatusCodes.ALL_GOOD, Package(PackageKind(kind_field), received_data), all_bytes

            except socket.timeout:
                return None  # Timeout is not an error
            except socket.error as err:
                logger.error(f'Socket Error receive_data: {err}\n{traceback.format_exc()}')
                return ProtocolStatusCodes.SOCKET_CONNECTION_ERROR, Package(PackageKind(0), str(err).encode()), b""
            except Exception as err:
                logger.error(f'General Error receive_data: {err}\n{traceback.format_exc()}')
                return ProtocolStatusCodes.GENERAL_ERROR, Package(PackageKind(0), str(err).encode()), b""

        result = receive_data_main()

        if result is not None:
            status, package, raw_bytes = result
            if package.payload != b"" and log:
                Network.log_transmission("recv", raw_bytes, tid)

        return result[:-1] if result is not None else None
