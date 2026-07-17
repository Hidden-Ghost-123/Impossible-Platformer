# Impossible Platformer

An impossible platformer game that you cannot complete. I dare you.

Started as a basic pygame platformer following along with a tutorial, then I kept adding stuff to it until it turned into its own thing - 4 playable characters with different abilities, 2 player mode, 5 levels, a coin system, and a bunch of traps that all try to kill you in different ways.

## Playing it

**In browser, straight from this repo:** the `docs` folder has the same web build already unpacked, ready for GitHub Pages - turn it on under this repo's Settings -> Pages -> Source: "Deploy from a branch" -> Branch: `main`, folder: `/docs` -> Save. GitHub will give you the live link a minute or two later (usually `https://hidden-ghost-123.github.io/Impossible-Platformer/`).

**In browser, via itch.io:** grab `impossible platformer.zip` from this repo and upload it to itch.io (or any host that takes a zipped HTML5 build) - it's already packaged for that, `index.html` and all. Set the viewport to 1000x800.

**On your own machine:** you need Python and pygame installed.

```
pip install pygame
python "Platformer Final.py"
```

Make sure the `assets` folder stays sitting next to the script, it loads everything with relative paths.

First time you run it you'll be asked to sign up / log in (local only, just writes to a `users.csv` next to the game, nothing gets sent anywhere).

## Controls

|              | Player 1     | Player 2   |
|--------------|--------------|------------|
| Move         | Left / Right | A / D      |
| Jump         | Up           | W          |
| Ability key  | Right Shift  | Left Shift |
| Ground pound | Down         | S          |
| Pause        | Esc          | Esc        |

Everyone can jump 3 times in the air (jump, double jump, triple jump), on top of whatever their character's special move is.

## The characters

- **MaskDude** - Dash. Short burst forward, breaks through enemies and ignores traps while it lasts.
- **NinjaFrog** - Frog Leap. One much bigger jump than normal, on a cooldown.
- **PinkMan** - Wall Cling. Slide down walls slowly instead of falling, jump off them to launch away.
- **VirtualGuy** - Ground Pound. Slam down out of the air, stuns nearby enemies when you land.

2 player mode has both players sharing the same level, coins and checkpoints.

## Levels

1. Spike Run
2. Sky Climb
3. Enemy Gauntlet
4. Rock Slide
5. The Pit

Each level has a minimum number of coins you need to collect before the goal will actually let you through - the game tells you how many more you need if you try and go through short.

## Traps

Fire, saws, spikes, trampolines, a fan that blows you upward, a rock head that slams sideways into you, and a spiked ball swinging on a chain. Enemies patrol an area and will chase and lunge at you if you get close - dash into one to knock it out.

## Assets

Character and trap sprites are from the free Pixel Adventure asset packs (Pixel Frog on itch.io). Everything else - the code, the levels, the sounds - is original.

## License

MIT, see `LICENSE`.
