import asyncio
import math
import random
import pygame


pygame.init()

WIDTH = 960
HEIGHT = 640
FPS = 60

BLACK = (8, 12, 24)
WHITE = (240, 245, 255)
GRAY = (105, 115, 135)
DARK_GRAY = (28, 35, 52)
RED = (255, 80, 90)
YELLOW = (255, 210, 70)
CYAN = (80, 220, 255)
GREEN = (90, 235, 145)

ROTATION_SPEED = 3
THRUST = 0.15
DRAG = 0.99
MAX_SPEED = 7

DETECTION_RANGE = 300
FOV_THRESHOLD = 0.7
ENEMY_ROTATION_SPEED = 0.5

PLAYER_RADIUS = 17
BULLET_SPEED = 10
BULLET_LIFETIME = 75
SHOT_COOLDOWN = 220
ASTEROID_COUNT = 7
SCORE_PER_ASTEROID = 100


class Player:
    def __init__(self):
        self.position = pygame.Vector2(WIDTH * 0.72, HEIGHT / 2)
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        self.angle = 90
        self.is_thrusting = False
        self.last_shot_time = -SHOT_COOLDOWN

    def get_forward_vector(self):
        radians = math.radians(self.angle)

        return pygame.Vector2(
            math.cos(radians),
            -math.sin(radians)
        )

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += ROTATION_SPEED

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= ROTATION_SPEED

        self.angle %= 360
        forward = self.get_forward_vector()

        self.acceleration = pygame.Vector2(0, 0)
        self.is_thrusting = False

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.acceleration = forward * THRUST
            self.is_thrusting = True

        self.velocity += self.acceleration
        self.velocity *= DRAG

        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)

        self.position += self.velocity
        self.wrap_around_screen()

    def wrap_around_screen(self):
        if self.position.x > WIDTH:
            self.position.x = 0

        if self.position.x < 0:
            self.position.x = WIDTH

        if self.position.y > HEIGHT:
            self.position.y = 0

        if self.position.y < 0:
            self.position.y = HEIGHT

    def shoot(self, current_time):
        if current_time - self.last_shot_time < SHOT_COOLDOWN:
            return None

        self.last_shot_time = current_time
        forward = self.get_forward_vector()
        bullet_position = self.position + forward * 28
        bullet_velocity = forward * BULLET_SPEED + self.velocity * 0.5

        return Bullet(bullet_position, bullet_velocity)

    def draw(self, screen):
        forward = self.get_forward_vector()
        left = forward.rotate(140)
        right = forward.rotate(-140)

        front_point = self.position + forward * 24
        back_left = self.position + left * 18
        back_right = self.position + right * 18

        if self.is_thrusting:
            flame_position = self.position - forward * 20
            pygame.draw.circle(screen, YELLOW, flame_position, 6)

        pygame.draw.polygon(
            screen,
            WHITE,
            [front_point, back_left, back_right],
            3
        )

        # Challenge: show the direction the ship faces.
        pygame.draw.line(
            screen,
            RED,
            self.position,
            self.position + forward * 65,
            3
        )

        # Challenge: show the ship's actual velocity direction.
        if self.velocity.length() > 0.05:
            pygame.draw.line(
                screen,
                YELLOW,
                self.position,
                self.position + self.velocity * 10,
                3
            )


class Bullet:
    def __init__(self, position, velocity):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.lifetime = BULLET_LIFETIME

    def update(self):
        self.position += self.velocity
        self.lifetime -= 1

    def is_active(self):
        return (
            self.lifetime > 0
            and -10 <= self.position.x <= WIDTH + 10
            and -10 <= self.position.y <= HEIGHT + 10
        )

    def draw(self, screen):
        pygame.draw.circle(screen, CYAN, self.position, 4)


class Asteroid:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.radius = random.randint(20, 38)

        movement_angle = random.uniform(0, 360)
        movement_speed = random.uniform(1.0, 2.2)
        radians = math.radians(movement_angle)
        self.velocity = pygame.Vector2(
            math.cos(radians),
            -math.sin(radians)
        ) * movement_speed

        point_count = random.randint(8, 11)
        self.shape = []

        for index in range(point_count):
            point_angle = 360 * index / point_count
            point_radius = self.radius * random.uniform(0.75, 1.15)
            point_vector = pygame.Vector2(point_radius, 0).rotate(point_angle)
            self.shape.append(point_vector)

    def update(self):
        self.position += self.velocity

        if self.position.x > WIDTH + self.radius:
            self.position.x = -self.radius

        if self.position.x < -self.radius:
            self.position.x = WIDTH + self.radius

        if self.position.y > HEIGHT + self.radius:
            self.position.y = -self.radius

        if self.position.y < -self.radius:
            self.position.y = HEIGHT + self.radius

    def draw(self, screen):
        points = [self.position + point for point in self.shape]
        pygame.draw.polygon(screen, GRAY, points, 3)


class Enemy:
    def __init__(self):
        self.position = pygame.Vector2(WIDTH / 4, HEIGHT / 2)
        self.angle = 0
        self.detected = False
        self.state = "PATROL"
        self.distance_to_player = 0
        self.dot_product = 0

    def get_forward_vector(self):
        radians = math.radians(self.angle)

        return pygame.Vector2(
            math.cos(radians),
            -math.sin(radians)
        )

    def update(self, player):
        # Challenge: make the enemy slowly scan the area.
        self.angle += ENEMY_ROTATION_SPEED
        self.angle %= 360

        enemy_forward = self.get_forward_vector()
        to_player = player.position - self.position
        self.distance_to_player = self.position.distance_to(player.position)

        if to_player.length() > 0:
            to_player = to_player.normalize()
            self.dot_product = enemy_forward.dot(to_player)
        else:
            self.dot_product = 1

        self.detected = (
            self.distance_to_player < DETECTION_RANGE
            and self.dot_product > FOV_THRESHOLD
        )

        if self.detected:
            self.state = "ATTACK"
        else:
            self.state = "PATROL"

    def draw(self, screen):
        enemy_forward = self.get_forward_vector()
        left = enemy_forward.rotate(140)
        right = enemy_forward.rotate(-140)

        front_point = self.position + enemy_forward * 22
        back_left = self.position + left * 17
        back_right = self.position + right * 17

        enemy_color = RED if self.detected else WHITE

        pygame.draw.circle(
            screen,
            GRAY,
            self.position,
            DETECTION_RANGE,
            1
        )

        half_fov_angle = math.degrees(math.acos(FOV_THRESHOLD))
        fov_left = enemy_forward.rotate(half_fov_angle)
        fov_right = enemy_forward.rotate(-half_fov_angle)

        pygame.draw.line(
            screen,
            DARK_GRAY,
            self.position,
            self.position + fov_left * DETECTION_RANGE,
            2
        )
        pygame.draw.line(
            screen,
            DARK_GRAY,
            self.position,
            self.position + fov_right * DETECTION_RANGE,
            2
        )

        pygame.draw.line(
            screen,
            CYAN,
            self.position,
            self.position + enemy_forward * 100,
            3
        )

        pygame.draw.polygon(
            screen,
            enemy_color,
            [front_point, back_left, back_right],
            3
        )


def create_asteroid(player_position, enemy_position):
    while True:
        position = pygame.Vector2(
            random.randint(30, WIDTH - 30),
            random.randint(30, HEIGHT - 30)
        )

        far_from_player = position.distance_to(player_position) > 170
        far_from_enemy = position.distance_to(enemy_position) > 90

        if far_from_player and far_from_enemy:
            return Asteroid(position)


def start_new_game():
    player = Player()
    enemy = Enemy()
    bullets = []
    asteroids = []

    for _ in range(ASTEROID_COUNT):
        asteroids.append(
            create_asteroid(player.position, enemy.position)
        )

    return player, enemy, bullets, asteroids, 0


def handle_bullet_collisions(bullets, asteroids, player, enemy):
    bullets_hit = set()
    asteroids_hit = set()

    for bullet in bullets:
        for asteroid in asteroids:
            collision_distance = bullet.position.distance_to(
                asteroid.position
            )

            if collision_distance < asteroid.radius + 4:
                bullets_hit.add(bullet)
                asteroids_hit.add(asteroid)
                break

    bullets[:] = [
        bullet for bullet in bullets
        if bullet not in bullets_hit
    ]
    asteroids[:] = [
        asteroid for asteroid in asteroids
        if asteroid not in asteroids_hit
    ]

    for _ in asteroids_hit:
        asteroids.append(
            create_asteroid(player.position, enemy.position)
        )

    return len(asteroids_hit) * SCORE_PER_ASTEROID


def player_hit_asteroid(player, asteroids):
    for asteroid in asteroids:
        collision_distance = player.position.distance_to(
            asteroid.position
        )

        if collision_distance < PLAYER_RADIUS + asteroid.radius:
            return True

    return False


def draw_background(screen, stars):
    screen.fill(BLACK)

    for star_position, radius in stars:
        pygame.draw.circle(screen, GRAY, star_position, radius)


def draw_text(screen, font, text, position, color=WHITE):
    text_image = font.render(text, True, color)
    screen.blit(text_image, position)


def draw_information(screen, font, player, enemy, score):
    forward = player.get_forward_vector()
    status_color = RED if enemy.detected else GREEN
    status_message = "PLAYER DETECTED!" if enemy.detected else "Player hidden"

    pygame.draw.rect(screen, (14, 20, 35), (12, 12, 390, 207))
    pygame.draw.rect(screen, DARK_GRAY, (12, 12, 390, 207), 2)

    information = [
        f"Angle: {player.angle:.0f} degrees",
        f"Forward: ({forward.x:.2f}, {forward.y:.2f})",
        f"Velocity: ({player.velocity.x:.2f}, {player.velocity.y:.2f})",
        f"Speed: {player.velocity.length():.2f}",
        f"Distance: {enemy.distance_to_player:.1f}",
        f"Dot Product: {enemy.dot_product:.2f}",
        f"Enemy State: {enemy.state}",
    ]

    for index, line in enumerate(information):
        draw_text(screen, font, line, (25, 22 + index * 26))

    draw_text(screen, font, f"Score: {score}", (WIDTH - 145, 20), WHITE)
    draw_text(screen, font, status_message, (WIDTH - 205, 48), status_color)
    draw_text(
        screen,
        font,
        "LEFT/A and RIGHT/D: rotate     UP/W: thrust     SPACE: shoot",
        (WIDTH / 2 - 310, HEIGHT - 34),
        WHITE
    )

    draw_text(screen, font, "RED: forward", (WIDTH - 175, HEIGHT - 82), RED)
    draw_text(screen, font, "YELLOW: velocity", (WIDTH - 175, HEIGHT - 58), YELLOW)


def draw_game_over(screen, title_font, font, score):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 205))
    screen.blit(overlay, (0, 0))

    title = title_font.render("YOU DIED", True, RED)
    final_score = font.render(f"Final Score: {score}", True, WHITE)
    restart = font.render("Press R to restart", True, WHITE)

    screen.blit(
        title,
        title.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 70))
    )
    screen.blit(
        final_score,
        final_score.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 5))
    )
    screen.blit(
        restart,
        restart.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 50))
    )


async def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Vector Flight: Asteroid Survival")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    title_font = pygame.font.Font(None, 76)

    player, enemy, bullets, asteroids, score = start_new_game()
    game_over = False

    stars = [
        ((55, 85), 1), ((140, 250), 2), ((220, 55), 1), ((320, 170), 1),
        ((430, 75), 2), ((515, 285), 1), ((610, 105), 1), ((720, 210), 2),
        ((835, 90), 1), ((910, 275), 1), ((75, 460), 2), ((175, 575), 1),
        ((290, 405), 1), ((405, 535), 2), ((540, 445), 1), ((665, 565), 1),
        ((785, 420), 2), ((905, 545), 1)
    ]

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
                and game_over
            ):
                player, enemy, bullets, asteroids, score = start_new_game()
                game_over = False

        keys = pygame.key.get_pressed()

        if not game_over:
            player.update(keys)
            enemy.update(player)

            if keys[pygame.K_SPACE]:
                new_bullet = player.shoot(pygame.time.get_ticks())

                if new_bullet is not None:
                    bullets.append(new_bullet)

            for bullet in bullets:
                bullet.update()

            bullets[:] = [
                bullet for bullet in bullets
                if bullet.is_active()
            ]

            for asteroid in asteroids:
                asteroid.update()

            score += handle_bullet_collisions(
                bullets,
                asteroids,
                player,
                enemy
            )

            if player_hit_asteroid(player, asteroids):
                game_over = True

        draw_background(screen, stars)
        enemy.draw(screen)

        for asteroid in asteroids:
            asteroid.draw(screen)

        for bullet in bullets:
            bullet.draw(screen)

        player.draw(screen)
        draw_information(screen, font, player, enemy, score)

        if game_over:
            draw_game_over(screen, title_font, font, score)

        pygame.display.flip()
        clock.tick(FPS)

        # Required by Pygbag so the browser can update the page.
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
