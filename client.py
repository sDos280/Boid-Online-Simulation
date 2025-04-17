import raylibpy as rl
import socket
import network_vars
import network


def communicating_setup():
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_socket.connect((network_vars.SERVER_IP, network_vars.SERVER_SETUP_PORT))

    incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    incoming_socket.bind(("0.0.0.0", 0))

    # send incoming socket port to server
    network.Network.send(temp_socket, network_vars.PacketType.CLIENT_SETUP, int.to_bytes(incoming_socket.getsockname()[1], 2, 'big'))

    # get server's outgoing socket port
    packet_type, data = network.Network.receive(temp_socket)

    if packet_type != network_vars.PacketType.CLIENT_SETUP:
        raise network.UnexpectedPacketType("Server did not respond with CLIENT_SETUP packet")
    outgoing_socket_port = int.from_bytes(data, 'big')

    # bind to server's outgoing socket port
    outgoing_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    outgoing_socket.connect((network_vars.SERVER_IP, outgoing_socket_port))

    # setup incoming and outgoing socket
    incoming_socket.listen(1)

    servers_incoming_socket, _ = incoming_socket.accept()

    temp_socket.close()

    return servers_incoming_socket, outgoing_socket


def main():
    incoming_socket, outgoing_socket = communicating_setup()
