# src/Environment.py
# Manages the 2D toroidal grid and the positions of all data-point "items".
# The grid is the "ant world."  Each cell holds at most one item (or is empty).

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


class Environment:
    """
    Toroidal 2D grid of GRID_SIZE x GRID_SIZE cells.

    cell_to_item[y][x] -> item_id  or  -1  (empty)
    item_to_cell[item_id] -> (x, y)  or  None  (item is being carried)
    """

    def __init__(self, df):
        """
        Parameters
        ----------
        df : pd.DataFrame
            Output of DataPipeline.load_and_prepare().
            Must have columns: x, y, label, category.
        """
        self.gs = config.GRID_SIZE
        self.n_items = len(df)

        # Store feature vectors (the 2D PCA coords) as numpy for fast distance math
        self.features = df[["x", "y"]].values.astype(float)
        self.labels   = df["label"].values.astype(int)
        self.categories = df["category"].values

        # Grid: -1 means empty, otherwise stores the item_id
        self.grid = np.full((self.gs, self.gs), -1, dtype=int)

        # Reverse lookup: where is each item on the grid?
        # None means an ant is currently carrying it.
        self.item_positions = [None] * self.n_items  # list of (x, y) or None

        # Seed the grid: map PCA coords linearly onto [0, GRID_SIZE)
        self._seed_positions()

    def _seed_positions(self):
        """Map PCA (x, y) floating-point range → integer grid cells."""
        xs = self.features[:, 0]
        ys = self.features[:, 1]

        x_min, x_max = xs.min(), xs.max()
        y_min, y_max = ys.min(), ys.max()

        # Avoid division by zero if all values are identical
        x_range = x_max - x_min if x_max != x_min else 1.0
        y_range = y_max - y_min if y_max != y_min else 1.0

        for item_id in range(self.n_items):
            gx = int((xs[item_id] - x_min) / x_range * (self.gs - 1))
            gy = int((ys[item_id] - y_min) / y_range * (self.gs - 1))
            gx = gx % self.gs
            gy = gy % self.gs

            # If the target cell is already occupied, spiral outward to find a free cell
            gx, gy = self._find_free_cell(gx, gy)
            self._place(item_id, gx, gy)

    def _find_free_cell(self, gx, gy):
        """Spiral search for an empty cell starting from (gx, gy)."""
        if self.grid[gy][gx] == -1:
            return gx, gy
        for r in range(1, self.gs):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    nx = (gx + dx) % self.gs
                    ny = (gy + dy) % self.gs
                    if self.grid[ny][nx] == -1:
                        return nx, ny
        # Should never reach here unless grid is completely full
        raise RuntimeError("Grid is full — reduce N_SAMPLES or increase GRID_SIZE.")

    # ── Low-level grid ops ────────────────────────────────────────────────────

    def _place(self, item_id, gx, gy):
        self.grid[gy][gx] = item_id
        self.item_positions[item_id] = (gx, gy)

    def place_item(self, item_id, gx, gy):
        """Place item_id at toroidal position (gx, gy).  Caller must ensure the cell is free."""
        gx = gx % self.gs
        gy = gy % self.gs
        self._place(item_id, gx, gy)

    def remove_item(self, gx, gy):
        """Remove the item at (gx, gy) from the grid. Returns the item_id."""
        gx = gx % self.gs
        gy = gy % self.gs
        item_id = self.grid[gy][gx]
        if item_id == -1:
            raise ValueError(f"Cell ({gx},{gy}) is already empty.")
        self.grid[gy][gx] = -1
        self.item_positions[item_id] = None    # item is now "in the air"
        return item_id

    def is_occupied(self, gx, gy):
        return self.grid[gy % self.gs][gx % self.gs] != -1

    def item_at(self, gx, gy):
        """Returns item_id or -1."""
        return self.grid[gy % self.gs][gx % self.gs]

    # ── Neighbourhood queries ─────────────────────────────────────────────────

    def get_neighbourhood_items(self, gx, gy, r=None):
        """
        Return list of item_ids in the Moore neighbourhood of radius r around (gx, gy),
        excluding the center cell itself.
        """
        r = r if r is not None else config.NEIGHBORHOOD_R
        items = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (gx + dx) % self.gs
                ny = (gy + dy) % self.gs
                iid = self.grid[ny][nx]
                if iid != -1:
                    items.append(iid)
        return items

    def compute_local_density(self, gx, gy, r=None):
        """
        Returns f(i) — the average similarity of the neighbourhood around (gx, gy).
        This is called by ClusteringEngine but exposed here for convenience.
        """
        r = r if r is not None else config.NEIGHBORHOOD_R
        n_cells = (2 * r + 1) ** 2 - 1          # total neighbour cells
        items = self.get_neighbourhood_items(gx, gy, r)
        return len(items) / n_cells              # simple density [0, 1]

    # ── Utilities ─────────────────────────────────────────────────────────────

    def placed_items(self):
        """Generator yielding (item_id, gx, gy) for every item currently on the grid."""
        for item_id, pos in enumerate(self.item_positions):
            if pos is not None:
                yield item_id, pos[0], pos[1]

    def grid_entropy(self):
        """
        A simple proxy for 'disorder': fraction of occupied cells that are isolated
        (no neighbour within r=1).  Returns a value in [0, 1].
        High → items are scattered.  Low → items are clustered.
        """
        total = 0
        isolated = 0
        for item_id, gx, gy in self.placed_items():
            total += 1
            neighbours = self.get_neighbourhood_items(gx, gy, r=1)
            if len(neighbours) == 0:
                isolated += 1
        return isolated / total if total > 0 else 0.0
