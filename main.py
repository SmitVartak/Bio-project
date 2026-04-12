# main.py — Entry point for the Swarm-Intelligent NIDS project
# Run with:  python main.py --help

import argparse
import os
import sys

import config
from src.DataPipeline import load_and_prepare


def parse_args():
    parser = argparse.ArgumentParser(
        description="Swarm-Intelligent Network Intrusion Detection System\n"
                    "Ant Colony Sorting on UNSW-NB15 network flow data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["sim", "headless", "compare", "ghost"],
        default="headless",
        help=(
            "sim      → live Pygame window during simulation\n"
            "headless → run without display; save Plotly HTML + entropy PNG\n"
            "compare  → run Ant + K-Means + DBSCAN comparison chart\n"
            "ghost    → run headless then perform ghost detection test"
        ),
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Override MAX_STEPS from config.py (e.g. --steps 50000 for a quick demo).",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="Override N_SAMPLES from config.py.",
    )
    parser.add_argument(
        "--ghost-profile",
        type=str,
        default="DoS",
        choices=["DoS", "Botnet", "Recon", "Normal"],
        help="Which synthetic attack profile to inject in ghost mode.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Allow CLI overrides of the two most common config values
    if args.steps is not None:
        config.MAX_STEPS = args.steps
        print(f"[main] MAX_STEPS overridden to {config.MAX_STEPS:,}")
    if args.samples is not None:
        config.N_SAMPLES = args.samples
        print(f"[main] N_SAMPLES overridden to {config.N_SAMPLES:,}")

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # ── Load and preprocess data ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(" Swarm-Intelligent NIDS — Ant Colony Sorting")
    print(f" Mode: {args.mode.upper()}")
    print(f"{'='*60}\n")

    if not os.path.exists(config.DATA_PATH):
        print(f"[ERROR] Dataset not found at: {config.DATA_PATH}")
        print("  Download the UNSW-NB15 training set CSV from:")
        print("  https://research.unsw.edu.au/projects/unsw-nb15-dataset")
        print("  and place it at:", config.DATA_PATH)
        sys.exit(1)

    df = load_and_prepare()

    # Export the initial PCA scatter before any sorting
    from viz.PlotlyExport import export_pca_initial
    export_pca_initial(df)

    # ── Instantiate simulation ────────────────────────────────────────────────
    from src.Simulation import Simulation
    sim = Simulation(df)

    # ── Mode: live Pygame ─────────────────────────────────────────────────────
    if args.mode == "sim":
        from viz.PyGameRenderer import PyGameRenderer
        renderer = PyGameRenderer()
        try:
            for state in sim.run():
                renderer.render(state)
        except KeyboardInterrupt:
            print("\n[main] Simulation interrupted by user.")
        finally:
            renderer.close()

    # ── Mode: headless (no display) ───────────────────────────────────────────
    elif args.mode in ("headless", "compare", "ghost"):
        try:
            for _ in sim.run():
                pass   # just consume the generator (prints progress to stdout)
        except KeyboardInterrupt:
            print("\n[main] Simulation interrupted — exporting partial results.")

    # ── Export final cluster state ────────────────────────────────────────────
    from viz.PlotlyExport import export_final_clusters
    export_final_clusters(sim.env)

    # Export entropy convergence curve
    from analysis.convergence import plot_entropy_curve
    plot_entropy_curve(sim.entropy_log)

    print(f"\n[main] Output files saved to: {os.path.abspath(config.OUTPUT_DIR)}/")

    # ── Mode: compare ─────────────────────────────────────────────────────────
    if args.mode == "compare":
        from analysis.comparison import run_comparison
        ant_assignments = sim.get_cluster_assignments()
        run_comparison(df, ant_assignments)

    # ── Mode: ghost ───────────────────────────────────────────────────────────
    if args.mode == "ghost":
        from analysis.ghost_detector import run_ghost_detection
        run_ghost_detection(sim, ghost_name=args.ghost_profile)

    print("\n[main] Done.")


if __name__ == "__main__":
    main()
