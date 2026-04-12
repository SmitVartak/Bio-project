# analysis/comparison.py
# Runs K-Means and DBSCAN on the same PCA-reduced data and compares
# Adjusted Rand Index (ARI) scores against ground-truth labels.

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import adjusted_rand_score, silhouette_score
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def run_comparison(df_data: pd.DataFrame,
                   ant_assignments: np.ndarray,
                   output_path: str = config.COMPARISON_PNG):
    """
    Compare ant clustering against K-Means and DBSCAN using ARI.

    Parameters
    ----------
    df_data         : pd.DataFrame  Output of DataPipeline (has x, y, label columns).
    ant_assignments : np.ndarray    Shape (n_items,).  Cell index per item from Simulation.
                                    Items with value -1 are still being carried (ignored).
    output_path     : str
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    X      = df_data[["x", "y"]].values
    labels = df_data["label"].values

    results = {}

    # ── Ant (convert cell indices → cluster IDs via connected-component proxy) ──
    valid_mask = ant_assignments != -1
    if valid_mask.sum() > 0:
        # Use the cell index itself as a rough cluster proxy.
        # Items in the same grid cell share the same "cluster" id.
        ant_pred = ant_assignments.copy()
        ant_ari  = adjusted_rand_score(labels[valid_mask], ant_pred[valid_mask])
        try:
            ant_sil = silhouette_score(X[valid_mask], ant_pred[valid_mask])
        except Exception:
            ant_sil = float("nan")
        results["Ant Colony\nSorting"] = {"ARI": ant_ari, "Silhouette": ant_sil}
        print(f"[Comparison] Ant   ARI={ant_ari:.4f}  Silhouette={ant_sil:.4f}")
    else:
        print("[Comparison] No valid ant assignments — skipping Ant metric.")

    # ── K-Means ──────────────────────────────────────────────────────────────
    n_clusters = max(2, int(labels.max()) + 1)
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    km_pred = km.fit_predict(X)
    km_ari  = adjusted_rand_score(labels, km_pred)
    try:
        km_sil = silhouette_score(X, km_pred)
    except Exception:
        km_sil = float("nan")
    results["K-Means"] = {"ARI": km_ari, "Silhouette": km_sil}
    print(f"[Comparison] K-Means  ARI={km_ari:.4f}  Silhouette={km_sil:.4f}")

    # ── DBSCAN ───────────────────────────────────────────────────────────────
    db = DBSCAN(eps=0.5, min_samples=5)
    db_pred = db.fit_predict(X)
    n_found = len(set(db_pred)) - (1 if -1 in db_pred else 0)
    print(f"[Comparison] DBSCAN found {n_found} clusters")
    if n_found >= 2:
        db_ari  = adjusted_rand_score(labels, db_pred)
        try:
            mask_db = db_pred != -1
            db_sil  = silhouette_score(X[mask_db], db_pred[mask_db]) if mask_db.sum() > 1 else float("nan")
        except Exception:
            db_sil = float("nan")
        results["DBSCAN"] = {"ARI": db_ari, "Silhouette": db_sil}
        print(f"[Comparison] DBSCAN  ARI={db_ari:.4f}  Silhouette={db_sil:.4f}")
    else:
        results["DBSCAN"] = {"ARI": 0.0, "Silhouette": float("nan")}

    # ── Plot ─────────────────────────────────────────────────────────────────
    methods      = list(results.keys())
    ari_scores   = [results[m]["ARI"]        for m in methods]
    sil_scores   = [results[m]["Silhouette"] for m in methods]

    x_pos = np.arange(len(methods))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor("#0A0C14")
    ax.set_facecolor("#0A0C14")

    bars_ari = ax.bar(x_pos - width/2, ari_scores, width,
                      label="Adjusted Rand Index (↑ better)",
                      color="#50B4FF", alpha=0.85, edgecolor="#0A0C14")
    bars_sil = ax.bar(x_pos + width/2,
                      [s if not np.isnan(s) else 0 for s in sil_scores], width,
                      label="Silhouette Score (↑ better, max=1)",
                      color="#3CDA78", alpha=0.85, edgecolor="#0A0C14")

    # Value labels above bars
    for bar in bars_ari:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                f"{h:.3f}", ha="center", va="bottom", color="#C8D2E6", fontsize=10)
    for bar in bars_sil:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                f"{h:.3f}", ha="center", va="bottom", color="#C8D2E6", fontsize=10)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(methods, color="#C8D2E6", fontsize=11)
    ax.set_ylabel("Score", color="#C8D2E6", fontsize=12)
    ax.set_ylim(-0.1, 1.2)
    ax.set_title("Clustering Algorithm Comparison\n"
                 "Ant Colony Sorting vs K-Means vs DBSCAN",
                 color="#E0E8F0", fontsize=14)
    ax.tick_params(colors="#C8D2E6")
    for spine in ax.spines.values():
        spine.set_edgecolor("#3C4060")

    ax.legend(facecolor="#161826", edgecolor="#3C4060", labelcolor="#C8D2E6", fontsize=10)
    ax.axhline(0, color="#3C4060", linewidth=0.8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[Comparison] Chart saved -> {output_path}")

    return results
