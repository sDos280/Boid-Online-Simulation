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