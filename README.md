# Impossible-Platformer
An impossible platformer game that you cannot complete . I dare you !

---

# Devlog 1 : 0-25 mins
I started the project by setting up the basic Pygame environment. The first goal was simply to get a window appearing on screen. After importing Pygame and initialising it, I created a 1000×800 game window and added a title to the window.

I then created a basic game loop which keeps the program running until the player closes the window. At this stage there are no graphics, characters or levels. The project currently only displays a blank screen.

Problems Encountered

No major issues were encountered during this stage. The main focus was confirming that Pygame was installed correctly and that the game window could be opened and closed safely.


![DEVLOG 1](https://github.com/Hidden-Ghost-123/Impossible-Platformer/blob/main/Screenshot%202026-06-10%20203328.png)


---

# Devlog 2 : 25 - 120 mins

### Objectives
- Add FPS control
- Create project constants
- Improve game loop structure
- Add a background colour
- Prepare the codebase for future player development
- Progress

After successfully creating the game window, I focused on improving the structure of the program. A frame rate limit was added using pygame.time.Clock() to ensure the game runs consistently on different computers.

I created constants for the screen width, screen height, and FPS rather than hard-coding values throughout the program. This will make future changes easier.

I also replaced the plain black screen with a temporary sky-blue background. This makes the project feel more like a game environment and provides a better foundation for testing future features.

Although no player has been added yet, the game loop is now stable and organised enough to begin implementing movement systems.

Problems Encountered

Initially the game was running as fast as the computer would allow, causing unnecessary CPU usage. Adding FPS control fixed this issue and ensures consistent performance.

### Testing Performed
- Verified the game window opens correctly.
- Verified the frame rate remains stable at 60 FPS.
- Confirmed the window closes without errors.
- Next Steps
- Create the player object.
- Draw the player on screen.
- Begin implementing horizontal movement using keyboard controls.

### Next Steps
- Create the player object.
- Draw the player on screen.
- Begin implementing horizontal movement using keyboard controls.

---
