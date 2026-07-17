#Impossible Platformer Game - FINAL VERSION
#Nishchay Bhudia
#Original: 08/10/2024 - 21/01/2025
#Update: added character select (4 characters, all different abilities), 2 player mode,
#new traps (fan, rock head, spiked ball), 2 more levels, coins, camera now scrolls up/down too
#Computer Science

#Imports
import time
import csv
import os
import random
import math
import pygame
import sys
from os import listdir
from os.path import isfile, join

#Initialising Pygame
pygame.init()
pygame.mixer.init()

#sound effects
def load_sounds():
    sounds = {
        'background': pygame.mixer.Sound('assets/Sound Effects/background.mp3'),
        'die': pygame.mixer.Sound('assets/Sound Effects/die.mp3'),
        'checkpoint': pygame.mixer.Sound('assets/Sound Effects/checkpoint.mp3'),
        'start': pygame.mixer.Sound('assets/Sound Effects/start.mp3'),
        'coin': pygame.mixer.Sound('assets/Sound Effects/item pick up.mp3'),
    }
    sounds['background'].set_volume(0.2)
    return sounds

game_sounds = load_sounds()

def play_background_music():
    game_sounds['background'].play(-1)

def stop_background_music():
    game_sounds['background'].stop()

def play_sound(sound_name):
    if sound_name in game_sounds:
        game_sounds[sound_name].play()

#Display Settings
pygame.display.set_caption("Impossible Game")

#Basic Variables
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
death_count = 0
coins_collected = 0
current_level_num = 1
block_size = 96
small_block_size = 48

#Pygame Window Setup
window = pygame.display.set_mode((WIDTH, HEIGHT))

#particle system, just used for jump dust/dash trail/coin sparkle/hit effect
#making a new tiny surface for every particle every frame was one of the big
#slowdowns on the web build, so cache them by (size, color, alpha) instead -
#most particles share the same handful of colors/sizes so this reuses a lot
_particle_surface_cache = {}

def _get_particle_surface(size, color, alpha):
    key = (size, color, alpha)
    surf = _particle_surface_cache.get(key)
    if surf is None:
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, alpha), (size, size), size)
        _particle_surface_cache[key] = surf
    return surf

class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=30, size=4):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-3, -1)
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self, win, offset_x, offset_y):
        if self.life <= 0:
            return
        alpha_ratio = self.life / self.max_life
        size = max(1, int(self.size * alpha_ratio))
        alpha = int(255 * alpha_ratio)
        surf = _get_particle_surface(size, self.color, alpha)
        win.blit(surf, (self.x - offset_x - size, self.y - offset_y - size))

    def is_dead(self):
        return self.life <= 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=8, life=30, size=4):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, life=life, size=size))

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if not p.is_dead()]

    def draw(self, win, offset_x, offset_y):
        for p in self.particles:
            p.draw(win, offset_x, offset_y)


particles = ParticleSystem()

#screen shake, used when player gets hit
class ScreenShake:
    def __init__(self):
        self.trauma = 0

    def add(self, amount):
        self.trauma = min(1, self.trauma + amount)

    def update(self):
        self.trauma = max(0, self.trauma - 0.05)

    def offset(self):
        if self.trauma <= 0:
            return (0, 0)
        power = self.trauma ** 2
        return (random.uniform(-1, 1) * 16 * power, random.uniform(-1, 1) * 16 * power)


screen_shake = ScreenShake()

#Loading Screen
def draw_loading_screen(window):
    window.fill((64, 224, 208))
    pygame.font.init()
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 50)

    title_text = font.render("Impossible Game", True, (255, 255, 255))
    instruction_text = small_font.render("Press Any Key to Start", True, (255, 255, 255))

    window.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - title_text.get_height() // 2 - 50))
    window.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2 - instruction_text.get_height() // 2 + 50))

    pygame.display.update()

def wait_for_key_press():
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                waiting = False

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

#Menu and Pause game (Esc key)
def show_menu(window, player):
    menu_font = pygame.font.Font(None, 36)
    menu_options = ["Resume", "Reset Character", "Reset Game"]
    selected_option = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        return "resume"
                    elif selected_option == 1:
                        return "reset_character"
                    elif selected_option == 2:
                        return "reset_game"
                elif event.key == pygame.K_ESCAPE:
                    return "resume"

        window.fill((64, 224, 208))
        for i, option in enumerate(menu_options):
            color = (255, 255, 255) if i == selected_option else (128, 128, 128)
            text = menu_font.render(option, True, color)
            window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 50 + i * 50))

        pygame.display.update()

#Sign Up and Log in system
def draw_auth_screen(window, mode):
    window.fill((255, 182, 193))
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 50)

    title_text = font.render(f"{'Sign Up' if mode == 'signup' else 'Log In'}", True, (255, 255, 255))
    window.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

    username_text = small_font.render("Username:", True, (255, 255, 255))
    window.blit(username_text, (WIDTH // 4, HEIGHT // 2 - 50))

    password_text = small_font.render("Password:", True, (255, 255, 255))
    window.blit(password_text, (WIDTH // 4, HEIGHT // 2 + 50))

    pygame.display.update()

def get_input(prompt):
    input_text = ""
    input_rect = pygame.Rect(WIDTH // 2, HEIGHT // 2 + (50 if prompt == "Password:" else -50), 200, 32)
    active = True

    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        pygame.draw.rect(window, (255, 255, 255), input_rect)
        text_surface = pygame.font.Font(None, 32).render(input_text, True, (0, 0, 0))
        window.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
        pygame.display.flip()

def authenticate_user(mode):
    draw_auth_screen(window, mode)
    username = get_input("Username:")
    password = get_input("Password:")

    if mode == "signup":
        with open("users.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([username, password])
        return True
    else:
        with open("users.csv", "r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username and row[1] == password:
                    return True
    return False

def auth_menu():
    while True:
        window.fill((64, 224, 208))
        font = pygame.font.Font(None, 74)
        small_font = pygame.font.Font(None, 50)

        title_text = font.render("Login/Sign up", True, (255, 255, 255))
        window.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

        signup_text = small_font.render("1. Sign Up", True, (255, 255, 255))
        window.blit(signup_text, (WIDTH // 2 - signup_text.get_width() // 2, HEIGHT // 2))

        login_text = small_font.render("2. Log In", True, (255, 255, 255))
        window.blit(login_text, (WIDTH // 2 - login_text.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    if authenticate_user("signup"):
                        return
                elif event.key == pygame.K_2:
                    if authenticate_user("login"):
                        return

if not os.path.exists("users.csv"):
    with open("users.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["username", "password"])

auth_menu()

#1 player or 2 player select screen
def mode_select_screen(window):
    options = ["1 Player", "2 Player"]
    selected = 0
    title_font = pygame.font.Font(None, 64)
    option_font = pygame.font.Font(None, 42)
    hint_font = pygame.font.Font(None, 26)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_UP):
                    selected = (selected - 1) % len(options)
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return "1P" if selected == 0 else "2P"

        window.fill((40, 40, 60))
        title = title_font.render("Select Game Mode", True, (255, 255, 255))
        window.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        for i, opt in enumerate(options):
            color = (255, 220, 60) if i == selected else (200, 200, 200)
            text = option_font.render(opt, True, color)
            window.blit(text, (WIDTH // 2 - text.get_width() // 2, 330 + i * 60))

        hint = hint_font.render("Left/Right to choose, Enter to confirm", True, (150, 150, 150))
        window.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 100))
        pygame.display.update()

#Splitting Sprite Images
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

#used for the trap folders where filenames aren't all lowercase off/on
def load_anim(folder, filename, width, height):
    path = join("assets", "Traps", folder, filename)
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    for i in range(sheet.get_width() // width):
        surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        rect = pygame.Rect(i * width, 0, width, height)
        surface.blit(sheet, (0, 0), rect)
        frames.append(pygame.transform.scale2x(surface))
    return frames

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

#the 4 playable characters, loaded once
CHARACTER_NAMES = ["MaskDude", "NinjaFrog", "PinkMan", "VirtualGuy"]
#(title, detail) - detail can reference {ability}/{jump}/{down}, filled in with
#whichever player's actual keys at the select screen
CHARACTER_ABILITIES = {
    "MaskDude": ("DASH", "Press {ability} to burst forward - breaks\nthrough enemies and ignores traps briefly"),
    "NinjaFrog": ("FROG LEAP", "Press {ability} for one big boosted jump,\nhigher and further than normal"),
    "PinkMan": ("WALL CLING", "Hold towards a wall while falling to slide\ndown slowly, press {jump} to launch off it"),
    "VirtualGuy": ("GROUND POUND", "Press {down} in mid-air to slam down and\nstun nearby enemies"),
}
CHARACTER_SPRITES = {name: load_sprite_sheets("MainCharacters", name, 32, 32, True) for name in CHARACTER_NAMES}

def key_name(key):
    return pygame.key.name(key).upper()

#rock head, fan and spiked ball frames
FAN_OFF = load_anim("Fan", "Off.png", 24, 8)
FAN_ON = load_anim("Fan", "On (24x8).png", 24, 8)
ROCK_IDLE = load_anim("Rock Head", "Idle.png", 42, 42)
ROCK_BLINK = load_anim("Rock Head", "Blink (42x42).png", 42, 42)
ROCK_LEFT_HIT = load_anim("Rock Head", "Left Hit (42x42).png", 42, 42)
ROCK_RIGHT_HIT = load_anim("Rock Head", "Right Hit (42x42).png", 42, 42)
ROCK_TOP_HIT = load_anim("Rock Head", "Top Hit (42x42).png", 42, 42)
ROCK_BOTTOM_HIT = load_anim("Rock Head", "Bottom Hit (42x42).png", 42, 42)
BALL_IMG = load_anim("Spiked Ball", "Spiked Ball.png", 28, 28)[0]
CHAIN_IMG = load_anim("Spiked Ball", "Chain.png", 8, 8)[0]
SPIKEHEAD_IDLE = load_anim("Spike Head", "Idle.png", 54, 52)
SPIKEHEAD_BLINK = load_anim("Spike Head", "Blink (54x52).png", 54, 52)

#character pick screen, used for player 1 and (if 2 player mode) player 2
def character_select_screen(window, label, controls):
    idx = 0
    title_font = pygame.font.Font(None, 50)
    name_font = pygame.font.Font(None, 46)
    desc_font = pygame.font.Font(None, 30)
    detail_font = pygame.font.Font(None, 24)
    hint_font = pygame.font.Font(None, 24)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    idx = (idx - 1) % len(CHARACTER_NAMES)
                elif event.key == pygame.K_RIGHT:
                    idx = (idx + 1) % len(CHARACTER_NAMES)
                elif event.key == pygame.K_RETURN:
                    return CHARACTER_NAMES[idx]

        name = CHARACTER_NAMES[idx]
        window.fill((30, 30, 45))

        title = title_font.render(label, True, (255, 255, 255))
        window.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))

        preview = CHARACTER_SPRITES[name]["idle_right"][0]
        preview = pygame.transform.scale(preview, (preview.get_width() * 2, preview.get_height() * 2))
        window.blit(preview, (WIDTH // 2 - preview.get_width() // 2, 240))

        arrow_font = pygame.font.Font(None, 60)
        left_arrow = arrow_font.render("<", True, (255, 255, 255))
        right_arrow = arrow_font.render(">", True, (255, 255, 255))
        window.blit(left_arrow, (WIDTH // 2 - 230, 290))
        window.blit(right_arrow, (WIDTH // 2 + 200, 290))

        name_text = name_font.render(name, True, (255, 220, 100))
        window.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, 420))

        ability_title, ability_detail = CHARACTER_ABILITIES[name]
        ability_detail = ability_detail.format(
            ability=key_name(controls['ability']),
            jump=key_name(controls['jump']),
            down=key_name(controls['down']),
        )

        title_text = desc_font.render(ability_title, True, (255, 200, 80))
        window.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 465))

        for i, line in enumerate(ability_detail.split("\n")):
            line_text = detail_font.render(line, True, (215, 215, 215))
            window.blit(line_text, (WIDTH // 2 - line_text.get_width() // 2, 500 + i * 24))

        triple_jump_hint = hint_font.render(
            "Everyone can triple jump - tap jump up to 3 times in the air", True, (150, 200, 255))
        window.blit(triple_jump_hint, (WIDTH // 2 - triple_jump_hint.get_width() // 2, 560))

        hint = hint_font.render("Left/Right to browse, Enter to pick", True, (150, 150, 150))
        window.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))
        pygame.display.update()

#controls for each player
P1_CONTROLS = {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP,
               'down': pygame.K_DOWN, 'ability': pygame.K_RSHIFT}
P2_CONTROLS = {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w,
               'down': pygame.K_s, 'ability': pygame.K_LSHIFT}

#The Player
class Player(pygame.sprite.Sprite):
    GRAVITY = 1
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, character="VirtualGuy", controls=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

        self.character = character
        self.sprites = CHARACTER_SPRITES[character]
        self.controls = controls if controls else P1_CONTROLS
        self.max_jumps = 3  #everyone gets a triple jump now

        #dash (MaskDude)
        self.dashing = False
        self.dash_cooldown = 0
        self.dash_timer = 0
        self.dash_dir = 1

        #wall cling (PinkMan)
        self.touching_wall = 0

        #ground pound (VirtualGuy)
        self.ground_pounding = False
        self.pound_impact = False

        #frog leap (NinjaFrog) - a much bigger jump than usual, on a cooldown
        self.leap_cooldown = 0

        #brief invincibility right after respawning
        self.invincible_timer = 0

    def try_jump(self):
        #wall jump takes priority if pinkman is stuck to a wall
        if self.character == "PinkMan" and self.touching_wall != 0 and self.y_vel >= 0:
            self.y_vel = -self.GRAVITY * 7
            self.x_vel = -self.touching_wall * PLAYER_VEL * 2
            self.direction = "right" if self.touching_wall == -1 else "left"
            self.animation_count = 0
            self.jump_count = 1
            self.fall_count = 0
            self.touching_wall = 0
            particles.emit(self.rect.centerx, self.rect.centery, (200, 200, 255), count=8, life=20, size=3)
            return

        if self.jump_count < self.max_jumps:
            self.y_vel = -self.GRAVITY * 8
            self.animation_count = 0
            self.jump_count += 1
            if self.jump_count == 1:
                self.fall_count = 0
            particles.emit(self.rect.centerx, self.rect.bottom, (200, 200, 200), count=6, life=20, size=3)

    def start_dash(self):
        if self.dash_cooldown <= 0 and not self.dashing and not self.ground_pounding:
            self.dashing = True
            self.dash_timer = 8
            self.dash_cooldown = 45
            self.dash_dir = 1 if self.direction == "right" else -1

    def start_ground_pound(self):
        if not self.ground_pounding:
            self.ground_pounding = True
            self.dashing = False
            self.y_vel = 22
            self.x_vel = 0

    def start_frog_leap(self):
        if self.leap_cooldown <= 0 and not self.dashing and not self.ground_pounding:
            self.y_vel = -self.GRAVITY * 14
            self.x_vel = (1 if self.direction == "right" else -1) * PLAYER_VEL * 2.5
            self.jump_count = 1
            self.fall_count = 0
            self.leap_cooldown = 70
            self.animation_count = 0
            particles.emit(self.rect.centerx, self.rect.bottom, (120, 255, 120), count=12, life=25, size=4)

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        if self.invincible_timer <= 0:
            self.hit = True
            screen_shake.add(0.6)
            particles.emit(self.rect.centerx, self.rect.centery, (255, 60, 60), count=14, life=25, size=5)

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

    def loop(self, fps):
        if self.ground_pounding:
            pass #keeps falling at a constant fast speed, no extra gravity needed
        elif self.dashing:
            self.x_vel = self.dash_dir * PLAYER_VEL * 3
            self.y_vel = 0
            self.dash_timer -= 1
            if self.dash_timer % 2 == 0:
                particles.emit(self.rect.centerx, self.rect.centery, (120, 200, 255), count=3, life=15, size=4)
            if self.dash_timer <= 0:
                self.dashing = False
        else:
            self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.leap_cooldown > 0:
            self.leap_cooldown -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        if self.ground_pounding:
            self.pound_impact = True
        self.ground_pounding = False
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
        self.touching_wall = 0

    def hit_head(self):
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.character == "PinkMan" and self.touching_wall != 0 and self.y_vel > 0:
            sprite_sheet = "wall_jump"
        elif self.y_vel < 0:
            sprite_sheet = "jump" if self.jump_count <= 1 else "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.sprites[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x, offset_y):
        if self.invincible_timer > 0 and self.invincible_timer % 6 < 3:
            return
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y - offset_y))

    def respawn(self, x, y):
        self.rect.x = x
        self.rect.y = y
        self.jump_count = 0
        self.dashing = False
        self.ground_pounding = False
        self.touching_wall = 0
        self.invincible_timer = 90

#Adding Blocks
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x, offset_y):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        #the frame only actually changes every ANIMATION_DELAY ticks, so only redo
        #the (expensive) mask when it does instead of every single frame
        if self.image is not getattr(self, "_mask_src", None):
            self.mask = pygame.mask.from_surface(self.image)
            self._mask_src = self.image
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Saw(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "saw")
        self.saw = load_sprite_sheets("Traps", "Saw", width, height)
        self.image = self.saw["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.saw[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        if self.image is not getattr(self, "_mask_src", None):
            self.mask = pygame.mask.from_surface(self.image)
            self._mask_src = self.image
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Checkpoint(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "checkpoint")
        self.checkpoint = pygame.image.load(join("assets", "checkpoint123.png")).convert_alpha()
        self.image = pygame.transform.scale(self.checkpoint, (width, height))
        self.mask = pygame.mask.from_surface(self.image)
        self.activated = False
        #respawn on the actual ground, not width/height away from the checkpoint's own
        #corner - that used to put the player partway inside the floor block and they'd
        #pop back out with a jolt the frame after respawning
        self.respawn_pos = (x + width // 2, HEIGHT - block_size - 50)

class Spike(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spike")
        self.spike = pygame.image.load(join("assets", "Traps", "Spikes", "Idle.png")).convert_alpha()
        self.image = pygame.transform.scale(self.spike, (width, height))
        self.mask = pygame.mask.from_surface(self.image)

#same idea as Spike but uses the spike head trap image, just sits there (no animation)
class Blk(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "blk")
        self.blk = pygame.image.load(join("assets", "Traps", "Spike Head", "Idle.png")).convert_alpha()
        self.image = pygame.transform.scale(self.blk, (width, height))
        self.mask = pygame.mask.from_surface(self.image)

#decorative block, not a hazard, just something to stand on
class Blk2(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "blk2")
        self.blk2 = pygame.image.load(join("assets", "op 4.png")).convert_alpha()
        self.image = pygame.transform.scale(self.blk2, (width, height))
        self.mask = pygame.mask.from_surface(self.image)

class Trampoline(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "trampoline")
        self.trampoline = load_sprite_sheets("Traps", "Trampoline", width, height)
        self.image = self.trampoline["idle"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "idle"
        self.launched = False

    def launch(self):
        self.animation_name = "Jump"
        self.launched = True
        self.animation_count = 0

    def reset(self):
        self.animation_name = "idle"
        self.launched = False

    def loop(self):
        sprites = self.trampoline[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        if self.image is not getattr(self, "_mask_src", None):
            self.mask = pygame.mask.from_surface(self.image)
            self._mask_src = self.image
        if self.animation_name == "Jump" and self.animation_count // self.ANIMATION_DELAY >= len(sprites):
            self.reset()

#fan trap - cycles on/off, blows the player upward while it's on
class Fan(Object):
    ANIMATION_DELAY = 4

    def __init__(self, x, y):
        super().__init__(x, y, 48, 16, "fan")
        self.image = FAN_OFF[0]
        self.mask = pygame.mask.from_surface(self.image)
        self.state = "on"
        self.timer = 0
        self.animation_count = 0

    def loop(self):
        self.timer += 1
        if self.state == "on" and self.timer > 160:
            self.state = "off"
            self.timer = 0
        elif self.state == "off" and self.timer > 70:
            self.state = "on"
            self.timer = 0

        frames = FAN_ON if self.state == "on" else FAN_OFF
        index = (self.animation_count // self.ANIMATION_DELAY) % len(frames)
        self.image = frames[index]
        self.animation_count += 1
        if self.image is not getattr(self, "_mask_src", None):
            self.mask = pygame.mask.from_surface(self.image)
            self._mask_src = self.image

    def blowing(self):
        return self.state == "on"

#rock head trap - sits idle, blinks a warning, then slides fast at the player and slams
class RockHead(Object):
    IDLE = "idle"
    BLINK = "blink"
    CHARGE = "charge"
    HIT = "hit"
    RETURN = "return"
    ANIMATION_DELAY = 4

    def __init__(self, x, y, direction="left", travel=480, speed=9):
        super().__init__(x, y, 84, 84, "rockhead")
        self.origin_x = x
        self.origin_y = y
        self.direction = direction
        self.travel = travel
        self.speed = speed
        self.state = self.IDLE
        self.timer = 0
        self.traveled = 0
        self.animation_count = 0
        self.image = ROCK_IDLE[0]
        self.mask = pygame.mask.from_surface(self.image)

    def reset(self):
        self.rect.x = self.origin_x
        self.rect.y = self.origin_y
        self.state = self.IDLE
        self.timer = 0
        self.traveled = 0
        self.animation_count = 0

    def stun(self):
        #ground pound interrupts a charge without teleporting it back
        self.state = self.IDLE
        self.timer = 0
        self.traveled = 0

    def loop(self):
        self.animation_count += 1

        if self.state == self.IDLE:
            self.image = ROCK_IDLE[0]
            self.timer += 1
            if self.timer > 100:
                self.state = self.BLINK
                self.timer = 0
                self.animation_count = 0

        elif self.state == self.BLINK:
            index = (self.animation_count // self.ANIMATION_DELAY) % len(ROCK_BLINK)
            self.image = ROCK_BLINK[index]
            self.timer += 1
            if self.timer > len(ROCK_BLINK) * self.ANIMATION_DELAY * 2:
                self.state = self.CHARGE
                self.timer = 0
                self.traveled = 0

        elif self.state == self.CHARGE:
            dx = dy = 0
            if self.direction == "left":
                dx = -self.speed
            elif self.direction == "right":
                dx = self.speed
            elif self.direction == "down":
                dy = self.speed
            elif self.direction == "up":
                dy = -self.speed
            self.rect.x += dx
            self.rect.y += dy
            self.traveled += self.speed
            self.image = ROCK_IDLE[0]
            if self.traveled >= self.travel:
                self.state = self.HIT
                self.timer = 0
                self.animation_count = 0

        elif self.state == self.HIT:
            hit_frames = {"left": ROCK_LEFT_HIT, "right": ROCK_RIGHT_HIT,
                          "down": ROCK_BOTTOM_HIT, "up": ROCK_TOP_HIT}[self.direction]
            index = min(self.animation_count // self.ANIMATION_DELAY, len(hit_frames) - 1)
            self.image = hit_frames[index]
            self.timer += 1
            if self.timer > len(hit_frames) * self.ANIMATION_DELAY + 25:
                self.state = self.RETURN
                self.timer = 0

        elif self.state == self.RETURN:
            dx = self.origin_x - self.rect.x
            dy = self.origin_y - self.rect.y
            dist = math.hypot(dx, dy)
            if dist < self.speed:
                self.rect.x = self.origin_x
                self.rect.y = self.origin_y
                self.state = self.IDLE
                self.timer = 0
            else:
                self.rect.x += int(self.speed * dx / dist)
                self.rect.y += int(self.speed * dy / dist)
            self.image = ROCK_IDLE[0]

        if self.image is not getattr(self, "_mask_src", None):
            self.mask = pygame.mask.from_surface(self.image)
            self._mask_src = self.image

#spiked ball on a chain, swings like a pendulum
class SpikedBall(Object):
    def __init__(self, anchor_x, anchor_y, chain_length=220, amplitude=0.8, speed=0.045, phase=0.0):
        super().__init__(anchor_x, anchor_y, 56, 56, "spikedball")
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.chain_length = chain_length
        self.amplitude = amplitude
        self.speed = speed
        self.angle = phase
        self.image = BALL_IMG
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        self.angle += self.speed
        swing = math.sin(self.angle) * self.amplitude
        ball_x = self.anchor_x + math.sin(swing) * self.chain_length
        ball_y = self.anchor_y + math.cos(swing) * self.chain_length
        self.rect.x = int(ball_x - 28)
        self.rect.y = int(ball_y - 28)

    def draw(self, win, offset_x, offset_y):
        cx = self.rect.x + 28 - offset_x
        cy = self.rect.y + 28 - offset_y
        ax = self.anchor_x - offset_x
        ay = self.anchor_y - offset_y
        steps = max(1, int(self.chain_length // 16))
        for i in range(steps):
            t = i / steps
            lx = ax + (cx - ax) * t
            ly = ay + (cy - ay) * t
            win.blit(CHAIN_IMG, (lx - 8, ly - 8))
        win.blit(self.image, (cx - 28, cy - 28))

#enemy that patrols, then chases and lunges at whichever player is closest
#rescaling + remasking a sprite every single frame for every enemy was expensive,
#and it's always the same handful of (frame, size) combos repeating, so cache them
_enemy_scaled_cache = {}

def _get_scaled_enemy_frame(frames, index, width, height):
    key = (id(frames), index, width, height)
    cached = _enemy_scaled_cache.get(key)
    if cached is None:
        img = pygame.transform.scale(frames[index], (width, height))
        cached = (img, pygame.mask.from_surface(img))
        _enemy_scaled_cache[key] = cached
    return cached

class AIEnemy(Object):
    PATROL, CHASE, LUNGE, STUNNED = "patrol", "chase", "lunge", "stunned"
    ANIMATION_DELAY = 5

    def __init__(self, x, y, width, height, patrol_range=150, aggro_range=450, speed=3, health=2):
        super().__init__(x, y, width, height, "enemy")
        self.image = pygame.transform.scale(SPIKEHEAD_IDLE[0], (width, height))
        self.mask = pygame.mask.from_surface(self.image)

        self.origin_x = x
        self.origin_y = y
        self.patrol_range = patrol_range
        self.aggro_range = aggro_range
        self.speed = speed
        self.state = self.PATROL
        self.patrol_dir = 1
        self.lunge_timer = 0
        self.stun_timer = 0
        self.max_health = health
        self.health = health
        self.alive = True
        self.animation_count = 0

    def reset(self):
        self.rect.x = self.origin_x
        self.rect.y = self.origin_y
        self.state = self.PATROL
        self.patrol_dir = 1
        self.lunge_timer = 0
        self.stun_timer = 0
        self.health = self.max_health
        self.alive = True

    def take_hit(self):
        self.health -= 1
        self.state = self.STUNNED
        self.stun_timer = 30
        particles.emit(self.rect.centerx, self.rect.centery, (255, 140, 0), count=10, life=20, size=4)
        if self.health <= 0:
            self.alive = False

    def loop(self, players):
        if not self.alive:
            return

        target = min(players, key=lambda p: math.hypot(p.rect.centerx - self.rect.centerx,
                                                         p.rect.centery - self.rect.centery))
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        self.animation_count += 1

        if self.state == self.STUNNED:
            self.stun_timer -= 1
            if self.stun_timer <= 0:
                self.state = self.PATROL

        elif self.state == self.PATROL:
            self.rect.x += int(self.patrol_dir * (self.speed * 0.6))
            if abs(self.rect.x - self.origin_x) > self.patrol_range:
                self.patrol_dir *= -1
            if distance < self.aggro_range:
                self.state = self.CHASE

        elif self.state == self.CHASE:
            if distance > self.aggro_range * 1.4:
                self.state = self.PATROL
            elif distance < 80:
                self.state = self.LUNGE
                self.lunge_timer = 20
            elif distance > 0:
                self.rect.x += int((dx / distance) * self.speed)
                self.rect.y += int((dy / distance) * self.speed * 0.5)

        elif self.state == self.LUNGE:
            self.lunge_timer -= 1
            lunge_dir = 1 if dx > 0 else -1
            self.rect.x += int(lunge_dir * self.speed * 2.5)
            if self.lunge_timer <= 0:
                self.state = self.CHASE

        frames = SPIKEHEAD_BLINK if self.state in (self.PATROL, self.CHASE) else SPIKEHEAD_IDLE
        index = (self.animation_count // self.ANIMATION_DELAY) % len(frames)
        self.image, self.mask = _get_scaled_enemy_frame(frames, index, self.width, self.height)

    def draw(self, win, offset_x, offset_y):
        if not self.alive:
            return
        if self.state == self.LUNGE:
            tint = self.image.copy()
            tint.fill((255, 80, 80, 60), special_flags=pygame.BLEND_RGBA_ADD)
            win.blit(tint, (self.rect.x - offset_x, self.rect.y - offset_y))
        else:
            win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

#coin - shared by both players, bobs up and down
class Coin(Object):
    def __init__(self, x, y, size=24):
        super().__init__(x, y, size, size, "coin")
        self.base_y = y
        self.timer = random.uniform(0, math.pi * 2)
        self.collected = False
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 215, 0), (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, (255, 245, 180), (size // 2, size // 2), size // 2 - 4)
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        self.timer += 0.1
        self.rect.y = int(self.base_y + math.sin(self.timer) * 6)

    def draw(self, win, offset_x, offset_y):
        if not self.collected:
            win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

#flag at the end of the level
class GoalFlag(Object):
    def __init__(self, x, y, width=48, height=96):
        super().__init__(x, y, width, height, "goal")
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (120, 90, 60), (width // 2 - 3, 0, 6, height))
        pygame.draw.polygon(self.image, (0, 220, 120), [(width // 2 + 3, 5), (width, 20), (width // 2 + 3, 35)])
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, win, offset_x, offset_y):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

#The Background (Function)
def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    for i in range(WIDTH // width + 2):
        for j in range(HEIGHT // height + 2):
            pos = (i * width, j * height)
            tiles.append(pos)
    return tiles, image

def draw_hud(window, level_num, coins_this_level, coins_needed, total_coins, deaths, two_player):
    font = pygame.font.Font(None, 32)
    level_text = font.render(f"Level {level_num}", True, (255, 255, 255))
    coin_text = font.render(f"Coins: {coins_this_level}/{total_coins}  (need {coins_needed})", True, (255, 215, 0))
    death_text = font.render(f"Deaths: {deaths}", True, (255, 130, 130))
    window.blit(level_text, (20, 15))
    window.blit(coin_text, (20, 45))
    window.blit(death_text, (20, 75))
    if two_player:
        mode_text = font.render("2 Player Mode", True, (180, 220, 255))
        window.blit(mode_text, (WIDTH - mode_text.get_width() - 20, 20))

def draw_message_banner(window, text):
    font = pygame.font.Font(None, 38)
    text_surf = font.render(text, True, (255, 255, 255))
    box_w = text_surf.get_width() + 50
    box_h = text_surf.get_height() + 26
    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box.fill((0, 0, 0, 190))
    pygame.draw.rect(box, (255, 210, 60), (0, 0, box_w, box_h), 3)
    window.blit(box, (WIDTH // 2 - box_w // 2, 90))
    window.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, 90 + 13))

#Background Drawing
def draw(window, background, bg_image, players, objects, coins, enemies, spiked_balls,
         checkpoints, goal, offset_x, offset_y, message=None, coins_this_level=0,
         coins_needed=0, total_coins=0):
    shake_x, shake_y = screen_shake.offset()
    ox = offset_x - shake_x
    oy = offset_y - shake_y

    for tile in background:
        window.blit(bg_image, (tile[0] + shake_x, tile[1] + shake_y))

    for obj in objects:
        obj.draw(window, ox, oy)
    for cp in checkpoints:
        cp.draw(window, ox, oy)
    if goal is not None:
        goal.draw(window, ox, oy)
    for ball in spiked_balls:
        ball.draw(window, ox, oy)
    for coin in coins:
        coin.draw(window, ox, oy)
    for enemy in enemies:
        enemy.draw(window, ox, oy)
    for p in players:
        p.draw(window, ox, oy)

    particles.draw(window, ox, oy)
    draw_hud(window, current_level_num, coins_this_level, coins_needed, total_coins, death_count, len(players) > 1)
    if message:
        draw_message_banner(window, message)
    pygame.display.update()

#Verticle Collision Defining
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
            collided_objects.append(obj)
    return collided_objects

def collide(player, objects, dx):
    #this only nudges the player's rect sideways to test a spot, the sprite itself
    #never changes, so there's no need to call update() and rebuild the mask twice
    #(that was one of the expensive things happening every frame on the web build)
    player.move(dx, 0)
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    return collided_object

#things that the player can stand on / bump into. spike, saw, fire, rockhead and blk
#count as solid too EXCEPT while dashing, when they get passed through unharmed
SOLID_ALWAYS = (Block, Trampoline, Fan, Blk2)
SOLID_WHEN_NOT_DASHING = (Spike, Saw, Fire, RockHead, Blk)

def update_player(player, objects, enemies, spiked_balls, fans, rockheads):
    keys = pygame.key.get_pressed()
    c = player.controls

    #checking every block in the whole level for collision every frame was the
    #other big slowdown on the web build - levels are thousands of pixels long
    #but the screen is only 1000 wide, so only bother with stuff near the player
    px = player.rect.centerx
    nearby = [o for o in objects if abs(o.rect.centerx - px) < 700]

    if player.ground_pounding:
        player.x_vel = 0
        solids = [o for o in nearby if isinstance(o, SOLID_ALWAYS + SOLID_WHEN_NOT_DASHING)]
        collide_left = collide_right = None
        vertical_collide = handle_vertical_collision(player, solids, player.y_vel)

    elif player.dashing:
        solids = [o for o in nearby if isinstance(o, SOLID_ALWAYS)]
        collide_left = collide(player, solids, -PLAYER_VEL * 2)
        collide_right = collide(player, solids, PLAYER_VEL * 2)
        if collide_left and player.dash_dir < 0:
            player.dashing = False
        if collide_right and player.dash_dir > 0:
            player.dashing = False
        vertical_collide = handle_vertical_collision(player, solids, player.y_vel)

    else:
        player.x_vel = 0
        solids = [o for o in nearby if isinstance(o, SOLID_ALWAYS + SOLID_WHEN_NOT_DASHING)]
        collide_left = collide(player, solids, -PLAYER_VEL * 2)
        collide_right = collide(player, solids, PLAYER_VEL * 2)

        if player.character == "PinkMan" and player.y_vel > 0 and (collide_left or collide_right):
            player.touching_wall = -1 if collide_left else 1
            player.y_vel = min(player.y_vel, 2)
        else:
            player.touching_wall = 0

        if keys[c['left']] and not collide_left:
            player.move_left(PLAYER_VEL)
        if keys[c['right']] and not collide_right:
            player.move_right(PLAYER_VEL)

        vertical_collide = handle_vertical_collision(player, solids, player.y_vel)

    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj is None:
            continue
        if obj.name in ("spike", "saw", "fire", "rockhead", "blk"):
            if not player.dashing:
                player.make_hit()
        elif obj.name == "trampoline":
            if not obj.launched:
                obj.launch()
                player.y_vel = -12
                player.fall_count = 0
                player.dashing = False
                player.ground_pounding = False

    for ball in spiked_balls:
        if pygame.sprite.collide_mask(player, ball) and not player.dashing:
            player.make_hit()

    for enemy in enemies:
        if enemy.alive and pygame.sprite.collide_mask(player, enemy):
            if player.dashing:
                enemy.take_hit()
                screen_shake.add(0.3)
            else:
                player.make_hit()

    if player.pound_impact:
        screen_shake.add(0.8)
        particles.emit(player.rect.centerx, player.rect.bottom, (200, 160, 255), count=18, life=25, size=5)
        for enemy in enemies:
            if enemy.alive:
                dist = math.hypot(enemy.rect.centerx - player.rect.centerx, enemy.rect.centery - player.rect.centery)
                if dist < 180:
                    enemy.take_hit()
        for rh in rockheads:
            dist = math.hypot(rh.rect.centerx - player.rect.centerx, rh.rect.centery - player.rect.centery)
            if dist < 180:
                rh.stun()
        player.pound_impact = False

    for fan in fans:
        if fan.blowing() and fan.rect.left < player.rect.centerx < fan.rect.right:
            if fan.rect.top - 620 < player.rect.bottom <= fan.rect.top + 6:
                player.y_vel = max(player.y_vel - 1.4, -9)
                player.fall_count = 0

def reset_world(enemies, rockheads):
    for enemy in enemies:
        enemy.reset()
    for rh in rockheads:
        rh.reset()

#builds a level from a simple text map, one row per string
#. empty   # floor   ^ spike   S saw   ! fire   F fan   T trampoline
#C coin (on a block)   K checkpoint   E enemy   G goal flag   P player start
def build_from_map(rows):
    objects = []
    coins = []
    enemies = []
    checkpoints = []
    fans = []
    goal = None
    player_start = None
    height = len(rows)

    for r, line in enumerate(rows):
        y_tile = height - r
        y_top = HEIGHT - block_size * y_tile
        for col, ch in enumerate(line):
            x = col * block_size
            if ch == '#':
                objects.append(Block(x, y_top, block_size))
            elif ch == '^':
                objects.append(Block(x, y_top, block_size))
                objects.append(Spike(x + 13, y_top - 64, 70, 64))
            elif ch == '!':
                objects.append(Block(x, y_top, block_size))
                fire = Fire(x + 32, y_top - 64, 16, 32)
                fire.on()
                objects.append(fire)
            elif ch == 'S':
                objects.append(Block(x, y_top, block_size))
                saw = Saw(x + 10, y_top - 76, 38, 38)
                saw.on()
                objects.append(saw)
            elif ch == 'F':
                objects.append(Block(x, y_top, block_size))
                fan = Fan(x + 24, y_top - 16)
                objects.append(fan)
                fans.append(fan)
            elif ch == 'T':
                objects.append(Block(x, y_top, block_size))
                objects.append(Trampoline(x + 20, y_top - 56, 28, 28))
            elif ch == 'C':
                objects.append(Block(x, y_top, block_size))
                coins.append(Coin(x + 36, y_top - 90))
            elif ch == 'c':
                coins.append(Coin(x + 36, y_top - 90))
            elif ch == 'E':
                objects.append(Block(x, y_top, block_size))
                enemies.append(AIEnemy(x + 13, y_top - 64, 70, 64))
            elif ch == 'K':
                objects.append(Block(x, y_top, block_size))
                checkpoints.append(Checkpoint(x, y_top - 104, 96, 104))
            elif ch == 'G':
                objects.append(Block(x, y_top, block_size))
                goal = GoalFlag(x + 24, y_top - 96, 48, 96)
            elif ch == 'P':
                objects.append(Block(x, y_top, block_size))
                player_start = (x, y_top - 50)

    if player_start is None:
        player_start = (50, HEIGHT - block_size - 50)

    return objects, coins, enemies, checkpoints, goal, player_start, fans

#Level 1 - the original level, just with the coins moved to safe spots and
#one spike wall thinned out because it used to be completely impossible to cross
def build_level1():
    #the fire at 6350 used to sit at offset -255, which put most of it hidden inside
    #the long_platform block right above it - moved to -352 so it sits cleanly on
    #top of the platform instead of buried in it
    fire_positions = [
        (350, -352), (100, -64), (4330, -64), (4360, -64), (4530, -64),
        (4560, -64), (4700, -64), (4730, -64), (4880, -64), (4900, -64),
        (5040, -64), (5070, -64), (6350, -352)
    ]
    fires = [Fire(x, HEIGHT - block_size + y_offset, 16, 32) for x, y_offset in fire_positions]
    for fire in fires:
        fire.on()

    #saws are actually 76px tall once drawn (not the 38 passed to the constructor,
    #that gets doubled), so -64 was sinking them a little into the ground/platform
    saw_positions = [(300, -76), (400, -76), (3850, -172)]
    saws = [Saw(x, HEIGHT - block_size + y_offset, 38, 38) for x, y_offset in saw_positions]
    for saw in saws:
        saw.on()

    trampoline_positions = [
        (2510, -100), (2790, -250), (3050, -150), (4440, -343),
        (4835, -373), (5920, -373)
    ]
    trampolines = [Trampoline(x, HEIGHT - block_size + y_offset, 28, 28) for x, y_offset in trampoline_positions]

    #this used to be one solid unbroken wall of spikes from 2301 to 3281 with zero
    #gaps in it, which meant there was no way to jump over it. pulled a few spikes
    #out (2441, 2651, 2861, 3071) so it's a run of jumpable 2-spike clusters instead
    spike_positions = [
        (600, -64), (500, -64), (700, -64), (800, -64), (600, -544),
        (400, -352), (900, -64), (1100, -64), (1250, -64), (1940, -160),
        (2120, -350), (2301, -64), (2371, -64), (2511, -64), (2581, -64),
        (2721, -64), (2791, -64), (2931, -64), (3001, -64), (3141, -64), (3211, -64),
        (5200, -64), (5400, -64), (5600, -64), (5800, -64), (4370, -350),
        (4510, -350), (4730, -350), (4870, -350), (4940, -350), (5010, -350),
        (5080, -350), (5150, -350), (5220, -350), (5290, -350), (5360, -350),
        (5430, -350), (5500, -350), (5570, -350), (5640, -350), (5710, -350),
        (5780, -350), (5850, -350), (5920, -350), (5990, -350), (6010, -350),
        (6080, -350), (6150, -350), (6220, -350), (6600, -64), (6670, -64),
        (6740, -64), (6810, -64), (6880, -64)
    ]
    spikes = [Spike(x, HEIGHT - block_size + y_offset, 70, 64) for x, y_offset in spike_positions]

    blk = Blk(1700, HEIGHT - block_size - 64, 70, 64)
    blk2 = Blk2(1600, HEIGHT - block_size - 400, 70, 64)

    enemies = [
        AIEnemy(800, HEIGHT - block_size - 64, 70, 64, patrol_range=120, aggro_range=400, speed=3),
        AIEnemy(2600, HEIGHT - block_size - 64, 70, 64, patrol_range=150, aggro_range=350, speed=3),
        AIEnemy(4600, HEIGHT - block_size - 64, 70, 64, patrol_range=200, aggro_range=450, speed=3.5),
        AIEnemy(6300, HEIGHT - block_size - 64, 70, 64, patrol_range=100, aggro_range=500, speed=4),
    ]

    checkpoint_positions = [(1400, -168), (3500, -168), (6500, -550)]
    checkpoints = [Checkpoint(x, HEIGHT - block_size + y_offset, 200, 200) for x, y_offset in checkpoint_positions]

    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 8) // block_size)]

    #(-1,8) and (-1,9) used to be here too - that made the wall next to the spawn
    #point go up to almost -100, way above the top of the screen. camera doesn't
    #follow vertically now so anything above about height 7 just isn't visible
    platform_positions = [
        (0, 2), (4, 4), (3, 4), (-1, 3), (-1, 4), (-1, 5), (-1, 6),
        (-1, 7), (-1, 2), (6, 6), (5, 6), (5, 5),
        (20, 2), (21, 2), (22, 2), (23, 2), (23, 5), (21, 3), (22, 3),
        (23, 3), (23, 4), (22, 4), (40, 2), (41, 3), (42, 2)
    ]
    platforms = [Block(x_mult * block_size, HEIGHT - y_mult * block_size, block_size) for x_mult, y_mult in platform_positions]

    long_platform = [Block(i * block_size, HEIGHT - block_size * 4, block_size) for i in range(45, 67)]
    long_platform.extend([Block(65 * block_size, HEIGHT - block_size * 3, block_size),
                           Block(66 * block_size, HEIGHT - block_size * 3, block_size)])

    #these used to climb all the way up to 11.75 blocks, which is over 1100px up -
    #completely off the top of the screen with no vertical camera follow. capped at 7
    pillar_heights = [5, 6, 7]
    pillars = []
    for h in pillar_heights:
        pillars.append(Block(48 * block_size, HEIGHT - block_size * h, block_size))
        pillars.append(Block(57 * block_size, HEIGHT - block_size * h, block_size))
    pillars.extend([
        Block(68 * block_size, HEIGHT - block_size * 5, block_size),
        Block(58 * block_size, HEIGHT - block_size * 7, block_size)
    ])

    small_block = Block(block_size * 6, HEIGHT - block_size * 3, small_block_size)

    #coins pulled off the ground hazards and spread across the actual safe stretches
    coin_positions = [50, 208, 1510, 2035, 3600, 4050, 4453, 5143, 5735, 6235]
    coins = [Coin(x, HEIGHT - block_size - 120) for x in coin_positions]

    objects = [
        *floor, *platforms, *long_platform, *pillars, small_block,
        *fires, *saws, *spikes, *trampolines, blk, blk2
    ]

    goal = GoalFlag(6900, HEIGHT - block_size - 96)

    return {
        'objects': objects, 'coins': coins, 'enemies': enemies, 'rockheads': [],
        'spiked_balls': [], 'fans': [], 'checkpoints': checkpoints, 'goal': goal,
        'player_start': (100, 100), 'respawn': (0, HEIGHT - block_size - 50), 'background': 'Green.png',
    }

#Level 2 - the original vertical/pillar level, coins unchanged (they were already fine,
#just floating bonus coins along the pillar climbs, nowhere near a hazard)
def build_level2():
    #the very first spike/fire/spike used to be at 150/250/350 - the player spawns
    #at x=100 and those hazards are ~64px wide once you count their real sprite size,
    #so the level was starting with the player already standing on top of a spike
    #with zero time to react. pushed the opening hazards back to give a proper runway.
    fire_positions = [(700, -64), (900, -350), (2200, -64), (2230, -64), (5000, -600)]
    fires = [Fire(x, HEIGHT - block_size + y_offset, 16, 32) for x, y_offset in fire_positions]
    for fire in fires:
        fire.on()

    #saws are really 76px tall (38 doubled), -64 was sinking them 12px into the ground
    saw_positions = [(600, -200), (1800, -450), (1830, -450), (3600, -76), (3630, -76), (4800, -700)]
    saws = [Saw(x, HEIGHT - block_size + y_offset, 38, 38) for x, y_offset in saw_positions]
    for saw in saws:
        saw.on()

    spike_positions = [
        (500, -64), (950, -64), (1200, -64), (1250, -64), (1300, -64),
        (2500, -64), (2570, -64), (2640, -64), (3900, -64), (3970, -64),
        (4200, -450), (4270, -450), (5200, -64), (5270, -64), (5340, -64),
        (5410, -64), (5480, -64)
    ]
    spikes = [Spike(x, HEIGHT - block_size + y_offset, 70, 64) for x, y_offset in spike_positions]

    #the first trampoline used to be at (1000, -100), which put it half-buried
    #inside the first pillar of the staircase (a trampoline is really 56px, not 28,
    #so it was hanging 30+px into the solid block next to it and didn't work).
    #moved it to ground level just before the staircase starts instead
    trampoline_positions = [(850, -56), (2900, -100), (4100, -100)]
    trampolines = [Trampoline(x, HEIGHT - block_size + y_offset, 28, 28) for x, y_offset in trampoline_positions]

    #the stairs used to climb up to height 8 (and the flat ledge sat at height 8 too),
    #which is right at the top of the screen - since the camera doesn't scroll
    #vertically you couldn't see yourself up there at all. capped everything at 7
    pillars = []
    for i, h in enumerate([2, 3, 4, 5, 6, 7]):
        pillars.append(Block((10 + i) * block_size, HEIGHT - block_size * h, block_size))
    for i, h in enumerate([7, 6, 5, 4, 3, 2]):
        pillars.append(Block((28 + i) * block_size, HEIGHT - block_size * h, block_size))

    high_ledge = [Block(i * block_size, HEIGHT - block_size * 7, block_size) for i in range(16, 28)]

    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 6) // block_size)]

    checkpoint_positions = [(1500, -168), (4300, -168)]
    checkpoints = [Checkpoint(x, HEIGHT - block_size + y_offset, 200, 200) for x, y_offset in checkpoint_positions]

    #coins along the stairs/ledge redone to match the height-7 cap above (they used
    #to go up to height 9, which is now higher than the stairs even reach)
    coins = [Coin(x, y) for x, y in [
        (1000, HEIGHT - block_size * 3), (1200, HEIGHT - block_size * 5),
        (1450, HEIGHT - block_size * 7), (2000, HEIGHT - block_size * 7),
        (2550, HEIGHT - block_size * 7), (2850, HEIGHT - block_size * 5),
        (3100, HEIGHT - block_size * 3), (4450, HEIGHT - block_size - 120),
        (5000, HEIGHT - block_size - 120)
    ]]

    enemies = [
        AIEnemy(1900, HEIGHT - block_size * 7 - 64, 70, 64, patrol_range=300, aggro_range=250, speed=3),
        AIEnemy(2300, HEIGHT - block_size - 64, 70, 64, patrol_range=150, aggro_range=400, speed=4),
        AIEnemy(3800, HEIGHT - block_size - 64, 70, 64, patrol_range=180, aggro_range=450, speed=4),
        AIEnemy(5100, HEIGHT - block_size - 64, 70, 64, patrol_range=120, aggro_range=500, speed=4.5),
    ]

    objects = [*floor, *pillars, *high_ledge, *fires, *saws, *spikes, *trampolines]
    goal = GoalFlag(5600, HEIGHT - block_size - 96)

    return {
        'objects': objects, 'coins': coins, 'enemies': enemies, 'rockheads': [],
        'spiked_balls': [], 'fans': [], 'checkpoints': checkpoints, 'goal': goal,
        'player_start': (100, HEIGHT - block_size - 100), 'respawn': (0, HEIGHT - block_size - 50), 'background': 'Blue.png',
    }

#Level 3 - the original enemy gauntlet + mini boss, coins were already all in safe
#gaps between the hazards so they're untouched
def build_level3():
    spike_positions = [
        (300, -64), (1000, -64), (1700, -64), (2400, -64), (3100, -64),
        (3800, -64), (4500, -64)
    ]
    spikes = [Spike(x, HEIGHT - block_size + y_offset, 70, 64) for x, y_offset in spike_positions]

    #saws are really 76px tall (38 doubled), -64 was sinking them 12px into the ground
    saw_positions = [(1400, -76), (2800, -76), (4200, -76)]
    saws = [Saw(x, HEIGHT - block_size + y_offset, 38, 38) for x, y_offset in saw_positions]
    for saw in saws:
        saw.on()

    platform_positions = [(8, 3), (9, 3), (10, 3), (20, 4), (21, 4), (22, 4), (32, 3), (33, 3)]
    platforms = [Block(x_mult * block_size, HEIGHT - y_mult * block_size, block_size) for x_mult, y_mult in platform_positions]

    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 6) // block_size)]

    checkpoint_positions = [(2000, -168), (4000, -168)]
    checkpoints = [Checkpoint(x, HEIGHT - block_size + y_offset, 200, 200) for x, y_offset in checkpoint_positions]

    coins = [Coin(x, HEIGHT - block_size - 120) for x in
             [500, 900, 1600, 2100, 2700, 3300, 3900, 4600, 5100]]

    enemies = [
        AIEnemy(700, HEIGHT - block_size - 64, 70, 64, patrol_range=100, aggro_range=350, speed=3),
        AIEnemy(1500, HEIGHT - block_size - 64, 70, 64, patrol_range=100, aggro_range=380, speed=3.5),
        AIEnemy(2200, HEIGHT - block_size - 64, 70, 64, patrol_range=120, aggro_range=400, speed=3.5),
        AIEnemy(2900, HEIGHT - block_size - 64, 70, 64, patrol_range=120, aggro_range=420, speed=4),
        AIEnemy(3600, HEIGHT - block_size - 64, 70, 64, patrol_range=150, aggro_range=450, speed=4),
        AIEnemy(4300, HEIGHT - block_size - 64, 70, 64, patrol_range=150, aggro_range=470, speed=4.5),
    ]
    boss = AIEnemy(5000, HEIGHT - block_size - 64, 90, 84, patrol_range=200, aggro_range=600, speed=5)
    boss.health = 5
    boss.max_health = 5
    enemies.append(boss)

    objects = [*floor, *platforms, *spikes, *saws]
    goal = GoalFlag(5500, HEIGHT - block_size - 96)

    return {
        'objects': objects, 'coins': coins, 'enemies': enemies, 'rockheads': [],
        'spiked_balls': [], 'fans': [], 'checkpoints': checkpoints, 'goal': goal,
        'player_start': (100, 100), 'respawn': (0, HEIGHT - block_size - 50), 'background': 'Brown.png',
    }

#Level 4 - new level, this is where the rock head trap shows up for the first time
def build_level4():
    LEVEL4 = '######.#!###C##########^###K####F####E####..#####C##########S###K####E####F####C#########G'
    objects, coins, enemies, checkpoints, goal, player_start, fans = build_from_map([LEVEL4])

    floor_top = HEIGHT - block_size
    rockheads = [
        RockHead(18 * block_size + 6, floor_top - 84, direction="left", travel=5 * block_size, speed=9),
        RockHead(55 * block_size + 6, floor_top - 84, direction="left", travel=5 * block_size, speed=9),
        RockHead(85 * block_size + 6, floor_top - 84, direction="left", travel=5 * block_size, speed=10),
    ]
    objects.extend(rockheads)

    default_respawn = (0, floor_top - 50)
    return {
        'objects': objects, 'coins': coins, 'enemies': enemies, 'rockheads': rockheads,
        'spiked_balls': [], 'fans': fans, 'checkpoints': checkpoints, 'goal': goal,
        'player_start': player_start, 'respawn': default_respawn, 'background': 'Purple.png',
    }

#Level 5 - The Pit: final level, everything shows up at once plus swinging spiked balls
def build_level5():
    LEVEL5 = '######E##!#..#####C#########^###K####F####..#####E####S############CK####E####..#####^###F####K####E####C#########G'
    objects, coins, enemies, checkpoints, goal, player_start, fans = build_from_map([LEVEL5])

    floor_top = HEIGHT - block_size
    rockheads = [
        RockHead(23 * block_size + 6, floor_top - 84, direction="left", travel=4 * block_size, speed=9),
        RockHead(62 * block_size + 6, floor_top - 84, direction="left", travel=4 * block_size, speed=9),
        RockHead(109 * block_size + 6, floor_top - 84, direction="left", travel=4 * block_size, speed=11),
    ]
    objects.extend(rockheads)

    #simulated the actual jump-across-the-gap frame by frame against the ball's swing:
    #these numbers give a real ~24 frame (0.4s) safe window every 1.3s where the ball
    #is out of the way, so it's always beatable if you watch and time it, but it's
    #actually in the way (y~584-600, right in a normal jump's path) the rest of the time
    spiked_balls = [
        SpikedBall(12 * block_size, 100, chain_length=500, amplitude=0.25, speed=0.08, phase=0.0),
        SpikedBall(43 * block_size, 100, chain_length=500, amplitude=0.25, speed=0.08, phase=2.0),
        SpikedBall(79 * block_size, 100, chain_length=500, amplitude=0.25, speed=0.08, phase=4.0),
    ]

    boss = AIEnemy(111 * block_size, floor_top - 84, 90, 84,
                   patrol_range=120, aggro_range=650, speed=5.5, health=7)
    enemies.append(boss)

    default_respawn = (0, floor_top - 50)
    return {
        'objects': objects, 'coins': coins, 'enemies': enemies, 'rockheads': rockheads,
        'spiked_balls': spiked_balls, 'fans': fans, 'checkpoints': checkpoints, 'goal': goal,
        'player_start': player_start, 'respawn': default_respawn, 'background': 'Gray.png',
    }

LEVELS = [build_level1, build_level2, build_level3, build_level4, build_level5]

#Defining The Window (Function)
def main(window):
    global current_level_num, coins_collected, death_count
    clock = pygame.time.Clock()

    draw_loading_screen(window)
    wait_for_key_press()
    play_background_music()
    play_sound('start')

    mode = mode_select_screen(window)
    two_player = (mode == "2P")

    char1 = character_select_screen(window, "Player 1 - pick your character", P1_CONTROLS)
    char2 = None
    if two_player:
        char2 = character_select_screen(window, "Player 2 - pick your character", P2_CONTROLS)

    level_index = 0
    coins_collected = 0
    death_count = 0

    while level_index < len(LEVELS):
        current_level_num = level_index + 1
        level_data = LEVELS[level_index]()
        background, bg_image = get_background(level_data['background'])

        objects = level_data['objects']
        coins = level_data['coins']
        enemies = level_data['enemies']
        rockheads = level_data['rockheads']
        spiked_balls = level_data['spiked_balls']
        fans = level_data['fans']
        checkpoints = level_data['checkpoints']
        goal = level_data['goal']
        player_start = level_data['player_start']
        default_respawn = level_data['respawn']

        checkpoint_pos = None
        players = [Player(player_start[0], player_start[1], 50, 50, char1, P1_CONTROLS)]
        if two_player:
            players.append(Player(player_start[0] - 60, player_start[1], 50, 50, char2, P2_CONTROLS))

        offset_x = 0
        offset_y = 0
        scroll_area_width = 200
        pit_death_y = default_respawn[1] + 500
        level_complete = False

        #need a chunk of the level's coins to be allowed through the goal
        total_coins_in_level = len(coins)
        coins_needed = max(1, round(total_coins_in_level * 0.45))
        coins_collected_this_level = 0

        run = True
        while run:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stop_background_music()
                    pygame.quit()
                    quit()

                if event.type == pygame.KEYDOWN:
                    #esc only opens the menu on the actual key press, not every frame
                    #it's held down, otherwise resuming would just reopen it straight away
                    if event.key == pygame.K_ESCAPE:
                        menu_action = show_menu(window, players[0])
                        if menu_action == "reset_character":
                            for p in players:
                                p.make_hit()
                        elif menu_action == "reset_game":
                            for i, p in enumerate(players):
                                p.respawn(player_start[0] - i * 60, player_start[1])
                            checkpoint_pos = None
                            reset_world(enemies, rockheads)
                            offset_x = 0

                    for p in players:
                        if event.key == p.controls['jump']:
                            p.try_jump()
                        elif p.character == "MaskDude" and event.key == p.controls['ability']:
                            p.start_dash()
                        elif p.character == "NinjaFrog" and event.key == p.controls['ability']:
                            p.start_frog_leap()
                        elif p.character == "VirtualGuy" and event.key == p.controls['down']:
                            p.start_ground_pound()

            for p in players:
                p.loop(FPS)
            particles.update()
            screen_shake.update()

            #no point animating traps nobody is anywhere near - same idea as the
            #collision culling, levels are way longer than the screen
            player_xs = [p.rect.centerx for p in players]
            for obj in objects:
                if isinstance(obj, (Fire, Saw, Trampoline, Fan, RockHead)):
                    if any(abs(obj.rect.centerx - x) < 700 for x in player_xs):
                        obj.loop()
            for ball in spiked_balls:
                ball.loop()
            for coin in coins:
                coin.loop()
            for enemy in enemies:
                enemy.loop(players)

            for p in players:
                update_player(p, objects, enemies, spiked_balls, fans, rockheads)

            for coin in coins:
                if not coin.collected:
                    for p in players:
                        if pygame.sprite.collide_mask(p, coin):
                            coin.collected = True
                            coins_collected += 1
                            coins_collected_this_level += 1
                            particles.emit(coin.rect.centerx, coin.rect.centery, (255, 215, 0), count=10, life=20, size=3)
                            play_sound('coin')
                            break
            coins = [c for c in coins if not c.collected]

            for cp in checkpoints:
                for p in players:
                    if pygame.sprite.collide_mask(p, cp):
                        if not cp.activated:
                            play_sound('checkpoint')
                            particles.emit(cp.rect.centerx, cp.rect.centery, (255, 215, 0), count=20, life=35, size=5)
                        cp.activated = True
                        checkpoint_pos = cp.respawn_pos

            goal_message = None
            if goal is not None and any(goal.rect.colliderect(p.rect) for p in players):
                if coins_collected_this_level >= coins_needed:
                    level_complete = True
                    run = False
                else:
                    short = coins_needed - coins_collected_this_level
                    goal_message = (f"Not enough coins! Need {short} more "
                                     f"({coins_collected_this_level}/{coins_needed}) to move on")

            draw(window, background, bg_image, players, objects, coins,
                 [e for e in enemies if e.alive], spiked_balls, checkpoints, goal, offset_x, offset_y,
                 message=goal_message, coins_this_level=coins_collected_this_level,
                 coins_needed=coins_needed, total_coins=total_coins_in_level)

            anyone_died = False
            for p in players:
                if p.rect.top > pit_death_y:
                    p.hit = True
                if p.hit:
                    anyone_died = True
                    play_sound('die')
                    death_count += 1
                    if checkpoint_pos:
                        p.rect.x, p.rect.y = checkpoint_pos
                    else:
                        p.rect.x, p.rect.y = default_respawn
                    p.hit = False
                    p.invincible_timer = 60
                    p.dashing = False
                    p.ground_pounding = False

            if anyone_died:
                reset_world(enemies, rockheads)
                #snap the camera back onto the player straight away, otherwise if you
                #respawn behind where the camera had scrolled to, you'd be stuck invisible
                #off the left side of the screen until you happened to walk left into view
                offset_x = max(0, players[0].rect.centerx - WIDTH // 2)

            #camera only follows left/right, never up/down
            for p in players:
                if ((p.rect.right - offset_x >= WIDTH - scroll_area_width) and p.x_vel > 0) or (
                        (p.rect.left - offset_x <= scroll_area_width) and p.x_vel < 0):
                    offset_x += p.x_vel

        if level_complete:
            show_level_complete_screen(window, level_index + 1)
            level_index += 1
        else:
            break

    show_game_complete_screen(window)
    stop_background_music()
    pygame.quit()
    quit()

#level transition screens
def show_level_complete_screen(window, level_num):
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 40)
    start = time.time()
    while time.time() - start < 2.5:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        window.fill((30, 30, 40))
        text = font.render(f"Level {level_num} Complete!", True, (255, 255, 255))
        sub = small_font.render(f"Coins: {coins_collected}", True, (255, 215, 0))
        window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 60))
        window.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))
        pygame.display.update()

def show_game_complete_screen(window):
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 40)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                waiting = False
        window.fill((10, 40, 20))
        text = font.render("You Beat The Game!", True, (255, 255, 255))
        sub = small_font.render(f"Total Coins Collected: {coins_collected}", True, (255, 215, 0))
        window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 60))
        window.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))
        pygame.display.update()

#END GAME
if __name__ == "__main__":
    main(window)
