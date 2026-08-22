"""
life.py -- Core simulation engine for Conway's Game of Life.

Implements a generalized "Life-like" cellular automaton (B/S notation),
of which Conway's original rule (B3/S23) is just one instance. Kept
completely independent of pygame/rendering so it can be unit tested or
reused headlessly.
"""

from __future__ import annotations

import numpy as np


class LifeGrid:
    """A toroidal-or-bounded 2D binary cellular automaton grid."""

    def __init__(
        self,
        rows: int,
        cols: int,
        wrap: bool = True,
        birth: frozenset[int] = frozenset({3}),
        survive: frozenset[int] = frozenset({2, 3}),
    ):
        self.rows = rows
        self.cols = cols
        self.wrap = wrap
        self.birth = set(birth)
        self.survive = set(survive)
        self.cells = np.zeros((rows, cols), dtype=np.uint8)
        self.generation = 0

    # ------------------------------------------------------------------
    # Grid management
    # ------------------------------------------------------------------
    def resize(self, rows: int, cols: int) -> None:
        """Resize the grid, preserving overlapping cell state (top-left aligned)."""
        new = np.zeros((rows, cols), dtype=np.uint8)
        r = min(rows, self.rows)
        c = min(cols, self.cols)
        new[:r, :c] = self.cells[:r, :c]
        self.cells = new
        self.rows, self.cols = rows, cols

    def clear(self) -> None:
        self.cells.fill(0)
        self.generation = 0

    def randomize(self, density: float, rng: np.random.Generator | None = None) -> None:
        """Fill the grid with live cells at the given probability [0, 1]."""
        rng = rng or np.random.default_rng()
        self.cells = (rng.random((self.rows, self.cols)) < density).astype(np.uint8)
        self.generation = 0

    def toggle_cell(self, row: int, col: int) -> None:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.cells[row, col] ^= 1

    def set_cell(self, row: int, col: int, value: int) -> None:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.cells[row, col] = 1 if value else 0

    def population(self) -> int:
        return int(self.cells.sum())

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------
    def _neighbor_counts(self) -> np.ndarray:
        """Return an array of live-neighbor counts for every cell.

        Uses 8 shifted views summed together -- O(rows*cols), no
        external dependency beyond numpy, and correct for both wrapped
        (toroidal) and bounded (dead border) topologies.
        """
        c = self.cells
        if self.wrap:
            total = np.zeros_like(c, dtype=np.uint8)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    total += np.roll(np.roll(c, dr, axis=0), dc, axis=1)
            return total
        else:
            padded = np.pad(c, 1, mode="constant", constant_values=0)
            total = np.zeros_like(c, dtype=np.uint8)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    total += padded[1 + dr : 1 + dr + self.rows, 1 + dc : 1 + dc + self.cols]
            return total

    def step(self) -> None:
        """Advance the simulation by one generation according to the B/S rule."""
        counts = self._neighbor_counts()
        alive = self.cells.astype(bool)

        born = np.isin(counts, list(self.birth)) & ~alive
        survives = np.isin(counts, list(self.survive)) & alive

        self.cells = (born | survives).astype(np.uint8)
        self.generation += 1


# Well-known Life-like rule presets, expressed as (birth, survive) neighbor sets.
RULE_PRESETS: dict[str, tuple[frozenset[int], frozenset[int]]] = {
    "Conway's Life (B3/S23)": (frozenset({3}), frozenset({2, 3})),
    "HighLife (B36/S23)": (frozenset({3, 6}), frozenset({2, 3})),
    "Day & Night (B3678/S34678)": (frozenset({3, 6, 7, 8}), frozenset({3, 4, 6, 7, 8})),
    "Seeds (B2/S)": (frozenset({2}), frozenset()),
    "Life without Death (B3/S012345678)": (frozenset({3}), frozenset(range(9))),
    "Replicator (B1357/S1357)": (frozenset({1, 3, 5, 7}), frozenset({1, 3, 5, 7})),
    "Maze (B3/S12345)": (frozenset({3}), frozenset({1, 2, 3, 4, 5})),
}
