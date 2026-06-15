# Impossible Platformer Game
# Nishchay Bhudia

import pygame

# initialise pygame
pygame.init()

# display settings
WIDTH = 1000
HEIGHT = 800
FPS = 60

PLAYER_VEL = 5

# create window
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Impossible Game")

clock = pygame.time.Clock()


# player Class
class Player:

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = (255, 0, 0)

    def move_left(self, vel):
        self.rect.x -= vel

    def move_right(self, vel):
        self.rect.x += vel

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)


# create the player
player = Player(100, 100, 50, 50)

# main loop
run = True

while run:

    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        player.move_left(PLAYER_VEL)

    if keys[pygame.K_RIGHT]:
        player.move_right(PLAYER_VEL)

    # draw background
    window.fill((64, 224, 208))

    # draw player
    player.draw(window)

    pygame.display.update()

pygame.quit()
