from boid import Boid
import random
import math
import boid


def generate_random_velocity_boid(start_x: float, start_y: float) -> Boid:
    """Generate a random velocity boid with a given starting position."""
    vx = -Boid.MAX_SPEED if random.random() < 0.5 else Boid.MAX_SPEED
    vy = -Boid.MAX_SPEED if random.random() < 0.5 else Boid.MAX_SPEED
    return Boid(start_x, start_y, vx, vy)


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

    # aplay offset
    middle = ((tip[0] + left[0] + right[0]) / 3, (tip[1] + left[1] + right[1]) / 3)

    offset = (x - middle[0], y - middle[1])

    return [(tip[0]+offset[0], tip[1]+offset[1]), (left[0]+offset[0], left[1]+offset[1]), (right[0]+offset[0], right[1]+offset[1])]


def serialize_boids(boids: list[boid.Boid]) -> bytes:
    """Serialize the list of boids for network transmission."""
    serialized_data = b''

    serialized_data += len(boids).to_bytes(2, 'big')  # Number of boids
    for boid in boids:
        serialized_data += boid.serialize()

    return serialized_data


def deserialize_boids(data: bytes) -> list[boid.Boid]:
    """Deserialize the list of boids from network transmission."""
    num_boids = int.from_bytes(data[:2], 'big')
    boids = []

    for i in range(num_boids):
        start_index = 2 + i * boid.Boid.get_bytes_size()
        end_index = start_index + boid.Boid.get_bytes_size()
        boid_data = data[start_index:end_index]
        boids.append(boid.Boid.deserialize(boid_data))

    return boids
