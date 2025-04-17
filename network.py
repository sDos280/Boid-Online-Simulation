import socket
import network_vars


class UnsuccessfulCommunication(Exception):
    """
    Exception raised when a communication attempt is unsuccessful.
    """
    pass


class ConnectionSevered(Exception):
    """
    Exception raised when a connection is severed.
    """
    pass


class UnexpectedPacketType(Exception):
    """
    Exception raised when an unexpected packet type is received.
    """
    pass


class Network:
    @staticmethod
    def send(socket: socket.socket, type: network_vars.PacketType, data: bytes):
        """
        Send data to a socket.
        :param socket: The socket to send data to.
        :param type: The type of packet to send.
        :param data: The data to send.
        """
        # add type field
        to_send = int.to_bytes(type.value, network_vars.PACKET_TYPE_FIELD_LENGTH, 'big')
        to_send += data

        # add length field
        try:
            to_send = int.to_bytes(len(to_send), network_vars.PACKET_TYPE_FIELD_LENGTH, 'big') + to_send
        except OverflowError:
            raise UnsuccessfulCommunication("Data size exceeds maximum limit")

        if len(to_send) > network_vars.MAX_PACKET_SIZE:
            raise UnsuccessfulCommunication("Packet size exceeds maximum limit")

        # send data
        sent = socket.send(data)

        if sent != len(data):
            raise UnsuccessfulCommunication("Not all data sent")

    @staticmethod
    def receive(socket: socket.socket) -> tuple[network_vars.PacketType, bytes]:
        """
        Receive data from a socket.
        :param socket: The socket to receive data from.
        :return: A tuple containing the packet type and the data.
        """
        # receive length field
        length_field = socket.recv(network_vars.PACKET_SIZE_FIELD_LENGTH)

        if length_field == b'':
            raise ConnectionSevered("The connection was closed")

        length = int.from_bytes(length_field, 'big')

        # receive type field
        type_field = socket.recv(network_vars.PACKET_TYPE_FIELD_LENGTH)
        if type_field == b'':
            raise ConnectionSevered("The connection was closed")

        packet_type_type = network_vars.PacketType(int.from_bytes(type_field, 'big'))

        # receive data
        application_data = socket.recv(length - network_vars.PACKET_SIZE_FIELD_LENGTH - network_vars.PACKET_TYPE_FIELD_LENGTH)

        if application_data == b'':
            raise ConnectionSevered("The connection was closed")

        return packet_type_type, application_data


class OutgoingChannel:
    pass


class IncomingChannel:
    pass
