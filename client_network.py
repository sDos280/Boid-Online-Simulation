import socket
from network_vars import *
from network import Network, ProtocolStatusCodes, Package, PackageKind


def communicating_setup():
    # Connect to server setup server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_SETUP_PORT))

    # Receive the ports for incoming and outgoing communication
    status, package = Network.receive_data(client_socket)

    if status != ProtocolStatusCodes.ALL_GOOD:
        raise Exception("Failed to establish connection with server setup server")

    # Unpack the ports [servers' outgoing port, servers' incoming port]
    incoming_port, outgoing_port = package.payload[0:2], package.payload[2:4]

    incoming_port = int.from_bytes(incoming_port, byteorder='big')
    outgoing_port = int.from_bytes(outgoing_port, byteorder='big')

    print(f"Incoming port: {incoming_port}, Outgoing port: {outgoing_port}")
    # create the incoming and outgoing sockets
    incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    incoming_socket.connect((SERVER_IP, incoming_port))

    outgoing_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    outgoing_socket.connect((SERVER_IP, outgoing_port))

    return incoming_socket, outgoing_socket


if __name__ == '__main__':
    incoming_socket, outgoing_socket = communicating_setup()

    while True:
        pass
