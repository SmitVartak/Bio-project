# src/Ant.py
# Defines a single ant agent.  The ant has a simple state machine:
#   UNLOADED → wanders, may pick up an item
#   LOADED   → wanders while carrying one item, may drop it

import random
from collections import deque
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

# Movement deltas for the 4-connected grid (no diagonals → simpler, still effective)
_MOVES = [(1, 0), (-1, 0), (0, 1), (0, -1)]


class Ant:
    """
    A single foraging ant.

    Attributes
    ----------
    x, y        : int   Current position on the grid (toroidal).
    loaded      : bool  True if the ant is carrying an item.
    carried_id  : int   item_id of the carried data point, or -1 if unloaded.
    memory      : deque Short-term memory of recently dropped item_ids.
                        An ant will NOT pick up an item that is in its memory,
                        preventing the "flicker" problem (pick–drop–pick–drop...).
    """

    def __init__(self, ant_id: int, grid_size: int):
        self.ant_id     = ant_id
        self.gs         = grid_size
        self.x          = random.randint(0, grid_size - 1)
        self.y          = random.randint(0, grid_size - 1)
        self.loaded     = False
        self.carried_id = -1
        self.memory     = deque(maxlen=config.MEMORY_SIZE)

    # ── Movement ──────────────────────────────────────────────────────────────

    def move(self):
        """Take one random step on the toroidal grid."""
        dx, dy = random.choice(_MOVES)
        self.x = (self.x + dx) % self.gs
        self.y = (self.y + dy) % self.gs

    # ── State transitions ─────────────────────────────────────────────────────

    def pick_up(self, item_id: int):
        """
        Pick up item_id from the current cell.
        The caller (Simulation) is responsible for removing it from the grid.
        """
        self.loaded     = True
        self.carried_id = item_id

    def drop(self):
        """
        Drop the carried item at the current cell.
        The caller (Simulation) is responsible for placing it on the grid.
        Returns the item_id that was dropped.
        """
        dropped_id      = self.carried_id
        self.loaded     = False
        self.carried_id = -1
        # Remember what we just dropped so we don't instantly pick it up again
        self.memory.append(dropped_id)
        return dropped_id

    # ── Memory query ──────────────────────────────────────────────────────────

    def can_pick(self, item_id: int) -> bool:
        """Returns True if the ant is allowed to pick up this item_id."""
        return item_id not in self.memory
