import queue
import logging
from raylibpy import *
from boid_helper import generate_boids, get_triangle_points, serialize_boids
from server_network import ClientCommunicationInfo, setup_server_variables, server_establish_connection, set_shutdown
from network import Package, PackageKind
from boid import Boid
from logger_utils import create_formatted_logger

MAX_BOIDS = 200  # maximum number of boids

logger = create_formatted_logger()

all_incoming_packets = queue.Queue()  # a queue for all incoming packets

shutdown = False  # a flag to indicate if the server should shut down

all_client_infos: list[ClientCommunicationInfo] = []  # a list to store all client information

if __name__ == '__main__':
    setup_server_variables(all_incoming_packets, all_client_infos)
    server_establish_socket = server_establish_connection()

    init_window(800, 450, "Server view")

    set_target_fps(60)

    boids = generate_boids(100)

    while not window_should_close():
        # Update
        # send all the clients their packets
        while not all_incoming_packets.empty():
            packet = all_incoming_packets.get()
            if packet.kind != PackageKind.EXIT:
                match packet.kind:
                    case PackageKind.ADD_BOID:
                        boid = Boid.deserialize(packet.payload)

                        # check boids id is not already in the list and list is not full
                        if boid.id not in [b.id for b in boids] and len(boids) < MAX_BOIDS:
                            logger.info(f"Adding boid with ID: {boid.id} at position: ({boid.x}, {boid.y})")
                            boids.append(boid)
                    case PackageKind.REMOVE_BOID:
                        for i in range(len(boids)):
                            if boids[i].id == int.from_bytes(packet.payload, 'big'):
                                boids.pop(i)
                                logger.info(f"Removed boid with ID: {packet.payload.hex()}")
                                break
                    case _:
                        logger.error(f"Unknown package kind: {packet.kind.name}")
            else:
                logger.fatal(f"An exit package slipped through to server main!")

        mouse_pos = get_mouse_position()

        for client_info in all_client_infos:
            if not client_info.should_terminate:
                client_info.outgoing_queue.put(Package(PackageKind.BOIDS_STATE, serialize_boids(boids)))

        target_to = None
        target_away = None

        if is_mouse_button_down(MOUSE_BUTTON_LEFT):
            target_to = (mouse_pos.x, mouse_pos.y)
        elif is_mouse_button_down(MOUSE_BUTTON_RIGHT):
            target_away = (mouse_pos.x, mouse_pos.y)

        for boid in boids:
            boid.update(get_frame_time(), boids, 0, 0, 800, 450, target_to, target_away)

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

    set_shutdown(True)  # Set the shutdown flag to True

    server_establish_socket.close()
