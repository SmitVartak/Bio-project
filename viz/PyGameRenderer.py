# viz/PyGameRenderer.py
# Real-time "God View" Pygame window.
# Draws the grid with color-coded data points and ant positions.

try:
    import pygame
except ImportError:
    pygame = None

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

# ── Colour palette ────────────────────────────────────────────────────────────
COLOR_BG        = (10,  12,  20)    # near-black background
COLOR_GRID      = (25,  28,  40)    # subtle grid lines
COLOR_NORMAL    = (60, 220, 120)    # green  — benign traffic
COLOR_MALICIOUS = (220,  60,  80)   # red    — malicious traffic
COLOR_ANT_EMPTY = (200, 200, 255)   # light blue — unloaded ant
COLOR_ANT_FULL  = (255, 220,  50)   # yellow     — loaded ant
COLOR_HUD_TEXT  = (200, 210, 230)
COLOR_ENTROPY_BAR_BG  = (40,  44,  60)
COLOR_ENTROPY_BAR_FG  = (80, 180, 255)


class PyGameRenderer:
    """
    Handles all Pygame rendering.

    Call render(state) once per simulation yield to update the screen.
    Call should_quit() to check if the user closed the window.
    Call close() when done.
    """

    def __init__(self):
        if pygame is None:
            raise ImportError(
                "pygame is not installed for this Python version (3.14 has no wheel yet).\n"
                "Use --mode headless, --mode compare, or --mode ghost instead.\n"
                "To get the live window, run the project with Python 3.13 where pygame works."
            )
        pygame.init()
        pygame.display.set_caption("Swarm-Intelligent NIDS — Ant Colony Sorting")

        self.win_size  = config.WINDOW_SIZE
        self.gs        = config.GRID_SIZE
        self.cell_size = self.win_size / self.gs   # float pixels per cell

        self.screen = pygame.display.set_mode((self.win_size, self.win_size + 80))
        self.font_big   = pygame.font.SysFont("Consolas", 16, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 12)
        self.clock      = pygame.time.Clock()

        self._entropy_history = []   # for mini entropy bar chart

    # ── Public API ────────────────────────────────────────────────────────────

    def render(self, state: dict):
        """
        Render one frame.

        Parameters
        ----------
        state : dict with keys step, entropy, env, ants
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                sys.exit(0)

        self.screen.fill(COLOR_BG)
        self._draw_grid_lines()
        self._draw_items(state["env"])
        self._draw_ants(state["ants"])
        self._draw_hud(state)
        pygame.display.flip()
        self.clock.tick(config.FPS_CAP)

    def should_quit(self) -> bool:
        for event in pygame.event.get(pump=False):
            if event.type == pygame.QUIT:
                return True
        return False

    def close(self):
        pygame.quit()

    # ── Drawing helpers ───────────────────────────────────────────────────────

    def _cell_rect(self, gx, gy):
        """Return a pygame.Rect for grid cell (gx, gy)."""
        x = int(gx * self.cell_size)
        y = int(gy * self.cell_size)
        size = max(1, int(self.cell_size))
        return pygame.Rect(x, y, size, size)

    def _draw_grid_lines(self):
        """Draw faint grid lines every 10 cells."""
        for i in range(0, self.gs, 10):
            px = int(i * self.cell_size)
            pygame.draw.line(self.screen, COLOR_GRID,
                             (px, 0), (px, self.win_size))
            pygame.draw.line(self.screen, COLOR_GRID,
                             (0, px), (self.win_size, px))

    def _draw_items(self, env):
        """Draw each placed data point as a small colored circle."""
        radius = max(1, int(self.cell_size * 0.45))
        for item_id, gx, gy in env.placed_items():
            color = COLOR_MALICIOUS if env.labels[item_id] == 1 else COLOR_NORMAL
            cx = int(gx * self.cell_size + self.cell_size / 2)
            cy = int(gy * self.cell_size + self.cell_size / 2)
            pygame.draw.circle(self.screen, color, (cx, cy), radius)

    def _draw_ants(self, ants):
        """Draw each ant as a small triangle."""
        half = max(2, int(self.cell_size * 0.35))
        for ant in ants:
            color = COLOR_ANT_FULL if ant.loaded else COLOR_ANT_EMPTY
            cx = int(ant.x * self.cell_size + self.cell_size / 2)
            cy = int(ant.y * self.cell_size + self.cell_size / 2)
            points = [
                (cx,         cy - half),
                (cx - half,  cy + half),
                (cx + half,  cy + half),
            ]
            pygame.draw.polygon(self.screen, color, points)

    def _draw_hud(self, state):
        """Draw the info bar below the grid."""
        hud_y = self.win_size + 5
        step    = state["step"]
        entropy = state["entropy"]

        self._entropy_history.append(entropy)

        # Text labels
        step_surf = self.font_big.render(
            f"Step: {step:,}  |  Entropy: {entropy:.4f}  |  "
            f"Ants: {len(state['ants'])}  |  "
            f"Items on grid: {sum(1 for p in state['env'].item_positions if p is not None)}",
            True, COLOR_HUD_TEXT
        )
        self.screen.blit(step_surf, (8, hud_y))

        # Mini entropy bar (right side)
        bar_x  = 10
        bar_y  = hud_y + 22
        bar_w  = self.win_size - 20
        bar_h  = 20
        pygame.draw.rect(self.screen, COLOR_ENTROPY_BAR_BG,
                         (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * entropy)
        if fill_w > 0:
            pygame.draw.rect(self.screen, COLOR_ENTROPY_BAR_FG,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        label = self.font_small.render("Disorder", True, COLOR_HUD_TEXT)
        self.screen.blit(label, (bar_x + 4, bar_y + 3))
