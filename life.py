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
        # ages[r,c]: how many consecutive generations this cell has been
        # continuously alive (0 when dead, 1 the generation it's born).
        self.ages = np.zeros((rows, cols), dtype=np.int32)
        # lineage[r,c]: an opaque "family" id for the cell's ancestry (0 =
        # no lineage / dead). A cell born from parents inherits whichever
        # lineage id is most common among its live neighbors; a cell that
        # appears with no live parents (manual toggle, randomize, a pattern
        # stamp, or spontaneous birth under an unusual B0 rule) starts a
        # brand new lineage id of its own.
        self.lineage = np.zeros((rows, cols), dtype=np.int64)
        self._next_lineage_id = 1
        self.generation = 0

    def _new_lineage_id(self) -> int:
        lineage_id = self._next_lineage_id
        self._next_lineage_id += 1
        return lineage_id

    # ------------------------------------------------------------------
    # Grid management
    # ------------------------------------------------------------------
    def resize(self, rows: int, cols: int) -> None:
        """Resize the grid, preserving overlapping cell state (top-left aligned)."""
        new_cells = np.zeros((rows, cols), dtype=np.uint8)
        new_ages = np.zeros((rows, cols), dtype=np.int32)
        new_lineage = np.zeros((rows, cols), dtype=np.int64)
        r = min(rows, self.rows)
        c = min(cols, self.cols)
        new_cells[:r, :c] = self.cells[:r, :c]
        new_ages[:r, :c] = self.ages[:r, :c]
        new_lineage[:r, :c] = self.lineage[:r, :c]
        self.cells = new_cells
        self.ages = new_ages
        self.lineage = new_lineage
        self.rows, self.cols = rows, cols

    def clear(self) -> None:
        self.cells.fill(0)
        self.ages.fill(0)
        self.lineage.fill(0)
        self.generation = 0

    def randomize(self, density: float, rng: np.random.Generator | None = None) -> None:
        """Fill the grid with live cells at the given probability [0, 1].

        Each live cell seeded this way is its own founding lineage, so the
        heredity map starts maximally fragmented and you can watch families
        merge, compete, and go extinct as the simulation runs.
        """
        rng = rng or np.random.default_rng()
        self.cells = (rng.random((self.rows, self.cols)) < density).astype(np.uint8)
        self.ages = self.cells.astype(np.int32)  # newly alive cells start at age 1
        alive_r, alive_c = self.cells.nonzero()
        self.lineage = np.zeros((self.rows, self.cols), dtype=np.int64)
        n = len(alive_r)
        if n:
            new_ids = np.arange(self._next_lineage_id, self._next_lineage_id + n, dtype=np.int64)
            self.lineage[alive_r, alive_c] = new_ids
            self._next_lineage_id += n
        self.generation = 0

    def toggle_cell(self, row: int, col: int, lineage: int | None = None) -> None:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            now_alive = not self.cells[row, col]
            self.set_cell(row, col, 1 if now_alive else 0, lineage=lineage)

    def set_cell(self, row: int, col: int, value: int, lineage: int | None = None) -> None:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return
        if value:
            already_alive = bool(self.cells[row, col])
            self.cells[row, col] = 1
            if not already_alive:
                self.ages[row, col] = 1
                self.lineage[row, col] = lineage if lineage is not None else self._new_lineage_id()
        else:
            self.cells[row, col] = 0
            self.ages[row, col] = 0
            self.lineage[row, col] = 0

    def population(self) -> int:
        return int(self.cells.sum())

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------
    def _shifted_neighbors(self, array: np.ndarray) -> list[np.ndarray]:
        """Return the 8 shifted views of `array` for each neighbor offset,
        respecting the current wrap setting. Shared by neighbor-count and
        lineage-inheritance logic so both use identical adjacency."""
        shifts = []
        if self.wrap:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    shifts.append(np.roll(np.roll(array, dr, axis=0), dc, axis=1))
        else:
            padded = np.pad(array, 1, mode="constant", constant_values=0)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    shifts.append(padded[1 + dr : 1 + dr + self.rows, 1 + dc : 1 + dc + self.cols])
        return shifts

    def _neighbor_counts(self) -> np.ndarray:
        """Return an array of live-neighbor counts for every cell."""
        total = np.zeros_like(self.cells, dtype=np.uint8)
        for shifted in self._shifted_neighbors(self.cells):
            total += shifted
        return total

    def _inherited_lineage(self) -> np.ndarray:
        """For every cell, the most common nonzero lineage id among its 8
        neighbors (0 if none are alive). Used to assign newborn cells a
        lineage inherited from whichever family of parents is most
        represented among the neighbors that caused the birth."""
        candidates = np.stack(self._shifted_neighbors(self.lineage))  # shape (8, rows, cols)
        nonzero = candidates != 0
        # equal[i, j, r, c] = candidates[i] == candidates[j], counted only
        # where both sides are alive lineages so two dead (0) neighbors
        # never "vote" for each other.
        equal = (candidates[:, None, ...] == candidates[None, :, ...]) & nonzero[None, :, ...]
        counts = equal.sum(axis=1)  # shape (8, rows, cols): votes for each candidate slot
        counts = np.where(nonzero, counts, -1)  # dead slots can never win
        winner_slot = np.argmax(counts, axis=0)
        winner_lineage = np.take_along_axis(candidates, winner_slot[None, ...], axis=0)[0]
        any_alive_neighbor = nonzero.any(axis=0)
        return np.where(any_alive_neighbor, winner_lineage, 0)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Serialize the grid to a JSON-friendly dict (sparse cell list)."""
        rows, cols = self.cells.nonzero()
        return {
            "rows": self.rows,
            "cols": self.cols,
            "wrap": self.wrap,
            "birth": sorted(self.birth),
            "survive": sorted(self.survive),
            "generation": self.generation,
            "alive_cells": [[int(r), int(c)] for r, c in zip(rows, cols)],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LifeGrid":
        grid = cls(
            rows=d["rows"],
            cols=d["cols"],
            wrap=d.get("wrap", True),
            birth=frozenset(d.get("birth", [3])),
            survive=frozenset(d.get("survive", [2, 3])),
        )
        # Cells loaded from a file are treated as freshly born, each starting
        # its own lineage -- the save format doesn't carry age/heredity history.
        for r, c in d.get("alive_cells", []):
            grid.set_cell(r, c, 1)
        grid.generation = d.get("generation", 0)
        return grid

    def step(self) -> None:
        """Advance the simulation by one generation according to the B/S rule."""
        counts = self._neighbor_counts()
        alive = self.cells.astype(bool)

        born = np.isin(counts, list(self.birth)) & ~alive
        survives = np.isin(counts, list(self.survive)) & alive
        new_alive = born | survives

        # Age: survivors age by one generation, newborns start at 1, the rest are dead.
        new_ages = np.where(survives, self.ages + 1, np.where(born, 1, 0)).astype(np.int32)

        # Lineage: survivors keep their lineage; newborns inherit the modal
        # lineage among their live neighbors, or start a fresh lineage if
        # they have no live neighbors at all (only possible under a custom
        # B0 rule -- ordinary births always have live parents).
        inherited = self._inherited_lineage()
        new_lineage = np.where(survives, self.lineage, 0)
        born_with_parents = born & (inherited != 0)
        new_lineage = np.where(born_with_parents, inherited, new_lineage)
        born_spontaneous_r, born_spontaneous_c = np.nonzero(born & (inherited == 0))
        n_spontaneous = len(born_spontaneous_r)
        if n_spontaneous:
            fresh_ids = np.arange(self._next_lineage_id, self._next_lineage_id + n_spontaneous, dtype=np.int64)
            new_lineage[born_spontaneous_r, born_spontaneous_c] = fresh_ids
            self._next_lineage_id += n_spontaneous

        self.cells = new_alive.astype(np.uint8)
        self.ages = new_ages
        self.lineage = new_lineage
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
