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
  - Rule presets, chosen from a dropdown (Conway, HighLife, Day & Night, Seeds, ...)

The window is resizable -- the grid canvas fills the available space
and the control panel stays docked to the right edge.

Controls:
  Left click on the grid  -> toggle a cell (works while paused or running)
  Left-click drag on grid -> paint multiple cells
  Space                   -> play / pause
  S                       -> single step (while paused)
  R                       -> randomize
  C                       -> clear
  Ctrl+S                  -> save pattern to a .json file (native dialog)
  Ctrl+O                  -> load pattern from a .json file (native dialog)
  Esc / close window      -> quit

Run:
    python3 game_of_life.py
"""

from __future__ import annotations

import json
import sys

import pygame

from life import LifeGrid, RULE_PRESETS
from widgets import Slider, Button, Toggle, ToggleGrid, Dropdown

# ----------------------------------------------------------------------
# Layout constants
# ----------------------------------------------------------------------
PANEL_W = 340
INITIAL_GRID_AREA_W = 700
INITIAL_GRID_AREA_H = 700
INITIAL_WINDOW_W = INITIAL_GRID_AREA_W + PANEL_W
INITIAL_WINDOW_H = INITIAL_GRID_AREA_H

MIN_WINDOW_W = PANEL_W + 260
MIN_WINDOW_H = 640

BG_COLOR = (18, 18, 22)
PANEL_COLOR = (28, 29, 35)
GRID_BG = (10, 10, 13)
CELL_COLOR = (90, 200, 255)
GRID_LINE_COLOR = (35, 36, 42)
ACCENT = (90, 170, 255)
ACCENT_GREEN = (90, 210, 140)

MIN_CELL_SIZE = 4
MAX_CELL_SIZE = 25
DEFAULT_CELL_SIZE = 10

PRESET_NAMES = list(RULE_PRESETS.keys())


class GameOfLifeApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Conway's Game of Life")
        self.window_w = INITIAL_WINDOW_W
        self.window_h = INITIAL_WINDOW_H
        self.screen = pygame.display.set_mode((self.window_w, self.window_h), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.grid_area_w = self.window_w - PANEL_W
        self.grid_area_h = self.window_h

        self.cell_size = DEFAULT_CELL_SIZE
        rows = self.grid_area_h // self.cell_size
        cols = self.grid_area_w // self.cell_size

        birth, survive = RULE_PRESETS[PRESET_NAMES[0]]
        self.grid = LifeGrid(rows, cols, wrap=True, birth=birth, survive=survive)
        self.grid.randomize(0.25)

        self.running_sim = False
        self.mouse_painting = False
        self.paint_value = 1
        self.time_accumulator = 0.0
        self.status_message = ""
        self.status_timer = 0.0

        # Hidden tkinter root for native save/load file dialogs.
        self._tk_root = None

        self._build_panel()

    # ------------------------------------------------------------------
    # Panel construction / live relayout on resize
    # ------------------------------------------------------------------
    def _build_panel(self):
        """Create all panel widgets once (values persist across later relayouts)."""
        px = self.grid_area_w + 20
        y = 20
        gap = 46
        w = PANEL_W - 40

        self.speed_slider = Slider((px, y, w, 0), "Speed (gen/sec)", 1, 60, 8, step=1)
        y += gap
        self.density_slider = Slider((px, y, w, 0), "Randomize density (%)", 1, 90, 25, step=1)
        y += gap
        self.cellsize_slider = Slider(
            (px, y, w, 0), "Cell size (px)", MIN_CELL_SIZE, MAX_CELL_SIZE, DEFAULT_CELL_SIZE, step=1
        )
        y += gap + 10

        self.wrap_toggle = Toggle((px, y, w, 22), "Wrap-around edges", True)
        y += 34
        self.gridlines_toggle = Toggle((px, y, w, 22), "Show grid lines", True)
        y += 44

        self.birth_grid = ToggleGrid((px, y, 0, 0), "Birth (B) -- neighbor counts", {3}, accent=ACCENT_GREEN)
        y += 56
        self.survive_grid = ToggleGrid((px, y, 0, 0), "Survive (S) -- neighbor counts", {2, 3}, accent=ACCENT)
        y += 66

        self.preset_dropdown = Dropdown((px, y, w, 0), "Rule preset", PRESET_NAMES, selected_index=0)
        y += 56

        self.play_button = Button((px, y, w, 40), "Play (Space)", color=(60, 160, 100))
        y += 50
        btn_w = (w - 10) // 2
        self.step_button = Button((px, y, btn_w, 36), "Step (S)", color=(80, 100, 160))
        self.reset_button = Button((px + btn_w + 10, y, btn_w, 36), "Reset gen #", color=(90, 90, 100))
        y += 46
        self.randomize_button = Button((px, y, btn_w, 36), "Randomize (R)", color=(150, 120, 60))
        self.clear_button = Button((px + btn_w + 10, y, btn_w, 36), "Clear (C)", color=(160, 70, 70))
        y += 46
        self.save_button = Button((px, y, btn_w, 36), "Save (Ctrl+S)", color=(60, 110, 150))
        self.load_button = Button((px + btn_w + 10, y, btn_w, 36), "Load (Ctrl+O)", color=(60, 110, 150))
        y += 50

        self.stats_y = y + 10
        self.font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 22)

        self._all_widgets_ordered = [
            self.speed_slider, self.density_slider, self.cellsize_slider,
            self.wrap_toggle, self.gridlines_toggle,
            self.birth_grid, self.survive_grid,
            self.preset_dropdown,
            self.play_button, self.step_button, self.reset_button,
            self.randomize_button, self.clear_button,
            self.save_button, self.load_button,
        ]

    def _relayout_panel(self):
        """Reposition existing widgets (preserving their values) after a resize."""
        px = self.grid_area_w + 20
        y = 20
        gap = 46
        w = PANEL_W - 40
        btn_w = (w - 10) // 2

        self.speed_slider.set_pos(px, y); y += gap
        self.density_slider.set_pos(px, y); y += gap
        self.cellsize_slider.set_pos(px, y); y += gap + 10

        self.wrap_toggle.set_pos(px, y); y += 34
        self.gridlines_toggle.set_pos(px, y); y += 44

        self.birth_grid.set_pos(px, y); y += 56
        self.survive_grid.set_pos(px, y); y += 66

        self.preset_dropdown.set_pos(px, y); y += 56

        self.play_button.set_pos(px, y); y += 50
        self.step_button.set_pos(px, y)
        self.reset_button.set_pos(px + btn_w + 10, y); y += 46
        self.randomize_button.set_pos(px, y)
        self.clear_button.set_pos(px + btn_w + 10, y); y += 46
        self.save_button.set_pos(px, y)
        self.load_button.set_pos(px + btn_w + 10, y); y += 50

        self.stats_y = y + 10

    # ------------------------------------------------------------------
    # Resize handling
    # ------------------------------------------------------------------
    def _handle_resize(self, new_w, new_h):
        new_w = max(new_w, MIN_WINDOW_W)
        new_h = max(new_h, MIN_WINDOW_H)
        self.window_w, self.window_h = new_w, new_h
        self.screen = pygame.display.set_mode((self.window_w, self.window_h), pygame.RESIZABLE)

        self.grid_area_w = self.window_w - PANEL_W
        self.grid_area_h = self.window_h

        rows = max(1, self.grid_area_h // self.cell_size)
        cols = max(1, self.grid_area_w // self.cell_size)
        self.grid.resize(rows, cols)

        self._relayout_panel()

    # ------------------------------------------------------------------
    # Grid rebuild when cell size changes
    # ------------------------------------------------------------------
    def _apply_cell_size(self, new_size: int):
        if new_size == self.cell_size:
            return
        self.cell_size = new_size
        rows = max(1, self.grid_area_h // self.cell_size)
        cols = max(1, self.grid_area_w // self.cell_size)
        self.grid.resize(rows, cols)

    def _screen_to_cell(self, pos):
        x, y = pos
        if x >= self.grid_area_w or y >= self.grid_area_h:
            return None
        col = x // self.cell_size
        row = y // self.cell_size
        return row, col

    # ------------------------------------------------------------------
    # Save / load (native file dialogs via a hidden tkinter root)
    # ------------------------------------------------------------------
    def _get_tk_root(self):
        if self._tk_root is None:
            import tkinter as tk
            self._tk_root = tk.Tk()
            self._tk_root.withdraw()
            self._tk_root.attributes("-topmost", True)
        return self._tk_root

    def _set_status(self, message: str, seconds: float = 3.0):
        self.status_message = message
        self.status_timer = seconds

    def save_pattern(self):
        try:
            from tkinter import filedialog
            root = self._get_tk_root()
            path = filedialog.asksaveasfilename(
                parent=root,
                title="Save Game of Life pattern",
                defaultextension=".json",
                filetypes=[("Game of Life pattern", "*.json"), ("All files", "*.*")],
            )
            if not path:
                return
            data = self.grid.to_dict()
            data["cell_size"] = self.cell_size
            with open(path, "w") as f:
                json.dump(data, f)
            self._set_status(f"Saved: {path.split('/')[-1].split(chr(92))[-1]}")
        except Exception as exc:  # noqa: BLE001 -- surface any dialog/IO error to the user, don't crash the app
            self._set_status(f"Save failed: {exc}", seconds=5.0)

    def load_pattern(self):
        try:
            from tkinter import filedialog
            root = self._get_tk_root()
            path = filedialog.askopenfilename(
                parent=root,
                title="Load Game of Life pattern",
                filetypes=[("Game of Life pattern", "*.json"), ("All files", "*.*")],
            )
            if not path:
                return
            with open(path) as f:
                data = json.load(f)
            self.grid = LifeGrid.from_dict(data)
            self.grid_area_w_needed = self.grid.cols  # informational only
            if "cell_size" in data:
                self.cell_size = max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, int(data["cell_size"])))
                self.cellsize_slider.value = self.cell_size
            self.wrap_toggle.value = self.grid.wrap
            self.birth_grid.values = set(self.grid.birth)
            self.survive_grid.values = set(self.grid.survive)
            self.running_sim = False
            self._set_status(f"Loaded: {path.split('/')[-1].split(chr(92))[-1]}")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Load failed: {exc}", seconds=5.0)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self._quit()

        if event.type == pygame.VIDEORESIZE:
            self._handle_resize(event.w, event.h)
            return  # widget rects just moved; skip further hit-testing this event

        if event.type == pygame.KEYDOWN:
            ctrl = bool(event.mod & pygame.KMOD_CTRL)
            if event.key == pygame.K_ESCAPE:
                self._quit()
            elif ctrl and event.key == pygame.K_s:
                self.save_pattern()
            elif ctrl and event.key == pygame.K_o:
                self.load_pattern()
            elif event.key == pygame.K_SPACE:
                self.running_sim = not self.running_sim
            elif event.key == pygame.K_s and not self.running_sim:
                self.grid.step()
            elif event.key == pygame.K_r:
                self.grid.randomize(self.density_slider.value / 100.0)
            elif event.key == pygame.K_c:
                self.grid.clear()

        # If the preset dropdown is open, it should eat clicks before grid/paint logic.
        dropdown_was_open = self.preset_dropdown.open

        # Grid click / paint (only if not interacting with an open dropdown)
        if not dropdown_was_open:
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

        if self.preset_dropdown.handle_event(event):
            name = self.preset_dropdown.selected
            birth, survive = RULE_PRESETS[name]
            self.grid.birth = set(birth)
            self.grid.survive = set(survive)
            self.birth_grid.values = set(birth)
            self.survive_grid.values = set(survive)

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
        if self.save_button.handle_event(event):
            self.save_pattern()
        if self.load_button.handle_event(event):
            self.load_pattern()

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
        if self.status_timer > 0:
            self.status_timer -= dt

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        self.screen.fill(BG_COLOR)

        # Grid area (clipped so cells/gridlines from a loaded pattern larger
        # than the current canvas never spill into the panel)
        grid_surf_rect = pygame.Rect(0, 0, self.grid_area_w, self.grid_area_h)
        pygame.draw.rect(self.screen, GRID_BG, grid_surf_rect)

        self.screen.set_clip(grid_surf_rect)
        cs = self.cell_size
        alive_coords = self.grid.cells.nonzero()
        for r, c in zip(*alive_coords):
            rect = pygame.Rect(int(c) * cs, int(r) * cs, cs, cs)
            self.screen.fill(CELL_COLOR, rect)

        if self.gridlines_toggle.value and cs >= 4:
            for x in range(0, self.grid_area_w, cs):
                pygame.draw.line(self.screen, GRID_LINE_COLOR, (x, 0), (x, self.grid_area_h))
            for y in range(0, self.grid_area_h, cs):
                pygame.draw.line(self.screen, GRID_LINE_COLOR, (0, y), (self.grid_area_w, y))
        self.screen.set_clip(None)

        pygame.draw.rect(self.screen, (60, 60, 70), grid_surf_rect, 2)

        # Panel
        panel_rect = pygame.Rect(self.grid_area_w, 0, PANEL_W, self.window_h)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)

        self.speed_slider.draw(self.screen, ACCENT)
        self.density_slider.draw(self.screen, ACCENT)
        self.cellsize_slider.draw(self.screen, ACCENT)
        self.wrap_toggle.draw(self.screen, ACCENT)
        self.gridlines_toggle.draw(self.screen, ACCENT)
        self.birth_grid.draw(self.screen)
        self.survive_grid.draw(self.screen)
        self.preset_dropdown.draw(self.screen)

        self.play_button.label = "Pause (Space)" if self.running_sim else "Play (Space)"
        self.play_button.color = (200, 100, 70) if self.running_sim else (60, 160, 100)
        self.play_button.draw(self.screen)
        self.step_button.draw(self.screen)
        self.reset_button.draw(self.screen)
        self.randomize_button.draw(self.screen)
        self.clear_button.draw(self.screen)
        self.save_button.draw(self.screen)
        self.load_button.draw(self.screen)

        # Stats
        stats_x = self.grid_area_w + 20
        gen_text = self.title_font.render(f"Generation: {self.grid.generation}", True, (240, 240, 245))
        pop_text = self.font.render(
            f"Population: {self.grid.population()} / {self.grid.rows * self.grid.cols}", True, (180, 200, 220)
        )
        dims_text = self.font.render(f"Grid: {self.grid.cols} x {self.grid.rows}", True, (150, 150, 160))
        self.screen.blit(gen_text, (stats_x, self.stats_y))
        self.screen.blit(pop_text, (stats_x, self.stats_y + 26))
        self.screen.blit(dims_text, (stats_x, self.stats_y + 46))

        if self.status_timer > 0 and self.status_message:
            status_surf = self.font.render(self.status_message, True, (150, 230, 180))
            self.screen.blit(status_surf, (stats_x, self.stats_y + 70))

        # Dropdown overlay drawn LAST so it layers above every other panel widget.
        self.preset_dropdown.draw_open_overlay(self.screen)

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
