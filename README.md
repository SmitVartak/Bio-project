# Swarm-Intelligent Network Intrusion Detection System (NIDS)
## B.Tech Bio-Inspired Computing Project

Uses **Ant Colony Sorting** (Lumer & Faieta, 1994) to cluster network traffic
records from the UNSW-NB15 dataset in an **unsupervised** manner.
After convergence, malicious and normal packets form spatially distinct
clusters — without the algorithm ever being told what a threat looks like.

---

## Project Structure

```
Bio project/
├── data/
│   └── UNSW_NB15_training-set.csv   ← you download this
├── src/
│   ├── DataPipeline.py      Load CSV → StandardScaler → PCA → 2D coords
│   ├── Environment.py       Toroidal 2D grid, item placement, neighbourhood queries
│   ├── Ant.py               Ant state machine (loaded/unloaded, memory)
│   ├── ClusteringEngine.py  Pickup / drop probability math (Lumer & Faieta)
│   └── Simulation.py        Main loop, entropy logging, ghost injection
├── viz/
│   ├── PyGameRenderer.py    Live "God View" Pygame window
│   └── PlotlyExport.py      Interactive HTML scatter plots
├── analysis/
│   ├── convergence.py       Entropy-over-time curve plot
│   ├── comparison.py        Ant vs K-Means vs DBSCAN comparison chart
│   └── ghost_detector.py    Inject unseen packet → classify it
├── output/                  ← generated at runtime
├── config.py                All hyperparameters in one place
├── main.py                  CLI entry point
└── requirements.txt
```

---

## Setup

### 1. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 2. Download the dataset

Go to: https://research.unsw.edu.au/projects/unsw-nb15-dataset

Download **UNSW_NB15_training-set.csv** and place it in the `data/` folder:

```
data/UNSW_NB15_training-set.csv
```
### 3. Download the Project

```powershell
git clone https://github.com/SmitVartak/Bio-project.git
```
you might need to set up git bash and authenticate your account first
---

## Running the Project

All commands are run from the project root directory.

### Quick headless demo (no display needed, ~2 min)
```powershell
python main.py --mode headless --steps 100000 --samples 1000
```
Outputs:
- `output/pca_initial.html`   — PCA scatter before sorting
- `output/final_clusters.html` — final cluster state (open in browser)
- `output/entropy_curve.png`   — convergence graph

### Full live simulation (Pygame window)
```powershell
python main.py --mode sim
```

### Algorithm comparison (Ant vs K-Means vs DBSCAN)
```powershell
python main.py --mode compare --steps 200000
```
Outputs: `output/comparison.png`

### Ghost / Zero-Day detection demo
```powershell
python main.py --mode ghost --ghost-profile DoS
```
Available profiles: `DoS`, `Botnet`, `Recon`, `Normal`

---

## Key Hyperparameters (config.py)

| Parameter | Default | Effect |
|---|---|---|
| `GRID_SIZE` | 100 | Larger grids → more spread, slower |
| `N_ANTS` | 50 | More ants → faster but more CPU |
| `ALPHA` | 0.5 | Similarity threshold — key tuning knob |
| `K1` | 0.1 | Pickup eagerness |
| `K2` | 0.3 | Drop readiness |
| `MEMORY_SIZE` | 15 | Anti-flicker steps |
| `MAX_STEPS` | 300,000 | Runtime vs. quality tradeoff |

---

## How It Works

1. **Data** — 2000 network flows from UNSW-NB15 are normalized and
   compressed to 2D via PCA.  Each flow becomes a point on the grid.
2. **Ants** — 50 agents wander the toroidal grid.  They pick up isolated
   points (low local similarity) and drop them near similar points (high
   local similarity), following the Lumer-Faieta probability formulas.
3. **Convergence** — Over hundreds of thousands of steps, malicious flows
   (DoS, Exploits, Fuzzers, etc.) cluster together; normal flows cluster
   separately.  Grid entropy drops as clusters form.
4. **Ghost Detection** — A synthetic packet is dropped onto the settled
   grid.  The ants push it toward the most similar cluster, revealing
   its likely attack category.

---

## References

- Lumer, E. D., & Faieta, B. (1994). *Diversity and adaptation in populations
  of clustering ants.* Proceedings of the 3rd International Conference on
  Simulation of Adaptive Behavior (SAB94), pp. 501–508.
- Moustafa, N., & Slay, J. (2015). *UNSW-NB15: A comprehensive data set for
  network intrusion detection systems.* MilCIS 2015.
