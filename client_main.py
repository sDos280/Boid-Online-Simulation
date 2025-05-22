import threading
import logging
import queue
from client_network import communicating_setup, setup_client_variables, set_shutdown, setup_incoming_packets_thread, setup_outgoing_packets_thread

incoming_packets = queue.Queue()  # a queue for all incoming packets
outgoing_packets = queue.Queue()  # a queue for all outgoing packets

logger = logging.getLogger(__name__)

shutdown = False  # a flag to indicate if the client should shut down


def setup_network():
    logger.debug("Setting up client-server communication...")
    incoming_socket, outgoing_socket = communicating_setup()

    logger.debug("Setting up client network variables")
    set_shutdown(False)
    setup_client_variables(incoming_packets, outgoing_packets)

    # Start the incoming and outgoing threads
    incoming_thread = threading.Thread(target=setup_incoming_packets_thread, args=(incoming_socket,))
    outgoing_thread = threading.Thread(target=setup_outgoing_packets_thread, args=(outgoing_socket,))

    incoming_thread.start()
    outgoing_thread.start()

    return incoming_thread, outgoing_thread


def shutdown_network(incoming_thread, outgoing_thread):
    logger.debug("Shutting down client network...")
    set_shutdown(True)  # Set the shutdown flag to True

    # Wait for the threads to finish
    incoming_thread.join()
    outgoing_thread.join()

    logger.debug("Client network shut down successfully.")


if __name__ == '__main__':
    incoming_thread, outgoing_thread = setup_network()

    while True:
        pass

    shutdown_network(incoming_thread, outgoing_thread)
