# Impossible Platformer Game
#Nishchay Bhudia

import pygame

# initialise pygame
pygame.init()

#display settings
WIDTH = 1000
HEIGHT = 800

#create window 
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Impossible Game")

#main loop
run = True

while run:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    window.fill((0, 0, 0))

    pygame.display.update()

pygame.quit()
