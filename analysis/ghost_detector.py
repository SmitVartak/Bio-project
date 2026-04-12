# analysis/ghost_detector.py
# The "Zero-Day Detection" demo.
# Injects a synthetic unseen packet into the settled grid and tracks
# which cluster the ants push it toward.

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# These PCA-space coordinates approximate known attack profiles
# after dimensionality reduction.  The exact values depend on your data;
# these are overridden at runtime by the CLI in main.py if --ghost-coords is passed.
GHOST_PROFILES = {
    "DoS":    np.array([ 2.5,  1.0]),
    "Botnet": np.array([-1.5,  2.8]),
    "Recon":  np.array([ 0.5, -2.0]),
    "Normal": np.array([-0.5, -0.5]),
}


def run_ghost_detection(sim, ghost_name: str = "DoS",
                        extra_steps: int = 50_000):
    """
    Inject a synthetic 'ghost' packet into a settled simulation,
    let the ants sort it for extra_steps, then report which cluster
    it ended up in and identify the nearest cluster centroid.

    Parameters
    ----------
    sim         : Simulation  (already run to convergence)
    ghost_name  : str         Key from GHOST_PROFILES
    extra_steps : int         How many more steps to run after injection

    Returns
    -------
    result : dict with keys: ghost_id, final_pos, nearest_label, nearest_category
    """
    ghost_vec = GHOST_PROFILES.get(ghost_name, GHOST_PROFILES["DoS"])
    print(f"\n[GhostDetector] Injecting '{ghost_name}' packet at PCA coords {ghost_vec}")

    ghost_id = sim.inject_item(ghost_vec, label=1, category=f"Ghost-{ghost_name}")
    print(f"[GhostDetector] Ghost assigned item_id={ghost_id}")
    print(f"[GhostDetector] Running {extra_steps:,} extra steps ...")

    sim.run_n_steps(extra_steps)

    final_pos = sim.env.item_positions[ghost_id]
    if final_pos is None:
        print("[GhostDetector] Ghost is still being carried by an ant — run more steps.")
        return {"ghost_id": ghost_id, "final_pos": None,
                "nearest_label": "Unknown", "nearest_category": "Unknown"}

    gx, gy = final_pos
    print(f"[GhostDetector] Ghost settled at grid position ({gx}, {gy})")

    # Find the nearest cluster by looking at the surrounding items
    neighbours = sim.env.get_neighbourhood_items(gx, gy, r=3)
    if not neighbours:
        # Expand search radius
        neighbours = sim.env.get_neighbourhood_items(gx, gy, r=10)

    if neighbours:
        labels     = [sim.env.labels[n]     for n in neighbours]
        categories = [sim.env.categories[n] for n in neighbours]
        dominant_label    = max(set(labels),     key=labels.count)
        dominant_category = max(set(categories), key=categories.count)
    else:
        dominant_label    = "Unknown"
        dominant_category = "Unknown"

    label_str  = "Malicious" if dominant_label == 1 else "Normal"
    print(f"\n[GhostDetector] ==============================================")
    print(f"[GhostDetector]  RESULT: Ghost packet classified as  ->  {label_str}")
    print(f"[GhostDetector]  Dominant attack category in cluster ->  {dominant_category}")
    print(f"[GhostDetector] ==============================================\n")

    return {
        "ghost_id":         ghost_id,
        "final_pos":        final_pos,
        "nearest_label":    label_str,
        "nearest_category": dominant_category,
    }
