import threading
import logging
import queue
import time

from raylibpy import *
from boid_helper import get_triangle_points, deserialize_boids, generate_random_velocity_boid
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
    outgoing_packets.put(Package(PackageKind.EXIT_KIND, b""))

    time.sleep(1)  # Give some time for the exit package to be sent

    set_shutdown(True)  # Set the shutdown flag to True

    # Wait for the threads to finish
    incoming_thread.join()
    outgoing_thread.join()

    logger.debug("Client network shut down successfully.")


def get_closest_boid_to_point(boids: list[Boid], point: tuple[float, float]) -> tuple[Boid | None, float]:
    """Get the closest boid to a given point."""
    closest_boid = None
    min_distance = float('inf')

    for boid in boids:
        distance = (boid.x - point[0]) ** 2 + (boid.y - point[1]) ** 2
        if distance < min_distance:
            min_distance = distance
            closest_boid = boid

    return closest_boid, min_distance


if __name__ == '__main__':
    incoming_thread, outgoing_thread = setup_network()

    init_window(800, 450, "Client view")

    set_target_fps(60)

    boids: list[Boid] = []
    new_boids: list[Boid] = []

    last_state_pylod: bytes = b""

    peaked_boid: int | None = None

    while not window_should_close() and get_shutdown() is False:
        # Update
        # check if there is any incoming packet
        mouse_position = get_mouse_position()

        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            # Generate a new boid at the mouse position
            new_boid = generate_random_velocity_boid(mouse_position.x, mouse_position.y)
            new_boids.append(new_boid)
            outgoing_packets.put(Package(PackageKind.ADD_BOID, new_boid.serialize()))

        while not incoming_packets.empty():
            packet = incoming_packets.get()

            # Process the packet
            match packet.kind:
                case PackageKind.BOIDS_STATE:
                    # Update boids state
                    last_state_pylod = packet.payload
                case PackageKind.ERROR:
                    logger.error(f"Error packet received: {packet.payload.decode('utf-8')}")
                case _:
                    logger.warning(f"Unknown packet kind received: {packet.kind.name}")

            incoming_packets.task_done()

        boids = deserialize_boids(last_state_pylod)

        mouse_position = get_mouse_position()
        closes_boid, squared_distance = get_closest_boid_to_point(boids, (mouse_position.x, mouse_position.y))

        # Draw
        begin_drawing()
        clear_background(RAYWHITE)

        for boid in boids:
            points = get_triangle_points(boid.x, boid.y, boid.vx, boid.vy, 10)
            point1 = Vector2(points[0][0], points[0][1])
            point2 = Vector2(points[1][0], points[1][1])
            point3 = Vector2(points[2][0], points[2][1])

            if closes_boid is not None and closes_boid.id == boid.id:
                draw_triangle(point1, point3, point2, RED)
            else:
                draw_triangle(point1, point3, point2, BLUE)

        draw_fps(10, 10)

        end_drawing()

    close_window()

    shutdown_network(incoming_thread, outgoing_thread)
