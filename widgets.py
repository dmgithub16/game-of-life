"""
widgets.py -- Minimal, dependency-free pygame GUI widgets used by the
Game of Life control panel: Slider, Button, Toggle, and a compact
ToggleGrid for editing birth/survive neighbor-count rules.
"""

from __future__ import annotations

import pygame

FONT_NAME = None  # default pygame font


class Slider:
    """Horizontal slider with a label, live value readout, and drag handling."""

    def __init__(self, rect, label, min_val, max_val, value, step=1, fmt="{:.0f}", integer=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.step = step
        self.fmt = fmt
        self.integer = integer
        self.dragging = False
        self.track_rect = pygame.Rect(self.rect.x, self.rect.y + 30, self.rect.width, 8)
        self.font = pygame.font.Font(FONT_NAME, 16)
        self.small_font = pygame.font.Font(FONT_NAME, 14)

    def _value_to_x(self, value):
        frac = (value - self.min_val) / (self.max_val - self.min_val)
        return self.track_rect.x + int(frac * self.track_rect.width)

    def _x_to_value(self, x):
        frac = (x - self.track_rect.x) / self.track_rect.width
        frac = max(0.0, min(1.0, frac))
        raw = self.min_val + frac * (self.max_val - self.min_val)
        if self.integer:
            raw = round(raw / self.step) * self.step
        return max(self.min_val, min(self.max_val, raw))

    def handle_event(self, event) -> bool:
        """Returns True if the value changed this event."""
        handle_x = self._value_to_x(self.value)
        handle_rect = pygame.Rect(0, 0, 14, 20)
        handle_rect.center = (handle_x, self.track_rect.centery)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if handle_rect.collidepoint(event.pos) or self.track_rect.collidepoint(event.pos):
                self.dragging = True
                new_val = self._x_to_value(event.pos[0])
                if new_val != self.value:
                    self.value = new_val
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            new_val = self._x_to_value(event.pos[0])
            if new_val != self.value:
                self.value = new_val
                return True
        return False

    def draw(self, surface, accent):
        label_surf = self.font.render(self.label, True, (230, 230, 235))
        surface.blit(label_surf, (self.rect.x, self.rect.y))

        val_text = self.fmt.format(self.value)
        val_surf = self.small_font.render(val_text, True, (150, 200, 255))
        surface.blit(val_surf, (self.rect.right - val_surf.get_width(), self.rect.y + 2))

        pygame.draw.rect(surface, (60, 62, 70), self.track_rect, border_radius=4)
        filled_w = self._value_to_x(self.value) - self.track_rect.x
        if filled_w > 0:
            fill_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, filled_w, self.track_rect.height)
            pygame.draw.rect(surface, accent, fill_rect, border_radius=4)

        handle_x = self._value_to_x(self.value)
        pygame.draw.circle(surface, (240, 240, 245), (handle_x, self.track_rect.centery), 8)
        pygame.draw.circle(surface, accent, (handle_x, self.track_rect.centery), 8, 2)


class Button:
    """Clickable rectangular button with a text label."""

    def __init__(self, rect, label, color=(70, 130, 200), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.Font(FONT_NAME, 16)
        self.hovered = False

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        color = tuple(min(255, c + 25) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        text_surf = self.font.render(self.label, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Toggle:
    """Labeled on/off switch."""

    def __init__(self, rect, label, value=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.value = value
        self.font = pygame.font.Font(FONT_NAME, 16)
        self.switch_rect = pygame.Rect(self.rect.right - 46, self.rect.y, 46, 22)

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value
                return True
        return False

    def draw(self, surface, accent):
        label_surf = self.font.render(self.label, True, (230, 230, 235))
        surface.blit(label_surf, (self.rect.x, self.rect.y + 2))

        color = accent if self.value else (70, 72, 80)
        pygame.draw.rect(surface, color, self.switch_rect, border_radius=11)
        knob_x = self.switch_rect.right - 12 if self.value else self.switch_rect.x + 12
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, self.switch_rect.centery), 9)


class ToggleGrid:
    """A row of small numbered toggle buttons (used for Birth/Survive neighbor counts 0-8)."""

    def __init__(self, rect, label, values: set, count=9, accent=(90, 200, 120)):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.values = set(values)
        self.count = count
        self.accent = accent
        self.font = pygame.font.Font(FONT_NAME, 16)
        self.cell_font = pygame.font.Font(FONT_NAME, 14)
        self.cell_size = 24
        self.gap = 4
        self.cells = []
        for i in range(count):
            x = self.rect.x + i * (self.cell_size + self.gap)
            y = self.rect.y + 24
            self.cells.append(pygame.Rect(x, y, self.cell_size, self.cell_size))

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, cell_rect in enumerate(self.cells):
                if cell_rect.collidepoint(event.pos):
                    if i in self.values:
                        self.values.discard(i)
                    else:
                        self.values.add(i)
                    return True
        return False

    def draw(self, surface):
        label_surf = self.font.render(self.label, True, (230, 230, 235))
        surface.blit(label_surf, (self.rect.x, self.rect.y))
        for i, cell_rect in enumerate(self.cells):
            active = i in self.values
            color = self.accent if active else (55, 57, 64)
            pygame.draw.rect(surface, color, cell_rect, border_radius=4)
            text_color = (20, 20, 20) if active else (170, 170, 175)
            num_surf = self.cell_font.render(str(i), True, text_color)
            surface.blit(num_surf, num_surf.get_rect(center=cell_rect.center))
