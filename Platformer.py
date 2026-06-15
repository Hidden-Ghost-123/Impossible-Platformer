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

    def update(self, blocks):

        self.apply_gravity()

        # horizontal movement
        self.rect.x += self.x_vel

        # check horizontal collisions
        for block in blocks:
            if self.rect.colliderect(block):
                if self.x_vel > 0:
                    self.rect.right = block.left
                elif self.x_vel < 0:
                    self.rect.left = block.right

        # vertical movement
        self.rect.y += self.y_vel

        self.on_ground = False

        # check vertical collisions
        for block in blocks:
            if self.rect.colliderect(block):
                if self.y_vel > 0:
                    self.rect.bottom = block.top
                    self.y_vel = 0
                    self.on_ground = True

                elif self.y_vel < 0:
                    self.rect.top = block.bottom
                    self.y_vel = 0

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)


# player
player = Player(100, 100, 50, 50)

# platforms
blocks = [
    pygame.Rect(0, HEIGHT - 50, WIDTH, 50),   # floor
    pygame.Rect(200, 600, 200, 20),
    pygame.Rect(500, 450, 200, 20),
    pygame.Rect(800, 350, 150, 20)
]


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

    player.update(blocks)

    window.fill((64, 224, 208))

    # draw blocks
    for block in blocks:
        pygame.draw.rect(window, (0, 0, 0), block)

    player.draw(window)

    pygame.display.update()

pygame.quit()
