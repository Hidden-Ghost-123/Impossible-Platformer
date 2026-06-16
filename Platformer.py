import pygame
from os.path import join
from os import listdir
from os.path import isfile

pygame.init()

WIDTH = 1000
HEIGHT = 700
FPS = 60

PLAYER_VEL = 5
GRAVITY = 1

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Impossible Game")

clock = pygame.time.Clock()


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):

    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:

        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []

        for i in range(sprite_sheet.get_width() // width):

            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)

            rect = pygame.Rect(i * width, 0, width, height)

            surface.blit(sprite_sheet, (0, 0), rect)

            sprites.append(pygame.transform.scale2x(surface))

        if direction:

            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)

        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


class Player:

    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):

        self.rect = pygame.Rect(x, y, width, height)

        self.x_vel = 0
        self.y_vel = 0

        self.direction = "left"

        self.animation_count = 0

        self.fall_count = 0

        self.SPRITES = load_sprite_sheets(
            "MainCharacters", "VirtualGuy", 32, 32, True
        )

        self.sprite = self.SPRITES["idle_left"][0]

        self.mask = None

        self.on_ground = False

    def jump(self):
        self.y_vel = -15
        self.on_ground = False

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):

        self.x_vel = -vel

        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):

        self.x_vel = vel

        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def update_sprite(self):

        sprite_sheet = "idle"

        if self.y_vel < 0:
            sprite_sheet = "jump"

        elif self.y_vel > GRAVITY * 2:
            sprite_sheet = "fall"

        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction

        sprites = self.SPRITES[sprite_sheet_name]

        sprite_index = (
            self.animation_count // self.ANIMATION_DELAY
        ) % len(sprites)

        self.sprite = sprites[sprite_index]

        self.animation_count += 1

    def update(self, blocks):

        self.y_vel += GRAVITY

        self.rect.x += self.x_vel

        for block in blocks:

            if self.rect.colliderect(block):

                if self.x_vel > 0:
                    self.rect.right = block.left

                elif self.x_vel < 0:
                    self.rect.left = block.right

        self.rect.y += self.y_vel

        self.on_ground = False

        for block in blocks:

            if self.rect.colliderect(block):

                if self.y_vel > 0:
                    self.rect.bottom = block.top
                    self.y_vel = 0
                    self.on_ground = True

                elif self.y_vel < 0:
                    self.rect.top = block.bottom
                    self.y_vel = 0

        self.update_sprite()

    def draw(self, win):
        win.blit(self.sprite, self.rect)


player = Player(100, 100, 50, 50)

blocks = [
    pygame.Rect(0, HEIGHT - 50, WIDTH, 50),
    pygame.Rect(200, 600, 200, 20),
    pygame.Rect(500, 450, 200, 20)
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
        player.move_left(PLAYER_VEL)

    if keys[pygame.K_RIGHT]:
        player.move_right(PLAYER_VEL)

    player.update(blocks)

    window.fill((64, 224, 208))

    for block in blocks:
        pygame.draw.rect(window, (0, 0, 0), block)

    player.draw(window)

    pygame.display.update()

pygame.quit()
