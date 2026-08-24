"""
visualization.py -- Renders each live cell as a small pygame Surface
("tile") that encodes two independent pieces of information:

  - AGE, via color: a cell fades from a bright warm color when just born
    toward the grid's standard blue the longer it survives continuously.
  - HEREDITY, via a pixel pattern: cells descended from the same founding
    ancestor (the same "lineage", see life.LifeGrid) share a textured
    pattern, distinct from other lineages' patterns.

Tiles are cached by (age_bucket, pattern_index, cell_size) so a frame
with thousands of live cells costs one dict lookup + one blit per cell,
not a fresh set of draw calls -- this is what keeps the simulation fast
at high generation rates (see life.py's own step() performance, which
this rendering must not undercut).
"""

from __future__ import annotations

import pygame

AGE_CAP = 20          # generations at which the age color reaches its oldest shade
AGE_BUCKETS = 16       # quantization steps for the color gradient (cache granularity)
NUM_PATTERNS = 8        # distinct heredity pixel-pattern types
PATTERN_MIN_CELL_SIZE = 8  # below this cell size, patterns degrade to solid fill (too small to read)

COLOR_YOUNG = (255, 235, 150)  # bright warm -- just born
COLOR_OLD = (90, 200, 255)      # the grid's standard blue -- long-lived


def age_to_bucket(age: int) -> int:
    """Quantize an age (generations continuously alive) into a cache bucket."""
    t = min(max(age, 0), AGE_CAP) / AGE_CAP
    return round(t * (AGE_BUCKETS - 1))


def age_to_bucket_array(ages: "np.ndarray") -> "np.ndarray":
    """Vectorized form of age_to_bucket() for a whole array of ages at once.
    Scalar numpy indexing (ages[r, c]) in a Python per-cell loop is slow at
    scale (tested: ~17ms for 15,000 cells) -- this does it in one call."""
    import numpy as np
    t = np.clip(ages, 0, AGE_CAP) / AGE_CAP
    return np.round(t * (AGE_BUCKETS - 1)).astype(np.int32)


def pattern_index_for_lineage(lineage_id: int) -> int:
    return int(lineage_id) % NUM_PATTERNS


def pattern_index_array(lineage: "np.ndarray") -> "np.ndarray":
    """Vectorized form of pattern_index_for_lineage() for a whole array."""
    return lineage % NUM_PATTERNS


def _bucket_color(bucket: int) -> tuple[int, int, int]:
    t = bucket / (AGE_BUCKETS - 1)
    return tuple(int(COLOR_YOUNG[i] + (COLOR_OLD[i] - COLOR_YOUNG[i]) * t) for i in range(3))


def _shade(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def _draw_pattern(surface: pygame.Surface, size: int, pattern_idx: int, color: tuple[int, int, int]) -> None:
    dim = _shade(color, 0.45)

    if pattern_idx == 0:  # solid
        surface.fill(color)

    elif pattern_idx == 1:  # diagonal stripes, NW-SE
        surface.fill(dim)
        band = max(1, size // 3)
        for offset in range(-size, size, band * 2):
            pygame.draw.polygon(surface, color, [
                (offset, 0), (offset + band, 0), (offset + band + size, size), (offset + size, size),
            ])

    elif pattern_idx == 2:  # diagonal stripes, NE-SW
        surface.fill(dim)
        band = max(1, size // 3)
        for offset in range(0, size * 2, band * 2):
            pygame.draw.polygon(surface, color, [
                (offset, 0), (offset - band, 0), (offset - band - size, size), (offset - size, size),
            ])

    elif pattern_idx == 3:  # horizontal stripes
        surface.fill(dim)
        band = max(1, size // 3)
        for y in range(0, size, band * 2):
            pygame.draw.rect(surface, color, (0, y, size, band))

    elif pattern_idx == 4:  # vertical stripes
        surface.fill(dim)
        band = max(1, size // 3)
        for x in range(0, size, band * 2):
            pygame.draw.rect(surface, color, (x, 0, band, size))

    elif pattern_idx == 5:  # center dot
        surface.fill(dim)
        inset = max(1, size // 4)
        pygame.draw.rect(surface, color, (inset, inset, size - 2 * inset, size - 2 * inset))

    elif pattern_idx == 6:  # hollow ring / border
        surface.fill(dim)
        surface.fill(color, (0, 0, size, max(1, size // 4)))
        surface.fill(color, (0, size - max(1, size // 4), size, max(1, size // 4)))
        surface.fill(color, (0, 0, max(1, size // 4), size))
        surface.fill(color, (size - max(1, size // 4), 0, max(1, size // 4), size))

    else:  # pattern_idx == 7: cross / plus
        surface.fill(dim)
        band = max(1, size // 3)
        mid = (size - band) // 2
        pygame.draw.rect(surface, color, (mid, 0, band, size))
        pygame.draw.rect(surface, color, (0, mid, size, band))


class TileCache:
    """Caches rendered (age_bucket, pattern_idx) tiles for a given cell size.
    Call invalidate() whenever cell_size changes."""

    def __init__(self):
        self._cell_size = None
        self._tiles: dict[tuple[int, int], pygame.Surface] = {}

    def invalidate(self, cell_size: int) -> None:
        if cell_size != self._cell_size:
            self._cell_size = cell_size
            self._tiles.clear()

    def get(self, age_bucket: int, pattern_idx: int, color_by_age: bool, pattern_by_heredity: bool) -> pygame.Surface:
        effective_pattern = pattern_idx if (pattern_by_heredity and self._cell_size >= PATTERN_MIN_CELL_SIZE) else 0
        effective_bucket = age_bucket if color_by_age else AGE_BUCKETS - 1  # default: the standard "old" blue
        key = (effective_bucket, effective_pattern)
        tile = self._tiles.get(key)
        if tile is None:
            color = _bucket_color(effective_bucket)
            tile = pygame.Surface((self._cell_size, self._cell_size))
            _draw_pattern(tile, self._cell_size, effective_pattern, color)
            self._tiles[key] = tile
        return tile
