import queue
import socket
import time
import traceback
from network import Network, ProtocolStatusCodes, PackageKind

all_incoming_packets = queue.Queue()  # a queue for all incoming packets


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
        while not client_info.should_terminate:
            temp = Network.receive_data(client_info.incoming_socket, client_info.client_id)

            if temp is not None:  # temp is None on timeout
                status, package = temp

                match status:
                    case ProtocolStatusCodes.ALL_GOOD:
                        if package.kind != PackageKind.EXIT_KIND:
                            all_incoming_packets.put(package)

                    case ProtocolStatusCodes.SOCKET_DISCONNECTED | ProtocolStatusCodes.SOCKET_CONNECTION_ERROR:
                        print('Seems server disconnected abnormally')
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


def client_outgoing_thread_handler(client_info: ClientCommunicationInfo):
    print(f"Started outgoing thread handler for {client_info.client_id}!")

    try:
        while not client_info.should_terminate:
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


def established_client_communication_threads(client_info: ClientCommunicationInfo):
    pass
