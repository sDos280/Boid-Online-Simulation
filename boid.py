import struct
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
    MIN_SPEED = .01
    MAX_SPEED = 40
    MAX_FORCE = 100
    MAX_TURN = 5
    PERCEPTION_RADIUS = 30
    AVOID_RADIUS = 10
    CROWDING = 15
    CAN_WRAP = False
    EDGE_DISTANCE_PCT = 5
    SEPARATION = 1
    ALIGNMENT = 1 / 8
    COHESION = 1 / 100

    def __init__(self, x: float, y: float, vx: float, vy: float):
        self.x: float = x  # x position
        self.y: float = y  # y position
        self.vx: float = vx  # x velocity
        self.vy: float = vy  # y velocity

    def serialize(self) -> bytes:
        """Serialize the boid's state for network transmission."""
        return struct.pack('!ffff', self.x, self.y, self.vx, self.vy)

    @classmethod
    def deserialize(cls, data: bytes):
        """Deserialize the boid's state from network transmission."""
        x, y, vx, vy = struct.unpack('!ffff', data)
        return cls(x, y, vx, vy)

    def get_distance(self, boid: 'Boid') -> float:
        """Calculate the distance to another boid."""
        return ((self.x - boid.x) ** 2 + (self.y - boid.y) ** 2) ** 0.5

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

    def edge_avoidance(self, width: float, height: float) -> tuple[float, float]:
        left = self.x
        up = self.y
        right = width - self.x
        down = height - self.y

        scale = max(left, up, right, down)

        if scale > 0:
            steering_x = width / 2 - self.x
            steering_y = height / 2 - self.y
        else:
            steering_x = 0
            steering_y = 0

        return steering_x, steering_y

    def update(self, dt: float, boids: list['Boid'], width: float = 800, height: float = 450):
        for boid in boids:
            if boid is self:
                continue

            dist = self.get_distance(boid)

            fx, fy = 0.0, 0.0

            # add edge avoidance
            edge_avoidance_x, edge_avoidance_y = self.edge_avoidance(width, height)

            fx += edge_avoidance_x
            fy += edge_avoidance_y

            # add boid forces
            if dist < self.PERCEPTION_RADIUS:
                afx, afy = self.alignment(boids)
                cfx, cfy = self.cohesion(boids)

                fx = afx + cfx
                fy = afy + cfy

                if dist < self.AVOID_RADIUS:
                    sfx, sfy = self.separation(boids)

                    fx += sfx
                    fy += sfy

            # enforce turn limit
            _, old_heading = to_polar(self.vx, self.vy)
            new_velocity_x = self.vx + fx * dt
            new_velocity_y = self.vy + fy * dt
            speed, new_heading = to_polar(new_velocity_x, new_velocity_y)

            heading_diff = 180 - (180 - new_heading + old_heading) % 360

            if heading_diff > self.MAX_TURN:
                if heading_diff > self.MAX_TURN:
                    new_heading = old_heading + self.MAX_TURN
                else:
                    new_heading = old_heading - self.MAX_TURN

            self.vx, self.vy = from_polar(speed, new_heading)

            # enforce speed limit
            speed, _ = to_polar(self.vx, self.vy)
            if speed > self.MAX_SPEED:
                scale = self.MAX_SPEED / speed
                self.vx *= scale
                self.vy *= scale

        # update position
        self.x += self.vx * dt
        self.y += self.vy * dt
