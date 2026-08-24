"""
patterns_library.py -- A categorized library of well-known Conway's Game
of Life patterns, for insertion ("stamping") onto the live grid.

Selection and categorization follows Catagolue's census of naturally
occurring objects (https://catagolue.hatsya.com/syntheses -- the
database of cheapest known glider syntheses, built from the same
underlying object census as LifeWiki's "Most common objects on
Catagolue" list) plus the classic hand-discovered guns and methuselahs
that Catagolue's synthesis collection also documents. Where a pattern
appears in that top-100 census, its Catagolue commonality rank is
noted in the description.

Every pattern's coordinates were verified computationally against
their documented behavior before inclusion here (still lifes checked
for a stable first step; oscillators checked to return to their start
after their documented period; spaceships checked to translate by
their documented offset after their documented period; methuselahs
checked against their documented stabilization generation/population).

Each entry is (name, cells, description), where cells is a list of
(row, col) offsets of live cells relative to the pattern's top-left
bounding-box corner.
"""

from __future__ import annotations

# ----------------------------------------------------------------------
# Still lifes -- patterns that never change (period 1)
# ----------------------------------------------------------------------
STILL_LIFES = [
    ("Block", [(0, 0), (0, 1), (1, 0), (1, 1)],
     "4 cells. The single most common object on Catagolue -- about "
     "1 in 3 soup objects."),
    ("Beehive", [(0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 2)],
     "6 cells. 3rd most common Catagolue object; a hexagonal ring."),
    ("Loaf", [(0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 3), (3, 2)],
     "7 cells. 5th most common; a beehive pinched to a point."),
    ("Boat", [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)],
     "5 cells. 6th most common; a block with one corner shifted in."),
    ("Ship", [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)],
     "6 cells. 7th most common; two boats sharing a diagonal seam."),
    ("Tub", [(0, 1), (1, 0), (1, 2), (2, 1)],
     "4 cells. 8th most common; smallest still life with a hole."),
    ("Pond", [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)],
     "8 cells. 9th most common; a diamond ring, two boats fused."),
    ("Long boat", [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2)],
     "7 cells. 10th most common Catagolue object; an elongated boat."),
    ("Barge", [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2)],
     "6 cells. 14th most common; a diamond one cell longer than a tub."),
    ("Eater 1", [(0, 0), (0, 1), (1, 0), (2, 1), (2, 2), (2, 3), (3, 3)],
     "7 cells. 17th most common. A catalyst (\"fishhook\") that absorbs "
     "a glider and returns to shape unharmed."),
]

# ----------------------------------------------------------------------
# Oscillators -- patterns that return to their start after N > 1 steps
# ----------------------------------------------------------------------
OSCILLATORS = [
    ("Blinker", [(0, 0), (0, 1), (0, 2)],
     "3 cells, period 2. 2nd most common object and the smallest "
     "oscillator: flips between a row and a column."),
    ("Toad", [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
     "6 cells, period 2. 11th most common; two offset rows of three."),
    ("Beacon", [(0, 0), (0, 1), (1, 0), (2, 3), (3, 2), (3, 3)],
     "6 cells, period 2. 13th most common; two blocks touching at "
     "alternating corners."),
    ("Clock", [(0, 2), (1, 0), (1, 2), (2, 1), (2, 3), (3, 1)],
     "6 cells, period 2. 62nd most common Catagolue object."),
    ("Pulsar", None,  # generated programmatically below
     "48 cells, period 3. 21st most common; the largest small "
     "oscillator in common use, with 4-fold symmetry."),
    ("Pentadecathlon", [
        (0, 2), (0, 7), (1, 0), (1, 1), (1, 3), (1, 4), (1, 5), (1, 6), (1, 8), (1, 9), (2, 2), (2, 7),
    ], "12 cells, period 15. 52nd most common; the name refers to "
       "its period, not its cell count."),
]


def _make_pulsar():
    rows_edge = (0, 5, 7, 12)
    cols_mid = (2, 3, 4, 8, 9, 10)
    cols_edge = (0, 5, 7, 12)
    rows_mid = (2, 3, 4, 8, 9, 10)
    cells = set()
    for r in rows_edge:
        for c in cols_mid:
            cells.add((r, c))
    for c in cols_edge:
        for r in rows_mid:
            cells.add((r, c))
    return sorted(cells)


for _i, (_name, _cells, _desc) in enumerate(OSCILLATORS):
    if _cells is None:
        OSCILLATORS[_i] = (_name, _make_pulsar(), _desc)

# ----------------------------------------------------------------------
# Spaceships -- patterns that translate across the grid, period N
# ----------------------------------------------------------------------
SPACESHIPS = [
    ("Glider", [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
     "5 cells, period 4, moves diagonally at c/4. 4th most common "
     "object and the smallest, most common spaceship."),
    ("Lightweight spaceship (LWSS)", [
        (0, 0), (0, 3), (1, 4), (2, 0), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4),
    ], "9 cells, period 4, moves orthogonally at c/2. 18th most "
       "common; the most common orthogonal spaceship."),
    ("Middleweight spaceship (MWSS)", [
        (0, 2), (1, 0), (1, 4), (2, 5), (3, 0), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5),
    ], "11 cells, period 4, moves orthogonally at c/2. Found by "
       "John Conway in 1970; one column wider than the LWSS."),
    ("Heavyweight spaceship (HWSS)", [
        (0, 2), (0, 3), (1, 0), (1, 5), (2, 6), (3, 0), (3, 6), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
    ], "13 cells, period 4, moves orthogonally at c/2. The widest "
       "of the three classic c/2 spaceships."),
]

# ----------------------------------------------------------------------
# Guns -- patterns that periodically emit spaceships
# ----------------------------------------------------------------------
GUNS = [
    ("Gosper glider gun", [
        (0, 24), (1, 22), (1, 24), (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
        (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35),
        (4, 0), (4, 1), (4, 10), (4, 16), (4, 20), (4, 21),
        (5, 0), (5, 1), (5, 10), (5, 14), (5, 16), (5, 17), (5, 22), (5, 24),
        (6, 10), (6, 16), (6, 24),
        (7, 11), (7, 15),
        (8, 12), (8, 13),
    ], "36 cells, period 30 -- emits a glider every 30 generations "
       "forever. Found by Bill Gosper in 1970; the first pattern "
       "with unbounded growth."),
]

# ----------------------------------------------------------------------
# Methuselahs -- small patterns with long, chaotic evolutions before
# settling into a stable or periodic remainder
# ----------------------------------------------------------------------
METHUSELAHS = [
    ("R-pentomino", [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
     "5 cells. Evolves chaotically for 1103 generations, emitting "
     "gliders, before settling at a population of 116."),
    ("Diehard", [(0, 6), (1, 0), (1, 1), (2, 1), (2, 5), (2, 6), (2, 7)],
     "7 cells. Never has more than 7 live cells at once, yet takes "
     "exactly 130 generations to vanish completely."),
    ("Acorn", [(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)],
     "7 cells. Takes 5206 generations to stabilize, ending at "
     "population 633 with 13 gliders escaped."),
]

# ----------------------------------------------------------------------
# Combined, ordered category list for UI consumption
# ----------------------------------------------------------------------
PATTERN_CATEGORIES = [
    ("Still Life", STILL_LIFES),
    ("Oscillator", OSCILLATORS),
    ("Spaceship", SPACESHIPS),
    ("Gun", GUNS),
    ("Methuselah", METHUSELAHS),
]
