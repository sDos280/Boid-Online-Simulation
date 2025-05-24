from raylibpy import *
import math

RAY_LENGTH = 1000000


class Ray2D:
    def __init__(self):
        self.position: Vector2 = Vector2(0, 0)
        self.direction: Vector2 = Vector2(0, 0)


class Ray2DCollision:
    def __init__(self):
        self.hit: bool = False
        self.distance: float = 0.0
        self.point: Vector2 = Vector2(0, 0)
        self.normal: Vector2 = Vector2(0, 0)


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def _vector2_cross_product(v: Vector2) -> Vector2:
    """Return the perpendicular vector (2D cross product with z=1)"""
    return Vector2(v.y, -v.x)


def _vector2_normalize(v: Vector2) -> Vector2:
    """Normalize a Vector2"""
    length = math.sqrt(v.x ** 2 + v.y ** 2)
    if length == 0:
        return Vector2(0, 0)

    return Vector2(v.x / length, v.y / length)


def get_ray2d_collision_line_segment(ray: Ray2D, p1: Vector2, p2: Vector2) -> Ray2DCollision:
    collision = Ray2DCollision()

    ray_end = Vector2(ray.position.x + ray.direction.x * RAY_LENGTH,
                      ray.position.y + ray.direction.y * RAY_LENGTH)

    denominator = (p2.y - p1.y) * (ray.position.x - ray_end.x) - (p2.x - p1.x) * (ray.position.y - ray_end.y)

    if denominator != 0:
        uA = ((p2.x - p1.x) * (ray_end.y - p1.y) - (p2.y - p1.y) * (ray_end.x - p1.x)) / denominator
        uB = ((ray.position.x - ray_end.x) * (ray_end.y - p1.y) - (ray.position.y - ray_end.y) * (ray_end.x - p1.x)) / denominator

        if 0 <= uA <= 1 and 0 <= uB <= 1:
            collision.hit = True
            collision.point = Vector2(
                ray_end.x + uA * (ray.position.x - ray_end.x),
                ray_end.y + uA * (ray.position.y - ray_end.y)
            )
            collision.distance = math.sqrt((collision.point.x - ray.position.x) ** 2 + (collision.point.y - ray.position.y) ** 2)

            side = sign((ray.position.x - p1.x) * (p1.y - p2.y) + (ray.position.y - p1.y) * (p2.x - p1.x))

            line_dir = Vector2(p2.x - p1.x, p2.y - p1.y)
            line_normal = _vector2_cross_product(_vector2_normalize(line_dir))

            if side == 1:
                collision.normal = Vector2(-line_normal.x, -line_normal.y)
            elif side == -1:
                collision.normal = line_normal
            # If side == 0, ray is colinear with line, no normal

    return collision
