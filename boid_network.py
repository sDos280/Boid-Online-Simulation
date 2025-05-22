import boid


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
