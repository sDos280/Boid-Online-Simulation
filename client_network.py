import socket
import time
import logging
import threading
from network_vars import *
from network import Network, ProtocolStatusCodes, Package, PackageKind

__incoming_packets = None  # a queue for all incoming packets
__outgoing_packets = None  # a queue for all outgoing packets

logger = logging.getLogger(__name__)

__shutdown = False  # a flag to indicate if the client should shut down


def setup_incoming_packets_thread(incoming_socket):
    """
    This function sets up a thread to handle incoming packets from the server.
    It runs in a loop, receiving data from the socket and putting it into the incoming_packets queue.
    """

    logger.debug("Starting incoming packets thread...")

    global __shutdown

    while not __shutdown:
        temp = Network.receive_data(incoming_socket, log=False)

        if temp is not None:  # temp is None on timeout
            status, package = temp

            match status:
                case ProtocolStatusCodes.ALL_GOOD:
                    if package.kind != PackageKind.EXIT_KIND:
                        __incoming_packets.put(package)
                    else:
                        logger.debug("Received exit package, shutting down...")
                        __shutdown = True
                        break

                case ProtocolStatusCodes.SOCKET_DISCONNECTED | ProtocolStatusCodes.SOCKET_CONNECTION_ERROR:
                    logger.fatal('Seems server disconnected abnormally')
                    __shutdown = True
                    break
                case _:
                    logger.fatal(f'Something went wrong: {status} : {PackageKind(package.kind).name} : {package.payload}')
                    __shutdown = True
                    break

    logger.debug("Incoming packets thread shutting down...")


def setup_outgoing_packets_thread(outgoing_socket):
    logger.debug("Starting outgoing packets thread...")

    while not __shutdown:
        if not __outgoing_packets.empty():
            kind, data = __outgoing_packets.get()

            Network.send_data(outgoing_socket, kind, data, log=False)

            __outgoing_packets.task_done()

        time.sleep(1 / 10)

    logger.debug("Outgoing packets thread shutting down...")


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


def setup_client_variables(incoming_queue, outgoing_queue):
    """
    This function sets up the global variables for incoming and outgoing packets.
    It is called at the beginning of the program to initialize the queues.
    """
    global __incoming_packets
    global __outgoing_packets

    __incoming_packets = incoming_queue
    __outgoing_packets = outgoing_queue


def get_shutdown():
    """
    This function returns the shutdown flag.
    It is used to check if the threads should shut down.
    """
    global __shutdown
    return __shutdown


def set_shutdown(value):
    """
    This function sets the shutdown flag to the given value.
    It is used to signal the threads to shut down.
    """
    global __shutdown
    __shutdown = value


if __name__ == '__main__':
    incoming_socket, outgoing_socket = communicating_setup()

    # Start the incoming and outgoing threads
    incoming_thread = threading.Thread(target=setup_incoming_packets_thread, args=(incoming_socket,))
    outgoing_thread = threading.Thread(target=setup_outgoing_packets_thread, args=(outgoing_socket,))

    incoming_thread.start()
    outgoing_thread.start()

    while True:
        pass

    # Wait for the threads to finish
    incoming_thread.join()
    outgoing_thread.join()
