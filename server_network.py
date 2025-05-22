import queue
import socket
import time
import traceback
import threading
from network_vars import *
from network import Network, Package, ProtocolStatusCodes, PackageKind
import logging

logger = logging.getLogger(__name__)

__all_incoming_packets = None  # a queue for all incoming packets

shutdown = False  # a flag to indicate if the server should shut down

__all_client_infos = None  # a list to store all client information


class ClientCommunicationInfo:
    def __init__(self, outgoing_socket, incoming_socket, client_address, client_id: int = -1):
        self.outgoing_socket = outgoing_socket
        self.incoming_socket = incoming_socket
        self.client_address = client_address
        self.incoming_queue = queue.Queue()  # EXAMINE: this may not be needed
        self.outgoing_queue = queue.Queue()
        self.client_id = client_id
        self.should_terminate = False


def client_incoming_thread_handler(client_info: ClientCommunicationInfo):
    print(f"Started incoming thread handler for {client_info.client_id}!")

    try:
        while not client_info.should_terminate and not shutdown:
            temp = Network.receive_data(client_info.incoming_socket, client_info.client_id)

            if temp is not None:  # temp is None on timeout
                status, package = temp

                match status:
                    case ProtocolStatusCodes.ALL_GOOD:
                        if package.kind != PackageKind.EXIT_KIND:
                            __all_incoming_packets.put(package)

                    case ProtocolStatusCodes.SOCKET_DISCONNECTED | ProtocolStatusCodes.SOCKET_CONNECTION_ERROR:
                        print('Seems client disconnected abnormally')
                        client_info.should_collapse = True
                        break
                    case _:
                        print(f'Something went wrong: {status} : {PackageKind(package.kind).name} : {package.payload}')
                        client_info.should_collapse = True
                        break

            time.sleep(1 / 10)

    except socket.error as err:
        print(f'Got socket error: {err}')
        client_info.should_terminate = True
    except Exception as err:
        print(f'General error: {err}')
        print(traceback.format_exc())
        client_info.should_terminate = True

    print(f"Ended incoming thread handler for {client_info.client_id}!")

    client_info.incoming_socket.close()


def client_outgoing_thread_handler(client_info: ClientCommunicationInfo):
    print(f"Started outgoing thread handler for {client_info.client_id}!")

    try:
        while not client_info.should_terminate and not shutdown:
            if not client_info.outgoing_queue.empty():
                kind, data = client_info.outgoing_queue.get()

                Network.send_data(client_info.outgoing_socket, kind, data)

                client_info.outgoing_queue.task_done()

            time.sleep(1 / 10)

    except socket.error as err:
        print(f'Got socket error: {err}')
        client_info.should_terminate = True
    except Exception as err:
        print(f'General error: {err}')
        print(traceback.format_exc())
        client_info.should_terminate = True

    print(f"Ended outgoing thread handler for {client_info.client_id}!")

    client_info.outgoing_socket.close()


# this function creates a mini server that his only job is to establish a connection with the client
def client_communication_establish_server_thread(server_establish_socket: socket.socket):
    global shutdown

    print('Client\'s communication establish server started!')

    client_id = 0

    while not shutdown:
        try:
            client_establish_socket, address = server_establish_socket.accept()

            print(f'Client connected from {address}')

            # create new random sockets for the incoming and outgoing communication
            binding_outgoing_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            binding_outgoing_socket.bind((SERVER_IP, 0))
            binding_outgoing_socket.listen(1)
            binding_incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            binding_incoming_socket.bind((SERVER_IP, 0))
            binding_incoming_socket.listen(1)

            print(f"Client {client_id}: Initialize port {binding_outgoing_socket.getsockname()[1]} for outgoing communication")
            print(f"Client {client_id}: Initialize port {binding_incoming_socket.getsockname()[1]} for incoming communication")

            # send the port of the new sockets to the client
            Network.send_data(client_establish_socket,
                              Package(PackageKind.ESTABLISH_CONNECTION,
                                      binding_outgoing_socket.getsockname()[1].to_bytes(2, 'big') +
                                      binding_incoming_socket.getsockname()[1].to_bytes(2, 'big')),
                              tid=client_id)

            # wait for the client to connect to the incoming and outgoing sockets
            outgoing_socket, address1 = binding_outgoing_socket.accept()
            incoming_socket, address2 = binding_incoming_socket.accept()

            # add timeout to the incoming socket
            incoming_socket.settimeout(2.0)

            client_info = ClientCommunicationInfo(outgoing_socket, incoming_socket, address, client_id)

            # add the client info to the list
            __all_client_infos.append(client_info)

            # start the threads
            threading.Thread(target=client_incoming_thread_handler, args=(client_info,)).start()
            threading.Thread(target=client_outgoing_thread_handler, args=(client_info,)).start()

            client_id += 1

            # client_establish_socket.close()
        except socket.error as err:
            print(f'Error: client_communication_establish_server_thread: {err}')
            print(traceback.format_exc())
            shutdown = True

    server_establish_socket.close()


def server_establish_connection():
    server_establish_socket = socket.socket()
    server_establish_socket.bind((SERVER_IP, SERVER_SETUP_PORT))
    server_establish_socket.listen(20)

    # start the server
    threading.Thread(target=client_communication_establish_server_thread, args=(server_establish_socket,)).start()

    return server_establish_socket


def setup_server_variables(all_incoming_packets: queue.Queue, all_client_infos: list[ClientCommunicationInfo]):
    global __all_incoming_packets, __all_client_infos
    __all_incoming_packets = all_incoming_packets

    __all_client_infos = all_client_infos


if __name__ == '__main__':
    setup_server_variables(queue.Queue(), [])
    server_establish_socket = server_establish_connection()

    try:
        while True:
            input_text = input("Press Enter to exit the server...")
            if input_text == "":
                shutdown = True
                print("Shutting down server...")
                break
    except KeyboardInterrupt:
        shutdown = True

        print("Shutting down server...")

    server_establish_socket.close()
