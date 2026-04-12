# config.py — Central hyperparameter store for the Swarm-Intelligent NIDS
# Adjust these values to tune the simulation without touching any other file.

# ── Grid & Simulation ────────────────────────────────────────────────────────
GRID_SIZE       = 100       # Grid is GRID_SIZE x GRID_SIZE cells (toroidal)
N_ANTS          = 50        # Number of ant agents
MAX_STEPS       = 300_000   # Total simulation steps (reduce for a quick demo)
NEIGHBORHOOD_R  = 1         # Moore-neighbourhood radius for similarity search

# ── Data ─────────────────────────────────────────────────────────────────────
N_SAMPLES       = 2000      # How many records to sample from the CSV
PCA_COMPONENTS  = 2         # PCA output dimensions (must stay 2 for the 2D grid)
DATA_PATH       = "data/UNSW_NB15_training-set.csv"

# ── Ant Behaviour ────────────────────────────────────────────────────────────
K1              = 0.1       # Pickup sensitivity (higher → ants pick up more eagerly)
K2              = 0.3       # Drop sensitivity   (higher → ants drop less readily)
ALPHA           = 0.5       # Similarity threshold scale
MEMORY_SIZE     = 15        # Steps an ant remembers a dropped item (prevents flicker)

# ── Rendering ────────────────────────────────────────────────────────────────
WINDOW_SIZE     = 800       # Pygame window pixel width/height
FPS_CAP         = 60        # Pygame frame-rate cap
ENTROPY_INTERVAL= 1_000     # Record entropy every N steps

# ── Output paths ─────────────────────────────────────────────────────────────
OUTPUT_DIR          = "output"
FINAL_CLUSTER_HTML  = "output/final_clusters.html"
ENTROPY_CURVE_PNG   = "output/entropy_curve.png"
COMPARISON_PNG      = "output/comparison.png"
