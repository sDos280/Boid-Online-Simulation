from raylibpy import *
from boid import Boid
import random


def generate_boids(num_boids: int) -> list[Boid]:
    boids = []
    for _ in range(num_boids):
        x = random.uniform(0, 800)
        y = random.uniform(0, 450)
        vx = -Boid.MAX_SPEED if random.random() < 0.5 else Boid.MAX_SPEED
        vy = -Boid.MAX_SPEED if random.random() < 0.5 else Boid.MAX_SPEED
        boids.append(Boid(x, y, vx, vy))
    return boids


def main():
    init_window(800, 450, "raylib [core] example - basic window")

    set_target_fps(60)

    boids = generate_boids(100)

    while not window_should_close():
        # Update
        print(get_frame_time())
        for boid in boids:
            boid.update(get_frame_time(), boids, 10, 10, 800 - 10, 450 - 10)

        begin_drawing()
        clear_background(RAYWHITE)

        # Draw
        for boid in boids:
            draw_circle(int(boid.x), int(boid.y), 5, BLUE)

        draw_fps(10, 10)

        end_drawing()

    close_window()


if __name__ == '__main__':
    main()
