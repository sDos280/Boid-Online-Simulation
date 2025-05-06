import enum
import socket
import traceback

from cryptography.fernet import Fernet

from network_vars import PackageKind

# The length of the network package field (in bytes), used for defining a network package
NETWORK_PACKAGE_LENGTH_FIELD_SIZE = 32 // 8  # 32 bit / 8 bit per char
NETWORK_PACKAGE_KIND_FIELD_SIZE = 4


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


class EncryptionHandler:
    def __init__(self, key=Fernet.generate_key()):
        self.key: bytes = key
        self.fernet_obj = Fernet(key)

    def encrypt(self, data: bytes):
        return self.fernet_obj.encrypt(data)

    def decrypt(self, data: bytes):
        return self.fernet_obj.decrypt(data)

    def update_key(self, key: bytes):
        self.key: bytes = key
        self.fernet_obj = Fernet(key)


class Network:
    """
    A utility class for handling network operations, including sending and receiving data over a TCP connection,
    logging data transmissions, and checking the format of transmitted data.

    Methods:
        log_transmission(direction, byte_data, tid=-1):
            Logs the transmission direction, transaction ID (tid), and the TCP byte data.

        check_format(byte_data):
            Checks the format of the byte data to ensure it meets protocol specifications.

        send_data(sock, kind_field, byte_data, tid=-1, log=True):
            Sends byte data over a socket connection with an additional kind field and optional logging.

        receive_data(sock, tid=-1, log=True):
            Receives byte data from a socket connection, including length and kind fields, with logging.
    """

    @staticmethod
    def log_transmission(direction: str, byte_data: bytes | str, tid: int = -1):
        """
        Logs the transmission details, including the direction (sent/received), transaction ID (tid),
        and the byte data being transmitted. The log format differs based on the presence of a valid tid.

        Args:
            direction (str): The direction of the transmission, either 'sent' or 'received'.
            byte_data (bytes | str): The TCP byte data to log.
            tid (int, optional): The transaction ID associated with the transmission. Defaults to -1.

        Returns:
            None
        """
        if tid >= 0:
            if direction == 'sent':
                print(f'{tid} S LOG:Sent     >>> {byte_data}')
            else:
                print(f'{tid} S LOG:Received <<< {byte_data}')
        else:
            if direction == 'sent':
                print(f'LOG:Sent     >>> {byte_data}')
            else:
                print(f'LOG:Received <<< {byte_data}')

    @staticmethod
    def check_format(byte_data: bytes):
        """
        Checks the format of the byte data to ensure it follows the protocol requirements.
        Specifically, it validates the length field and compares the data length.

        Args:
            byte_data (bytes): The byte data to check.

        Returns:
            ProtocolStatusCodes: A status code indicating whether the data format is valid or not.
        """
        length_field = byte_data[0:NETWORK_PACKAGE_LENGTH_FIELD_SIZE]

        try:
            length_field = int(length_field)
        except ValueError:
            return ProtocolStatusCodes.NONE_INTEGER_LENGTH_FIELD

        if 0 < length_field < NETWORK_PACKAGE_LENGTH_FIELD_SIZE:
            return ProtocolStatusCodes.INCOMPATIBLE_LENGTH_FIELD

        kind_field = byte_data[NETWORK_PACKAGE_LENGTH_FIELD_SIZE:NETWORK_PACKAGE_LENGTH_FIELD_SIZE + NETWORK_PACKAGE_KIND_FIELD_SIZE]

        try:
            kind_field = int(kind_field)
        except ValueError:
            return ProtocolStatusCodes.NONE_INTEGER_KIND_FIELD

        return ProtocolStatusCodes.ALL_GOOD if len(byte_data) == length_field else ProtocolStatusCodes.INCOMPATIBLE_LENGTH_FIELD

    @staticmethod
    def send_data(sock: socket.socket, kind_field: enum.Enum | enum.IntEnum | int, byte_data: bytes | str, tid: int = -1, log: bool = True) -> tuple[ProtocolStatusCodes, str]:
        """
        Sends byte data over a socket connection, prefixed with a length field and a kind field.
        Logs the data if logging is enabled. Handles socket errors and general exceptions gracefully.

        Args:
            sock (socket.socket): The socket through which data is sent.
            kind_field (enum.Enum): The kind field that specifies the type of the message being sent.
            byte_data (bytes): The data to be sent.
            tid (int, optional): The transaction ID for logging purposes. Defaults to -1.
            log (bool, optional): Whether to log the transmission. Defaults to True.

        Returns:
            tuple: A status code from ProtocolStatusCodes and an error message or an empty string.

        Raises:
            ValueError: If the message or kind field exceeds the allowed size.
        """
        if isinstance(byte_data, str):
            byte_data = byte_data.encode()

        if len(byte_data) + NETWORK_PACKAGE_LENGTH_FIELD_SIZE + NETWORK_PACKAGE_KIND_FIELD_SIZE > get_max_package_length():
            return ProtocolStatusCodes.MESSAGE_TOO_LARGE, f"The message is too large, len={len(byte_data)}"

        if len(str(kind_field)) > NETWORK_PACKAGE_KIND_FIELD_SIZE:
            return ProtocolStatusCodes.MESSAGE_TOO_LARGE, f"The kind field is too large, len={len(str(kind_field))}"

        header = str(len(byte_data) + NETWORK_PACKAGE_LENGTH_FIELD_SIZE + NETWORK_PACKAGE_KIND_FIELD_SIZE).zfill(NETWORK_PACKAGE_LENGTH_FIELD_SIZE).encode()
        header += str(kind_field).zfill(NETWORK_PACKAGE_KIND_FIELD_SIZE).encode()
        payload = byte_data

        bytearray_data = header + payload

        try:
            sock.send(bytearray_data)
        except socket.error as err:
            print(f'Socket Error send_data: {err}')
            return ProtocolStatusCodes.SOCKET_CONNECTION_ERROR, f"{err}"
        except Exception as err:
            print(f'Socket Error send_data: {err}')
            print(traceback.format_exc())
            return ProtocolStatusCodes.GENERAL_ERROR, f"{err}"

        if log:
            Network.log_transmission('sent', bytearray_data, tid)

        return ProtocolStatusCodes.ALL_GOOD, ""

    @staticmethod
    def receive_data(sock: socket.socket, tid: int = -1, log: bool = True) -> tuple[ProtocolStatusCodes, PackageKind, bytes]:
        """
        Receives byte data from a socket connection. Handle cases where the data is received in
        chunks, ensuring all data is properly gathered, including the length and kind fields.
        Logs the data if logging is enabled.

        Args:
            sock (socket.socket): The socket from which data is received.
            tid (int, optional): The transaction ID for logging purposes. Defaults to -1.
            log (bool, optional): Whether to log the received data. Defaults to True.

        Returns:
            tuple: A status code from ProtocolStatusCodes, the kind field (as an integer), and
                   the received data as a string, or an error message.

        Raises:
            socket.error: If a socket error occurs.
            Exception: For other general errors.
        """

        def receive_data_main() -> tuple[ProtocolStatusCodes, PackageKind, bytes, bytes] | None:
            # TODO: make sure the number of bytes for the package length and for the kind is always of right length
            try:
                all_bytes = b""
                length_field = sock.recv(NETWORK_PACKAGE_LENGTH_FIELD_SIZE)
                all_bytes += length_field

                if length_field == b"":
                    return ProtocolStatusCodes.SOCKET_DISCONNECTED, PackageKind(0), "".encode(), all_bytes

                try:
                    length_field = int(length_field)
                except ValueError as err:
                    return ProtocolStatusCodes.NONE_INTEGER_LENGTH_FIELD, PackageKind(0), f"{err}".encode(), all_bytes

                if length_field < 0:
                    return ProtocolStatusCodes.NONE_INTEGER_LENGTH_FIELD, PackageKind(0), f"length_field={length_field}".encode(), all_bytes

                kind_field = sock.recv(NETWORK_PACKAGE_KIND_FIELD_SIZE)
                all_bytes += kind_field
                try:
                    kind_field = int(kind_field)
                except ValueError as err:
                    return ProtocolStatusCodes.NONE_INTEGER_KIND_FIELD, PackageKind(0), f"{err}".encode(), all_bytes

                if length_field - NETWORK_PACKAGE_LENGTH_FIELD_SIZE - NETWORK_PACKAGE_KIND_FIELD_SIZE != 0:
                    received_data = sock.recv(length_field - NETWORK_PACKAGE_LENGTH_FIELD_SIZE - NETWORK_PACKAGE_KIND_FIELD_SIZE)
                    all_bytes += received_data

                    if received_data == b"":
                        return ProtocolStatusCodes.SOCKET_DISCONNECTED, PackageKind(kind_field), "".encode(), all_bytes
                else:
                    # no data is needed to be received
                    received_data = b""

                while len(received_data) != length_field - NETWORK_PACKAGE_LENGTH_FIELD_SIZE - NETWORK_PACKAGE_KIND_FIELD_SIZE:
                    new_data = sock.recv(length_field - NETWORK_PACKAGE_LENGTH_FIELD_SIZE - len(received_data))
                    all_bytes += new_data

                    # this could fail if length_field - NETWORK_PACKAGE_LENGTH_FIELD_SIZE - len(received_data) == 0 TODO: rethink on this
                    if new_data == b"":
                        return ProtocolStatusCodes.SOCKET_DISCONNECTED, PackageKind(kind_field), (received_data + new_data), all_bytes

                    received_data += new_data

                return ProtocolStatusCodes.ALL_GOOD, PackageKind(kind_field), received_data, all_bytes
            except socket.timeout as err:
                return None  # a timeout shouldn't be a problem
            except socket.error as err:
                print(f'Socket Error receive_data: {err}')
                print(traceback.format_exc())
                return ProtocolStatusCodes.SOCKET_CONNECTION_ERROR, PackageKind(0), f"{err}".encode(), b""
            except Exception as err:
                print(f'Socket Error receive_data: {err}')
                print(traceback.format_exc())
                return ProtocolStatusCodes.GENERAL_ERROR, PackageKind(0), f"{err}".encode(), b""

        temp = receive_data_main()

        if temp is not None:
            status, _kind_field, output, _all_bytes = temp

            if output != b"" and log:
                Network.log_transmission("recv", _all_bytes, tid)

        return temp[:-1] if temp is not None else None
