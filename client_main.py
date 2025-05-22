import threading
import logging
import queue
from raylibpy import *
from boid_helper import get_triangle_points, deserialize_boids
from network import Package, PackageKind
from boid import Boid
from client_network import communicating_setup, setup_client_variables, get_shutdown, set_shutdown, setup_incoming_packets_thread, setup_outgoing_packets_thread

incoming_packets: queue.Queue[Package] = queue.Queue()  # a queue for all incoming packets
outgoing_packets: queue.Queue[Package] = queue.Queue()  # a queue for all outgoing packets

logger = logging.getLogger(__name__)

shutdown = False  # a flag to indicate if the client should shut down


def setup_network():
    logger.debug("Setting up client-server communication...")
    incoming_socket, outgoing_socket = communicating_setup()
    incoming_socket.settimeout(2.0)

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

    init_window(800, 450, "Client view")

    set_target_fps(60)

    last = b""
    boids: list[Boid] = []
    new_boids: list[Boid] = []

    while not window_should_close() and get_shutdown() is False:
        # Update
        # check if there is any incoming packet

        while not incoming_packets.empty():
            packet = incoming_packets.get()

            # Process the packet
            match packet.kind:
                case PackageKind.BOIDS_STATE:
                    # Update boids state
                    boids = deserialize_boids(packet.payload)
                case PackageKind.ERROR:
                    logger.error(f"Error packet received: {packet.payload.decode('utf-8')}")
                case _:
                    logger.warning(f"Unknown packet kind received: {packet.kind.name}")

            incoming_packets.task_done()

        begin_drawing()
        clear_background(RAYWHITE)

        # Draw
        for boid in boids:
            points = get_triangle_points(boid.x, boid.y, boid.vx, boid.vy, 10)
            point1 = Vector2(points[0][0], points[0][1])
            point2 = Vector2(points[1][0], points[1][1])
            point3 = Vector2(points[2][0], points[2][1])

            draw_triangle(point1, point3, point2, BLUE)

        draw_fps(10, 10)

        end_drawing()

    close_window()

    shutdown_network(incoming_thread, outgoing_thread)
