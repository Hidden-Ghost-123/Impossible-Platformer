# Impossible Platformer Game
# Nishchay Bhudia

import pygame

pygame.init()

WIDTH = 1000
HEIGHT = 800
FPS = 60

PLAYER_VEL = 5
GRAVITY = 1

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Impossible Game")

clock = pygame.time.Clock()


class Player:

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

        self.color = (255, 0, 0)

        self.x_vel = 0
        self.y_vel = 0

        self.on_ground = False

    def jump(self):
        self.y_vel = -15
        self.on_ground = False

    def move(self):
        self.rect.x += self.x_vel
        self.rect.y += self.y_vel

    def apply_gravity(self):
        self.y_vel += GRAVITY

    def update(self):
        self.apply_gravity()
        self.move()

        # floor collision (temporary)
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.y_vel = 0
            self.on_ground = True

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)


player = Player(100, 100, 50, 50)

run = True

while run:

    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and player.on_ground:
                player.jump()

    keys = pygame.key.get_pressed()

    player.x_vel = 0

    if keys[pygame.K_LEFT]:
        player.x_vel = -PLAYER_VEL

    if keys[pygame.K_RIGHT]:
        player.x_vel = PLAYER_VEL

    player.update()

    window.fill((64, 224, 208))

    player.draw(window)

    pygame.display.update()

pygame.quit()
