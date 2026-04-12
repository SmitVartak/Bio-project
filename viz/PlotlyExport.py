# viz/PlotlyExport.py
# Produces interactive HTML scatter plots of the final cluster state
# that can be opened in any browser and included in a presentation.

import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def export_final_clusters(env, output_path: str = config.FINAL_CLUSTER_HTML):
    """
    Build an interactive 2D scatter of all placed items colored by label.

    Parameters
    ----------
    env         : Environment  (after simulation has run)
    output_path : str          Where to save the .html file
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    records = []
    for item_id, gx, gy in env.placed_items():
        records.append({
            "grid_x":   gx,
            "grid_y":   gy,
            "label":    env.labels[item_id],
            "category": env.categories[item_id],
            "item_id":  item_id,
        })

    if not records:
        print("[PlotlyExport] No placed items — skipping export.")
        return

    df = pd.DataFrame(records)
    df["color_label"] = df["label"].map({0: "Normal", 1: "Malicious"})

    color_map = {"Normal": "#3CDA78", "Malicious": "#DC3C50"}

    fig = px.scatter(
        df,
        x="grid_x",
        y="grid_y",
        color="color_label",
        color_discrete_map=color_map,
        hover_data={"category": True, "item_id": True,
                    "grid_x": True, "grid_y": True},
        title="Ant Colony Sorting — Final Cluster State",
        labels={"grid_x": "Grid X", "grid_y": "Grid Y",
                "color_label": "Traffic Type"},
        template="plotly_dark",
        opacity=0.75,
    )

    fig.update_traces(marker=dict(size=5))
    fig.update_layout(
        paper_bgcolor="#0A0C14",
        plot_bgcolor="#0A0C14",
        font=dict(family="Consolas, monospace", color="#C8D2E6"),
        title_font_size=18,
        legend=dict(
            bgcolor="rgba(30,33,50,0.8)",
            bordercolor="#3C4060",
            borderwidth=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    fig.write_html(output_path)
    print(f"[PlotlyExport] Saved -> {output_path}")


def export_pca_initial(df_data, output_path: str = "output/pca_initial.html"):
    """
    Export the initial PCA distribution BEFORE ant sorting, for comparison.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    color_map = {"Normal": "#3CDA78", "Malicious": "#DC3C50"}
    df_data = df_data.copy()
    df_data["color_label"] = df_data["label"].map({0: "Normal", 1: "Malicious"})

    fig = px.scatter(
        df_data,
        x="x",
        y="y",
        color="color_label",
        color_discrete_map=color_map,
        hover_data={"category": True},
        title="PCA Distribution — Before Ant Sorting",
        labels={"x": "PC1", "y": "PC2", "color_label": "Traffic Type"},
        template="plotly_dark",
        opacity=0.75,
    )
    fig.update_traces(marker=dict(size=5))
    fig.update_layout(
        paper_bgcolor="#0A0C14",
        plot_bgcolor="#0A0C14",
        font=dict(family="Consolas, monospace", color="#C8D2E6"),
    )
    fig.write_html(output_path)
    print(f"[PlotlyExport] Saved PCA initial -> {output_path}")
