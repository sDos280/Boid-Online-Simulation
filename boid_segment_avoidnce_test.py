from raylibpy import *
from boid import Boid
import random
import math


def generate_boids(num_boids: int) -> list[Boid]:
    boids = []
    for _ in range(num_boids):
        x = random.uniform(0, 800)
        y = random.uniform(0, 450)
        vx = -Boid.MAX_SPEED if random.random() < 0.5 else Boid.MAX_SPEED
        vy = -Boid.MAX_SPEED if random.random() < 0.5 else Boid.MAX_SPEED
        boids.append(Boid(x, y, vx, vy))
    return boids


def get_triangle_points(x, y, vx, vy, size=1.0):
    """
    Given an origin (x, y) and a direction vector (vx, vy),
    return the coordinates of the 3 points of a triangle:
    - tip in the direction of the vector
    - two base corners to the left and right

    Returns: list of 3 (x, y) tuples
    """
    mag = math.hypot(vx, vy)
    if mag == 0:
        raise ValueError("Vector cannot be zero.")

    # Normalize vector
    dx = vx / mag
    dy = vy / mag

    # Perpendicular vector (rotated 90 degrees counterclockwise)
    perp_dx = -dy
    perp_dy = dx

    # Tip of the triangle (forward)
    tip = (x + dx * size, y + dy * size)

    # Base corners
    left = (x + perp_dx * (size / 2), y + perp_dy * (size / 2))
    right = (x - perp_dx * (size / 2), y - perp_dy * (size / 2))

    return [tip, left, right]


def main():
    init_window(800, 450, "raylib [core] example - basic window")

    set_target_fps(60)

    boids = [Boid(400, 100, 0, 40)]

    segments = [((10, 400), (790, 400))]

    while not window_should_close():
        # Update
        begin_drawing()
        clear_background(RAYWHITE)

        # Draw

        for boid in boids:
            boid.update(get_frame_time(), boids, 10, 10, 800 - 10, 450 - 10, segments)

        for segment in segments:
            p1 = Vector2(segment[0][0], segment[0][1])
            p2 = Vector2(segment[1][0], segment[1][1])
            draw_line_ex(p1, p2, 2, RED)

        for boid in boids:
            points = get_triangle_points(boid.x, boid.y, boid.vx, boid.vy, 10)
            point1 = Vector2(points[0][0], points[0][1])
            point2 = Vector2(points[1][0], points[1][1])
            point3 = Vector2(points[2][0], points[2][1])

            draw_triangle(point1, point3, point2, BLUE)

        draw_fps(10, 10)

        end_drawing()

    close_window()


if __name__ == '__main__':
    main()
