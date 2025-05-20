import struct


# https://github.com/meznak/boids_py/blob/master/boid.py

class Boid:
    MIN_SPEED = .01
    MAX_SPEED = .2
    MAX_FORCE = 1
    MAX_TURN = 5
    PERCEPTION = 60
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
        steering_x = 0.0
        steering_y = 0.0

        for boid in boids:
            dist = self.get_distance(boid)

            if dist < self.CROWDING:
                steering_x -= boid.x - self.x
                steering_y -= boid.y - self.y

        steering_x, steering_y = self.clamp_force(steering_x, steering_y)

        steering_x *= Boid.SEPARATION
        steering_y *= Boid.SEPARATION

        return steering_x, steering_y

    def alignment(self, boids: list['Boid']) -> tuple[float, float]:
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

        steering_x, steering_y = self.clamp_force(steering_x, steering_y)

        steering_x *= Boid.ALIGNMENT
        steering_y *= Boid.ALIGNMENT

        return steering_x, steering_y

    def cohesion(self, boids: list['Boid']) -> tuple[float, float]:
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

        steering_x, steering_y = self.clamp_force(steering_x, steering_y)

        steering_x *= Boid.COHESION
        steering_y *= Boid.COHESION

        return steering_x, steering_y

    def apply_force(self, fx: float, fy: float):
        """Apply a force to the boid's velocity."""
        self.vx += fx
        self.vy += fy

        self.vx = max(min(self.vx, self.MAX_SPEED), -self.MAX_SPEED)
        self.vy = max(min(self.vy, self.MAX_SPEED), -self.MAX_SPEED)

    @staticmethod
    def clamp_force(force_x: float, force_y: float) -> tuple[float, float]:
        """Clamp the force to a maximum value."""
        double_magnitude = (force_x ** 2 + force_y ** 2)

        if double_magnitude > Boid.MAX_FORCE ** 2:
            scale = (Boid.MAX_FORCE / (double_magnitude ** 0.5))
            force_x *= scale
            force_y *= scale

        return force_x, force_y
