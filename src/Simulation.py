# src/Simulation.py
# Ties together Environment, Ants, and ClusteringEngine into the main loop.
# Yields simulation state snapshots so the renderer can draw each frame.

import numpy as np
import random
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from src.Environment     import Environment
from src.Ant             import Ant
from src.ClusteringEngine import ClusteringEngine


class Simulation:
    """
    Encapsulates one full run of the ant-colony sorting algorithm.

    Usage (headless)
    ----------------
    sim = Simulation(df)
    for state in sim.run():
        # state is a dict with keys: step, entropy, env, ants
        pass

    Usage (with renderer)
    ---------------------
    sim = Simulation(df)
    renderer = PyGameRenderer(sim.env)
    for state in sim.run():
        renderer.render(state)
        if renderer.should_quit():
            break
    """

    def __init__(self, df):
        self.df          = df
        self.env         = Environment(df)
        self.ants        = [Ant(i, config.GRID_SIZE) for i in range(config.N_ANTS)]
        self.engine      = ClusteringEngine()
        self.step        = 0
        self.entropy_log = []    # list of (step, entropy) tuples
        self._start_time = None

    def run(self):
        """
        Generator that runs the simulation step by step.
        Yields a state dict every ENTROPY_INTERVAL steps.
        """
        self._start_time = time.time()
        print(f"[Simulation] Starting — {config.MAX_STEPS:,} steps, "
              f"{config.N_ANTS} ants, grid {config.GRID_SIZE}x{config.GRID_SIZE}")

        for step in range(1, config.MAX_STEPS + 1):
            self.step = step
            self._tick()

            if step % config.ENTROPY_INTERVAL == 0:
                entropy = self.env.grid_entropy()
                self.entropy_log.append((step, entropy))
                elapsed = time.time() - self._start_time
                print(f"  step={step:>8,}  entropy={entropy:.4f}  "
                      f"elapsed={elapsed:.1f}s", end="\r")
                yield {
                    "step":    step,
                    "entropy": entropy,
                    "env":     self.env,
                    "ants":    self.ants,
                }

        elapsed = time.time() - self._start_time
        print(f"\n[Simulation] Done in {elapsed:.1f}s")

    def _tick(self):
        """Process one step for every ant."""
        for ant in self.ants:
            ant.move()
            gx, gy = ant.x, ant.y

            if ant.loaded:
                # The ant is carrying an item — try to drop it
                if not self.env.is_occupied(gx, gy):
                    if ClusteringEngine.should_drop(ant.carried_id, gx, gy, self.env):
                        dropped_id = ant.drop()
                        self.env.place_item(dropped_id, gx, gy)

            else:
                # The ant is free — try to pick up the item under its feet
                item_id = self.env.item_at(gx, gy)
                if item_id != -1 and ant.can_pick(item_id):
                    if ClusteringEngine.should_pickup(item_id, gx, gy, self.env):
                        self.env.remove_item(gx, gy)
                        ant.pick_up(item_id)

    # ── Convenience helpers used by analysis scripts ──────────────────────────

    def get_cluster_assignments(self):
        """
        After the simulation, return an array of shape (n_items,) where each
        entry is the final grid cell index (gy * GRID_SIZE + gx) for placed items,
        or -1 for items currently being carried (should be 0 at rest).
        """
        assignments = np.full(self.env.n_items, -1, dtype=int)
        for item_id, pos in enumerate(self.env.item_positions):
            if pos is not None:
                gx, gy = pos
                assignments[item_id] = gy * config.GRID_SIZE + gx
        return assignments

    def inject_item(self, feature_vector, label=1, category="Injected"):
        """
        Add a single new data point to the environment mid-simulation.
        Used by the Ghost Detector.  Returns the new item_id.
        """
        import pandas as pd
        new_row = pd.DataFrame({
            "x": [feature_vector[0]],
            "y": [feature_vector[1]],
            "label":    [label],
            "category": [category],
        })

        new_id = self.env.n_items

        # Extend environment storage
        self.env.features   = np.vstack([self.env.features, feature_vector[:2]])
        self.env.labels     = np.append(self.env.labels, label)
        self.env.categories = np.append(self.env.categories, category)
        self.env.item_positions.append(None)
        self.env.n_items += 1

        # Place at a random empty cell
        for _ in range(1000):
            gx = random.randint(0, config.GRID_SIZE - 1)
            gy = random.randint(0, config.GRID_SIZE - 1)
            if not self.env.is_occupied(gx, gy):
                self.env.place_item(new_id, gx, gy)
                return new_id

        raise RuntimeError("Could not find a free cell to inject the ghost packet.")

    def run_n_steps(self, n: int):
        """Run exactly n steps without yielding — used after ghost injection."""
        for _ in range(n):
            self._tick()
