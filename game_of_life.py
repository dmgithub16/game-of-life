#!/usr/bin/env python3
"""
Conway's Game of Life -- interactive pygame implementation.

Every meaningful variable of the simulation is exposed as a live GUI
control in the side panel:
  - Simulation speed (generations/second)
  - Random-fill density
  - Cell size (grid resolution)
  - Edge behaviour: toroidal wrap-around vs. dead (bounded) border
  - Grid-line visibility
  - Birth rule (which live-neighbor counts create a new cell)
  - Survive rule (which live-neighbor counts keep a cell alive)
  - Rule presets (Conway, HighLife, Day & Night, Seeds, ...)

Controls:
  Left click on the grid  -> toggle a cell (works while paused or running)
  Left-click drag on grid -> paint multiple cells
  Space                   -> play / pause
  S                       -> single step (while paused)
  R                       -> randomize
  C                       -> clear
  Esc / close window      -> quit

Run:
    python3 game_of_life.py
"""

from __future__ import annotations

import sys

import pygame

from life import LifeGrid, RULE_PRESETS
from widgets import Slider, Button, Toggle, ToggleGrid

# ----------------------------------------------------------------------
# Layout constants
# ----------------------------------------------------------------------
GRID_AREA_W = 700
GRID_AREA_H = 700
PANEL_W = 340
WINDOW_W = GRID_AREA_W + PANEL_W
WINDOW_H = GRID_AREA_H

BG_COLOR = (18, 18, 22)
PANEL_COLOR = (28, 29, 35)
GRID_BG = (10, 10, 13)
CELL_COLOR = (90, 200, 255)
GRID_LINE_COLOR = (35, 36, 42)
ACCENT = (90, 170, 255)
ACCENT_GREEN = (90, 210, 140)
ACCENT_RED = (230, 100, 100)

MIN_CELL_SIZE = 4
MAX_CELL_SIZE = 25
DEFAULT_CELL_SIZE = 10


class GameOfLifeApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Conway's Game of Life")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()

        self.cell_size = DEFAULT_CELL_SIZE
        rows = GRID_AREA_H // self.cell_size
        cols = GRID_AREA_W // self.cell_size

        birth, survive = RULE_PRESETS["Conway's Life (B3/S23)"]
        self.grid = LifeGrid(rows, cols, wrap=True, birth=birth, survive=survive)
        self.grid.randomize(0.25)

        self.running_sim = False
        self.mouse_painting = False
        self.paint_value = 1
        self.time_accumulator = 0.0

        self._build_panel()

    # ------------------------------------------------------------------
    # Panel construction
    # ------------------------------------------------------------------
    def _build_panel(self):
        px = GRID_AREA_W + 20
        y = 20
        gap = 46

        self.speed_slider = Slider((px, y, PANEL_W - 40, 0), "Speed (gen/sec)", 1, 60, 8, step=1)
        y += gap
        self.density_slider = Slider(
            (px, y, PANEL_W - 40, 0), "Randomize density (%)", 1, 90, 25, step=1
        )
        y += gap
        self.cellsize_slider = Slider(
            (px, y, PANEL_W - 40, 0), "Cell size (px)", MIN_CELL_SIZE, MAX_CELL_SIZE, DEFAULT_CELL_SIZE, step=1
        )
        y += gap + 10

        self.wrap_toggle = Toggle((px, y, PANEL_W - 40, 22), "Wrap-around edges", True)
        y += 34
        self.gridlines_toggle = Toggle((px, y, PANEL_W - 40, 22), "Show grid lines", True)
        y += 44

        self.birth_grid = ToggleGrid((px, y, 0, 0), "Birth (B) -- neighbor counts", {3}, accent=ACCENT_GREEN)
        y += 56
        self.survive_grid = ToggleGrid((px, y, 0, 0), "Survive (S) -- neighbor counts", {2, 3}, accent=ACCENT)
        y += 66

        btn_w = (PANEL_W - 40 - 10) // 2
        self.play_button = Button((px, y, PANEL_W - 40, 40), "Play (Space)", color=(60, 160, 100))
        y += 50
        self.step_button = Button((px, y, btn_w, 36), "Step (S)", color=(80, 100, 160))
        self.reset_button = Button((px + btn_w + 10, y, btn_w, 36), "Reset gen #", color=(90, 90, 100))
        y += 46
        self.randomize_button = Button((px, y, btn_w, 36), "Randomize (R)", color=(150, 120, 60))
        self.clear_button = Button((px + btn_w + 10, y, btn_w, 36), "Clear (C)", color=(160, 70, 70))
        y += 50

        # Rule preset buttons, stacked
        self.preset_buttons = []
        for name in RULE_PRESETS:
            self.preset_buttons.append((Button((px, y, PANEL_W - 40, 30), name, color=(50, 52, 60)), name))
            y += 36

        self.stats_y = y + 10
        self.font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 22)

    # ------------------------------------------------------------------
    # Grid rebuild when cell size changes
    # ------------------------------------------------------------------
    def _apply_cell_size(self, new_size: int):
        if new_size == self.cell_size:
            return
        self.cell_size = new_size
        rows = GRID_AREA_H // self.cell_size
        cols = GRID_AREA_W // self.cell_size
        self.grid.resize(rows, cols)

    def _screen_to_cell(self, pos):
        x, y = pos
        if x >= GRID_AREA_W:
            return None
        col = x // self.cell_size
        row = y // self.cell_size
        return row, col

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self._quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._quit()
            elif event.key == pygame.K_SPACE:
                self.running_sim = not self.running_sim
            elif event.key == pygame.K_s and not self.running_sim:
                self.grid.step()
            elif event.key == pygame.K_r:
                self.grid.randomize(self.density_slider.value / 100.0)
            elif event.key == pygame.K_c:
                self.grid.clear()

        # Grid click / paint
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cell = self._screen_to_cell(event.pos)
            if cell is not None:
                row, col = cell
                self.paint_value = 0 if self.grid.cells[row, col] else 1
                self.grid.toggle_cell(row, col)
                self.mouse_painting = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_painting = False
        elif event.type == pygame.MOUSEMOTION and self.mouse_painting:
            cell = self._screen_to_cell(event.pos)
            if cell is not None:
                row, col = cell
                self.grid.set_cell(row, col, self.paint_value)

        # Panel widgets
        self.speed_slider.handle_event(event)
        self.density_slider.handle_event(event)
        if self.cellsize_slider.handle_event(event):
            self._apply_cell_size(int(self.cellsize_slider.value))
        self.wrap_toggle.handle_event(event)
        self.gridlines_toggle.handle_event(event)

        if self.birth_grid.handle_event(event):
            self.grid.birth = set(self.birth_grid.values)
        if self.survive_grid.handle_event(event):
            self.grid.survive = set(self.survive_grid.values)

        if self.play_button.handle_event(event):
            self.running_sim = not self.running_sim
        if self.step_button.handle_event(event):
            self.grid.step()
        if self.reset_button.handle_event(event):
            self.grid.generation = 0
        if self.randomize_button.handle_event(event):
            self.grid.randomize(self.density_slider.value / 100.0)
        if self.clear_button.handle_event(event):
            self.grid.clear()

        for button, name in self.preset_buttons:
            if button.handle_event(event):
                birth, survive = RULE_PRESETS[name]
                self.grid.birth = set(birth)
                self.grid.survive = set(survive)
                self.birth_grid.values = set(birth)
                self.survive_grid.values = set(survive)

    def _quit(self):
        pygame.quit()
        sys.exit(0)

    # ------------------------------------------------------------------
    # Update / simulation timing
    # ------------------------------------------------------------------
    def update(self, dt: float):
        self.grid.wrap = self.wrap_toggle.value
        if self.running_sim:
            self.time_accumulator += dt
            step_interval = 1.0 / max(1, self.speed_slider.value)
            while self.time_accumulator >= step_interval:
                self.grid.step()
                self.time_accumulator -= step_interval

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        self.screen.fill(BG_COLOR)

        # Grid area
        grid_surf_rect = pygame.Rect(0, 0, GRID_AREA_W, GRID_AREA_H)
        pygame.draw.rect(self.screen, GRID_BG, grid_surf_rect)

        cs = self.cell_size
        alive_coords = self.grid.cells.nonzero()
        for r, c in zip(*alive_coords):
            rect = pygame.Rect(int(c) * cs, int(r) * cs, cs, cs)
            pygame.draw.rect(self.screen, CELL_COLOR, rect)

        if self.gridlines_toggle.value and cs >= 4:
            for x in range(0, GRID_AREA_W, cs):
                pygame.draw.line(self.screen, GRID_LINE_COLOR, (x, 0), (x, GRID_AREA_H))
            for y in range(0, GRID_AREA_H, cs):
                pygame.draw.line(self.screen, GRID_LINE_COLOR, (0, y), (GRID_AREA_W, y))

        pygame.draw.rect(self.screen, (60, 60, 70), grid_surf_rect, 2)

        # Panel
        panel_rect = pygame.Rect(GRID_AREA_W, 0, PANEL_W, WINDOW_H)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)

        self.speed_slider.draw(self.screen, ACCENT)
        self.density_slider.draw(self.screen, ACCENT)
        self.cellsize_slider.draw(self.screen, ACCENT)
        self.wrap_toggle.draw(self.screen, ACCENT)
        self.gridlines_toggle.draw(self.screen, ACCENT)
        self.birth_grid.draw(self.screen)
        self.survive_grid.draw(self.screen)

        self.play_button.label = "Pause (Space)" if self.running_sim else "Play (Space)"
        self.play_button.color = (200, 100, 70) if self.running_sim else (60, 160, 100)
        self.play_button.draw(self.screen)
        self.step_button.draw(self.screen)
        self.reset_button.draw(self.screen)
        self.randomize_button.draw(self.screen)
        self.clear_button.draw(self.screen)

        preset_label = self.font.render("Rule presets:", True, (180, 180, 190))
        self.screen.blit(preset_label, (self.preset_buttons[0][0].rect.x, self.preset_buttons[0][0].rect.y - 20))
        for button, _ in self.preset_buttons:
            button.draw(self.screen)

        # Stats
        stats_x = GRID_AREA_W + 20
        gen_text = self.title_font.render(f"Generation: {self.grid.generation}", True, (240, 240, 245))
        pop_text = self.font.render(
            f"Population: {self.grid.population()} / {self.grid.rows * self.grid.cols}", True, (180, 200, 220)
        )
        dims_text = self.font.render(f"Grid: {self.grid.cols} x {self.grid.rows}", True, (150, 150, 160))
        self.screen.blit(gen_text, (stats_x, self.stats_y))
        self.screen.blit(pop_text, (stats_x, self.stats_y + 26))
        self.screen.blit(dims_text, (stats_x, self.stats_y + 46))

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


def main():
    app = GameOfLifeApp()
    app.run()


if __name__ == "__main__":
    main()
