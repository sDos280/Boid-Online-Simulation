import struct
import random
import math


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


# https://github.com/meznak/boids_py/blob/master/boid.py
class Boid:
    MIN_SPEED = 60
    MAX_SPEED = 100
    MAX_FORCE = 100
    MAX_TURN = 5
    PERCEPTION_RADIUS = 100
    AVOID_RADIUS = 20

    SEPARATION = 1
    ALIGNMENT = 1 / 8
    COHESION = 1 / 100
    EDGE_AVOIDANCE = 1 / 2

    MOVE_TOWARDS_WEIGHT = 100

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

    def move_towards(self, target: tuple[float, float] | None) -> tuple[float, float]:
        """
        Move the boid towards a target point (target_x, target_y).
        """
        if target is None:
            return 0.0, 0.0

        direction_x = target[0] - self.x
        direction_y = target[1] - self.y
        distance = math.sqrt(direction_x ** 2 + direction_y ** 2)

        if distance == 0:
            return self.vx, self.vy

        # Normalize the direction vector
        direction_x /= distance
        direction_y /= distance

        # Scale the direction vector by the MOVE_TOWARDS_WEIGHT
        return direction_x * Boid.MOVE_TOWARDS_WEIGHT, direction_y * Boid.MOVE_TOWARDS_WEIGHT

    def move_away_from(self, target: tuple[float, float] | None) -> tuple[float, float]:
        """
        Move the boid away from a target point (target_x, target_y).
        """
        if target is None:
            return 0.0, 0.0

        direction_x = self.x - target[0]
        direction_y = self.y - target[1]
        distance = math.sqrt(direction_x ** 2 + direction_y ** 2)

        if distance == 0:
            return self.vx, self.vy

        # Normalize the direction vector
        direction_x /= distance
        direction_y /= distance

        # Scale the direction vector by the MOVE_TOWARDS_WEIGHT
        return direction_x * Boid.MOVE_TOWARDS_WEIGHT, direction_y * Boid.MOVE_TOWARDS_WEIGHT

    def update(self, dt: float, boids: list['Boid'], min_x: float, min_y: float, max_x: float, max_y: float, target_to: tuple[float, float] | None, target_away: tuple[float, float] | None):
        boids_in_perception_range = [boid for boid in boids if boid is not self and self.get_distance_squared(boid) < Boid.PERCEPTION_RADIUS * Boid.PERCEPTION_RADIUS]
        boids_in_avoidance_range = [boid for boid in boids_in_perception_range if boid is not self and self.get_distance_squared(boid) < Boid.AVOID_RADIUS * Boid.AVOID_RADIUS]

        # calculate edge avoidance
        edge_avoidance_x, edge_avoidance_y = self.edge_avoidance(min_x, min_y, max_x, max_y)

        # calculate flow forces
        afx, afy = self.alignment(boids_in_perception_range)
        cfx, cfy = self.cohesion(boids_in_perception_range)
        sfx, sfy = self.separation(boids_in_avoidance_range)

        # calculate move towards target
        mtfx, mtfy = self.move_towards(target_to)

        # calculate move away from target
        mafx, mafy = self.move_away_from(target_away)

        fx = edge_avoidance_x + mtfx + mafx + afx + cfx + sfx
        fy = edge_avoidance_y + mtfy + mafy + afy + cfy + sfy

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
