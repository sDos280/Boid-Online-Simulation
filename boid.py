import struct
import random
import raylib_2d_extension
import math


def vector_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def vector_dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def vector_length(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2)


def point_segment_distance(p, a, b):
    """
    Calculate the shortest distance from point p to the line segment ab.

    Parameters:
        p (tuple): The point (x, y).
        a (tuple): First endpoint of the segment (x, y).
        b (tuple): Second endpoint of the segment (x, y).

    Returns:
        float: The shortest distance from point p to segment ab.
    """
    ab = vector_sub(b, a)
    ap = vector_sub(p, a)
    ab_length_squared = vector_dot(ab, ab)

    if ab_length_squared == 0:
        # a and b are the same point
        return vector_length(vector_sub(p, a))

    # Project point p onto the line defined by a and b, but clamp it to the segment
    t = max(0, min(1, vector_dot(ap, ab) / ab_length_squared))
    projection = (a[0] + t * ab[0], a[1] + t * ab[1])

    return vector_length(vector_sub(p, projection))


def map_range(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def to_polar(x: float, y: float) -> tuple[float, float]:
    """
    Convert Cartesian coordinates (x, y) to polar coordinates (r, theta).
    Returns:
        r: float - the magnitude (radius)
        theta: float - the angle in radians
    """
    r = math.hypot(x, y)  # Same as sqrt(x*x + y*y)
    theta = math.atan2(y, x)  # Returns angle in radians from -pi to pi
    return r, theta


def from_polar(r: float, theta: float) -> tuple[float, float]:
    """
    Convert polar coordinates (r, theta) to Cartesian coordinates (x, y).
    Args:
        r: float - the magnitude (radius)
        theta: float - the angle in radians
    Returns:
        x: float - x coordinate
        y: float - y coordinate
    """
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return x, y


def alternating_sequence(n: int) -> int:
    if n == 0:
        return 0
    return -((n + 1) // 2) if n % 2 == 1 else (n // 2)


VIEW_ANGLE = 270 * (math.pi / 180)  # the max offset between two angles in the raycasting
RAY_OFFSET = 15 * (math.pi / 180)  # the offset between two rays in the raycasting
MAX_RAYS = 20
_OFFSET_ANGLES = []

for i in range(MAX_RAYS):
    if math.fabs(alternating_sequence(i) * RAY_OFFSET) > VIEW_ANGLE / 2:
        break
    _OFFSET_ANGLES.append(alternating_sequence(i) * RAY_OFFSET)


# https://github.com/meznak/boids_py/blob/master/boid.py
class Boid:
    # al the distances of radiuses are squared
    MIN_SPEED = 60
    MAX_SPEED = 100
    MAX_FORCE = 100
    MAX_TURN = 5
    PERCEPTION_RADIUS = 100
    AVOID_RADIUS = 20
    CROWDING = 15

    OFFSET_ANGLES = _OFFSET_ANGLES

    SEPARATION = 1
    ALIGNMENT = 1 / 8
    COHESION = 1 / 100
    EDGE_AVOIDANCE = 1 / 2

    def __init__(self, x: float, y: float, vx: float, vy: float, id: int = None):
        self.x: float = x  # x position
        self.y: float = y  # y position
        self.vx: float = vx  # x velocity
        self.vy: float = vy  # y velocity
        self.id: int = random.randint(0, 0xFFFFFFFF) if id is None else id  # boid id

    def serialize(self) -> bytes:
        """Serialize the boid's state for network transmission."""
        return struct.pack('!ffffI', self.x, self.y, self.vx, self.vy, self.id)

    @classmethod
    def deserialize(cls, data: bytes):
        """Deserialize the boid's state from network transmission."""
        x, y, vx, vy, id = struct.unpack('!ffffI', data)
        return cls(x, y, vx, vy, id)

    @staticmethod
    def get_bytes_size() -> int:
        """Get the size of the serialized boid data."""
        return struct.calcsize('!ffffI')

    def get_distance_squared(self, boid: 'Boid') -> float:
        """Calculate the squared distance to another boid."""
        return (self.x - boid.x) ** 2 + (self.y - boid.y) ** 2

    def get_distance(self, boid: 'Boid') -> float:
        """Calculate the distance to another boid."""
        return math.sqrt(self.get_distance_squared(boid))

    def separation(self, boids: list['Boid']) -> tuple[float, float]:
        """Calculate the separation force from other boids. all boids should be inside the avoid radius."""
        if len(boids) == 0:
            return 0.0, 0.0

        steering_x = 0.0
        steering_y = 0.0

        for boid in boids:
            steering_x -= boid.x - self.x
            steering_y -= boid.y - self.y

        steering_x *= Boid.SEPARATION
        steering_y *= Boid.SEPARATION

        return steering_x, steering_y

    def alignment(self, boids: list['Boid']) -> tuple[float, float]:
        """Calculate the alignment force with other boids. all boids should be inside the perception radius."""

        if len(boids) == 0:
            return 0.0, 0.0

        steering_x = 0.0
        steering_y = 0.0

        for boid in boids:
            steering_x += boid.vx
            steering_y += boid.vy

        steering_x /= len(boids)
        steering_y /= len(boids)

        steering_x -= self.vx
        steering_y -= self.vy

        steering_x *= Boid.ALIGNMENT
        steering_y *= Boid.ALIGNMENT

        return steering_x, steering_y

    def cohesion(self, boids: list['Boid']) -> tuple[float, float]:
        """Calculate the cohesion force with other boids. all boids should be inside the perception radius."""

        if len(boids) == 0:
            return 0.0, 0.0

        steering_x = 0.0
        steering_y = 0.0

        for boid in boids:
            steering_x += boid.x
            steering_y += boid.y

        steering_x /= len(boids)
        steering_y /= len(boids)

        steering_x -= self.x
        steering_y -= self.y

        steering_x *= Boid.COHESION
        steering_y *= Boid.COHESION

        return steering_x, steering_y

    def edge_avoidance(self, min_x: float, min_y: float, max_x: float, max_y: float) -> tuple[float, float]:
        left = self.x - min_x
        up = self.y - min_y
        right = max_x - self.x
        down = max_y - self.y

        scale = min(left, up, right, down)

        if scale < 0.0:
            steering_x = (max_x - min_x) / 2 - self.x
            steering_y = (max_y - min_y) / 2 - self.y
        else:
            steering_x = 0.0
            steering_y = 0.0

        return steering_x * Boid.EDGE_AVOIDANCE, steering_y * Boid.EDGE_AVOIDANCE

    def avoid_segments(self, segments: list[tuple[tuple[float, float], tuple[float, float]]]) -> tuple[float, float]:
        r, theta = to_polar(self.vx, self.vy)

        def get_furthest_collision_for_a_ray(ray: raylib_2d_extension.Ray2D) -> raylib_2d_extension.Ray2DCollision | None:
            """Return the furthest collision of the ray with the segments (no if there isn't any collision)."""
            best_collision: raylib_2d_extension.Ray2DCollision | None = None
            furthest_distance = float('-inf')

            for segment in segments:
                collision = raylib_2d_extension.get_ray2d_collision_line_segment(ray, segment[0], segment[1])

                if collision.hit:
                    if collision.distance > furthest_distance:
                        furthest_distance = collision.distance
                        best_collision = collision

            return best_collision

        def get_best_direction() -> tuple[float, float]:
            over_all_ray_best_dir: tuple[float, float] | None = None
            over_all_ray_furthest_distance: float = float('-inf')
            over_all_ray_best_angle: float = 0.0

            for offset_angle in Boid.OFFSET_ANGLES:
                ray = raylib_2d_extension.Ray2D()
                ray.position = (self.x, self.y)
                ray.direction = from_polar(1, theta + offset_angle)

                ray_furthest_collision = get_furthest_collision_for_a_ray(ray)

                if ray_furthest_collision is None:  # we found a path without collisions
                    return from_polar(Boid.EDGE_AVOIDANCE, theta + offset_angle)

                if ray_furthest_collision.distance > over_all_ray_furthest_distance:  # we found a better path, although we know there is something a head
                    over_all_ray_furthest_distance = ray_furthest_collision.distance
                    over_all_ray_best_dir = ray.direction
                    over_all_ray_best_angle = offset_angle

            if over_all_ray_best_dir is not None:
                return from_polar(Boid.EDGE_AVOIDANCE, over_all_ray_best_angle)

        ray = raylib_2d_extension.Ray2D()
        ray.position = (self.x, self.y)
        ray.direction = get_best_direction()

        raylib_2d_extension.draw_ray2d(ray, raylib_2d_extension.GREEN)

        return get_best_direction()

    def update(self, dt: float, boids: list['Boid'], min_x: float, min_y: float, max_x: float, max_y: float, segments: list[tuple[tuple[float, float], tuple[float, float]]]):
        boids_in_perception_range = [boid for boid in boids if boid is not self and self.get_distance_squared(boid) < Boid.PERCEPTION_RADIUS * Boid.PERCEPTION_RADIUS]
        boids_in_avoidance_range = [boid for boid in boids_in_perception_range if boid is not self and self.get_distance_squared(boid) < Boid.AVOID_RADIUS * Boid.AVOID_RADIUS]

        # add edge avoidance
        edge_avoidance_x, edge_avoidance_y = self.edge_avoidance(min_x, min_y, max_x, max_y)

        # add segments avoidance
        # segments_avoidance_x, segments_avoidance_y = self.avoid_segments(segments)

        afx, afy = self.alignment(boids_in_perception_range)
        cfx, cfy = self.cohesion(boids_in_perception_range)
        sfx, sfy = self.separation(boids_in_avoidance_range)

        # fx = segments_avoidance_x + edge_avoidance_x + afx + cfx + sfx
        # fy = segments_avoidance_y + segments_avoidance_y + afy + cfy + sfy

        fx = edge_avoidance_x + afx + cfx + sfx
        fy = edge_avoidance_y + afy + cfy + sfy

        # enforce turn limit
        _, old_heading = to_polar(self.vx, self.vy)
        new_velocity_x = self.vx + fx * dt
        new_velocity_y = self.vy + fy * dt
        speed, new_heading = to_polar(new_velocity_x, new_velocity_y)

        heading_diff = 180 - (180 - new_heading + old_heading) % 360

        if heading_diff > Boid.MAX_TURN:
            if heading_diff > Boid.MAX_TURN:
                new_heading = old_heading + Boid.MAX_TURN
            else:
                new_heading = old_heading - Boid.MAX_TURN

        self.vx, self.vy = from_polar(speed, new_heading)

        # enforce speed limit
        speed, _ = to_polar(self.vx, self.vy)
        if speed > Boid.MAX_SPEED:
            scale = Boid.MAX_SPEED / speed
            self.vx *= scale
            self.vy *= scale
        elif speed < Boid.MIN_SPEED:
            scale = Boid.MIN_SPEED / speed
            self.vx *= scale
            self.vy *= scale

        # update position
        self.x += self.vx * dt
        self.y += self.vy * dt
