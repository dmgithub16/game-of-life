# Conway's Game of Life

An interactive implementation of Conway's Game of Life (and Life-like
cellular automata generally) in Python, using `pygame` for rendering
and `numpy` for the simulation core. Every parameter of the automaton
is exposed as a live GUI control — nothing is hardcoded that you'd
have to edit source to change.

## Features / exposed variables

| Control | What it does |
|---|---|
| **Speed (gen/sec)** | Simulation rate, 1–60 generations/second |
| **Randomize density** | Probability a cell is alive when you hit Randomize |
| **Cell size** | Pixel size per cell; grid dimensions auto-recompute to fill the fixed canvas (4–25 px) |
| **Wrap-around edges** | Toroidal topology (edges wrap) vs. bounded (dead border) |
| **Show grid lines** | Toggle the cell gridlines |
| **Birth (B)** | Which live-neighbor counts (0–8) cause a dead cell to become alive |
| **Survive (S)** | Which live-neighbor counts (0–8) keep a live cell alive |
| **Rule presets** | One-click B/S presets: Conway's Life, HighLife, Day & Night, Seeds, Life without Death, Replicator, Maze |

Because Birth/Survive are independently editable neighbor-count sets,
this isn't limited to Conway's original B3/S23 rule — it's a general
Life-like automaton sandbox.

## Controls

- **Left click** a cell to toggle it (works whether running or paused)
- **Left-click drag** to paint/erase multiple cells at once
- **Space** — play / pause
- **S** — single-step (while paused)
- **R** — randomize the grid using the current density
- **C** — clear the grid
- **Esc** or close the window — quit

## Running it

```bash
pip install -r requirements.txt
python3 game_of_life.py
```

Requires a display (this is a windowed pygame app — it won't run
headless without a virtual framebuffer like `Xvfb`).

## Project structure

```
game-of-life/
├── life.py           # Pure simulation engine (numpy), no pygame dependency
├── widgets.py         # Minimal reusable pygame GUI widgets (Slider, Button, Toggle, ToggleGrid)
├── game_of_life.py     # Main application: window, panel wiring, main loop
├── requirements.txt
└── README.md
```

`life.py` is intentionally decoupled from pygame so the rule engine
can be unit-tested or reused (e.g. in a headless script or a
different front end) without pulling in a display dependency.

## Rules background

Conway's Game of Life is the B3/S23 case of a "Life-like" cellular
automaton in B/S notation: a dead cell with exactly **3** live
neighbors is **B**orn, and a live cell **S**urvives with **2 or 3**
live neighbors; otherwise it dies (under- or over-population).
