# analysis/convergence.py
# Reads the entropy time-series from a finished Simulation and plots the
# "convergence curve" — disorder decreasing over time.

import matplotlib
matplotlib.use("Agg")   # non-interactive backend (safe for headless runs)

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def plot_entropy_curve(entropy_log: list, output_path: str = config.ENTROPY_CURVE_PNG):
    """
    Plot a smooth entropy-over-time curve and save it as a PNG.

    Parameters
    ----------
    entropy_log : list of (step, entropy) tuples, from Simulation.entropy_log
    output_path : str
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    if not entropy_log:
        print("[Convergence] No entropy data to plot.")
        return

    steps   = np.array([s for s, _ in entropy_log])
    entropy = np.array([e for _, e in entropy_log])

    # Smooth with a rolling window so the curve looks clean on a poster
    window  = max(1, len(entropy) // 20)
    smoothed = np.convolve(entropy, np.ones(window) / window, mode="same")

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0A0C14")
    ax.set_facecolor("#0A0C14")

    # Raw (faint)
    ax.plot(steps, entropy, color="#3C4060", linewidth=0.8, alpha=0.6, label="Raw entropy")
    # Smoothed
    ax.plot(steps, smoothed, color="#50B4FF", linewidth=2.2, label=f"Smoothed (window={window})")
    # Shaded area under smoothed curve
    ax.fill_between(steps, smoothed, alpha=0.12, color="#50B4FF")

    # Annotation: mark the point of ~50% entropy reduction
    idx_half = np.argmin(np.abs(smoothed - smoothed[0] * 0.5))
    if idx_half < len(steps):
        ax.axvline(steps[idx_half], color="#FFD050", linewidth=1, linestyle="--", alpha=0.6)
        ax.text(steps[idx_half] + steps[-1] * 0.01, smoothed[0] * 0.5,
                "50% order achieved", color="#FFD050", fontsize=9, va="bottom")

    ax.set_xlabel("Simulation Step", color="#C8D2E6", fontsize=12)
    ax.set_ylabel("Grid Entropy (Isolation Fraction)", color="#C8D2E6", fontsize=12)
    ax.set_title("Ant Colony Sorting — Convergence Curve\n"
                 "Entropy decreases as clusters form", color="#E0E8F0", fontsize=14)

    ax.tick_params(colors="#C8D2E6")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    for spine in ax.spines.values():
        spine.set_edgecolor("#3C4060")

    ax.legend(facecolor="#161826", edgecolor="#3C4060", labelcolor="#C8D2E6", fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[Convergence] Saved -> {output_path}")
