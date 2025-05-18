import struct


class Boid:
    def __init__(self, x: float, y: float, vx: float, vy: float):
        self.x: float = x  # x position
        self.y: float = y  # y position
        self.vx: float = vx  # x velocity
        self.vy: float = vy  # y velocity

    def update(self):
        """Update the boid's position based on its velocity."""
        self.x += self.vx
        self.y += self.vy

    def apply_force(self, fx, fy):
        """Apply a force to the boid's velocity."""
        self.vx += fx
        self.vy += fy

    def get_position(self):
        """Return the current position of the boid."""
        return self.x, self.y

    def serialize(self) -> bytes:
        """Serialize the boid's state for network transmission."""
        return struct.pack('!ffff', self.x, self.y, self.vx, self.vy)

    @classmethod
    def deserialize(cls, data: bytes):
        """Deserialize the boid's state from network transmission."""
        x, y, vx, vy = struct.unpack('!ffff', data)
        return cls(x, y, vx, vy)
