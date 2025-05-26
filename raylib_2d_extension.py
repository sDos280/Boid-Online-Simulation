import math
from raylibpy import *

RAY_LENGTH = 1000000


class Ray2D:
    def __init__(self, position: tuple[float, float] = (0.0, 0.0), direction: tuple[float, float] = (0.0, 0.0)):
        self.position: tuple[float, float] = position
        self.direction: tuple[float, float] = direction


class Ray2DCollision:
    def __init__(self, hit: bool = False, distance: float = 0.0, point: tuple[float, float] = (0.0, 0.0), normal: tuple[float, float] = (0.0, 0.0)):
        self.hit: bool = hit
        self.distance: float = distance
        self.point: tuple[float, float] = point
        self.normal: tuple[float, float] = normal


def draw_ray2d(ray: Ray2D, color: Color = RED):
    ray_end = vector2_add(ray.position, vector2_scale(ray.direction, RAY_LENGTH))
    draw_line_v(ray.position, ray_end, color)


def draw_ray2d_collision(collision: Ray2DCollision, color: Color = GREEN):
    if collision.hit:
        draw_circle_v(collision.point, 5, color)
        draw_line_v(collision.point, vector2_add(collision.point, collision.normal), color)
        draw_text(f"Distance: {collision.distance:.2f}", collision.point[0] + 10, collision.point[1] + 10, 10, color)


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def vector2_add(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])


def vector2_subtract(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1])


def vector2_scale(v, scalar):
    return (v[0] * scalar, v[1] * scalar)


def vector2_length(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2)


def vector2_normalize(v):
    length = vector2_length(v)
    if length == 0:
        return (0.0, 0.0)
    return (v[0] / length, v[1] / length)


def vector2_cross_product(v):
    """Return the 2D perpendicular (cross with implicit Z = 1 vector)."""
    return (v[1], -v[0])


def get_ray2d_collision_line_segment(ray: Ray2D, p1: tuple[float, float], p2: tuple[float, float]) -> Ray2DCollision:
    collision = Ray2DCollision()

    ray_end = vector2_add(ray.position, vector2_scale(ray.direction, RAY_LENGTH))

    denominator = (p2[1] - p1[1]) * (ray.position[0] - ray_end[0]) - (p2[0] - p1[0]) * (ray.position[1] - ray_end[1])

    if denominator != 0:
        uA = ((p2[0] - p1[0]) * (ray_end[1] - p1[1]) - (p2[1] - p1[1]) * (ray_end[0] - p1[0])) / denominator
        uB = ((ray.position[0] - ray_end[0]) * (ray_end[1] - p1[1]) - (ray.position[1] - ray_end[1]) * (ray_end[0] - p1[0])) / denominator

        if 0 <= uA <= 1 and 0 <= uB <= 1:
            collision.hit = True
            collision.point = (
                ray_end[0] + uA * (ray.position[0] - ray_end[0]),
                ray_end[1] + uA * (ray.position[1] - ray_end[1])
            )
            collision.distance = vector2_length(vector2_subtract(collision.point, ray.position))

            side = sign((ray.position[0] - p1[0]) * (p1[1] - p2[1]) + (ray.position[1] - p1[1]) * (p2[0] - p1[0]))

            line_dir = vector2_subtract(p2, p1)
            line_normal = vector2_cross_product(vector2_normalize(line_dir))

            if side == 1:
                collision.normal = (-line_normal[0], -line_normal[1])
            elif side == -1:
                collision.normal = line_normal
            # side == 0 => no normal; ray is on the line

    return collision
