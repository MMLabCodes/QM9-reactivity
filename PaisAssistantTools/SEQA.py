# =============================================================================
# SEQA v2.0.1 — Symmetric Equal Quadrant Analysis
# =============================================================================
# Author: Pai Surya Darshan
# Created: 2021-07-16
#
# Purpose:
#   Perform SEQA analysis on (x, y) data:
#   - Auto scaling
#   - Quadrant + sub-quadrant assignment
#   - Density plot
#   - Statistical + inequality analysis
#
# Last Updated: 2026-01-29
#
# What's New:
# - Removed older clunky data validation and cleaning steps.
#   Now, updated with rescaling (explained below).
# - Added min-max auto-rescaling to [0, 1] for both x and y;
#   if they are not already in that range. (Thanks Issac)
# - Added a New 'Gini' Metric to further describe data 
#   With respect to it's inequality and dominance. (Thanks Fran)
# - Allows you to time the df prior to preprocessing, and then pass the original df to the main function.
# =============================================================================

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

if __name__ == "__main__":
    from PaiStyle_1 import pai_plt
else:
    from PaisAssistantTools.PaiStyle_1 import pai_plt

# =============================================================================
# PREPROCESSING
# =============================================================================

def seqa_preprocess(
    df,
    x_col,
    y_col,
    dropna=True,
    x_range=None,   # (min, max)
    y_range=None,   # (min, max)
):
    df_out = df.copy()

    # --- enforce numeric
    df_out[x_col] = pd.to_numeric(df_out[x_col], errors="coerce")
    df_out[y_col] = pd.to_numeric(df_out[y_col], errors="coerce")

    # --- remove inf
    df_out[x_col] = df_out[x_col].replace([np.inf, -np.inf], np.nan)
    df_out[y_col] = df_out[y_col].replace([np.inf, -np.inf], np.nan)

    # --- drop invalid rows
    if dropna:
        df_out = df_out.dropna(subset=[x_col, y_col]).copy()

    # ---------------------------------------------------------------------
    # NEW: TRIM BEFORE SCALING
    # ---------------------------------------------------------------------
    if x_range is not None:
        xmin, xmax = x_range
        df_out = df_out[(df_out[x_col] >= xmin) & (df_out[x_col] <= xmax)]

    if y_range is not None:
        ymin, ymax = y_range
        df_out = df_out[(df_out[y_col] >= ymin) & (df_out[y_col] <= ymax)]

    # ---------------------------------------------------------------------
    # Extract arrays AFTER trimming
    # ---------------------------------------------------------------------
    x = df_out[x_col].values
    y = df_out[y_col].values

    # --- scaling check
    def needs_scaling(arr, tol=1e-12):
        arr = np.asarray(arr, dtype=float)
        return not (np.nanmin(arr) >= -tol and np.nanmax(arr) <= 1 + tol)

    x_was_rescaled = needs_scaling(x)
    y_was_rescaled = needs_scaling(y)

    if x_was_rescaled:
        x_min, x_max = np.min(x), np.max(x)
        if np.isclose(x_max, x_min):
            x = np.full_like(x, 0.5, dtype=float)
        else:
            x = (x - x_min) / (x_max - x_min)

    if y_was_rescaled:
        y_min, y_max = np.min(y), np.max(y)
        if np.isclose(y_max, y_min):
            y = np.full_like(y, 0.5, dtype=float)
        else:
            y = (y - y_min) / (y_max - y_min)

    df_out["x_scaled"] = x
    df_out["y_scaled"] = y

    meta = {
        "scaled": x_was_rescaled or y_was_rescaled,
        "scaled_x": x_was_rescaled,
        "scaled_y": y_was_rescaled,
        "n_rows": len(df_out),
        "x_col": x_col,
        "y_col": y_col,
        "x_range": x_range,
        "y_range": y_range,
    }

    return df_out, meta

# =============================================================================
# REGION ASSIGNMENT
# =============================================================================

def seqa_assign_regions(df):
    df = df.copy()

    x = df["x_scaled"].values
    y = df["y_scaled"].values

    # --- main quadrant
    def get_quad(x, y):
        if x >= 0.5 and y >= 0.5:
            return "I"
        elif x < 0.5 and y >= 0.5:
            return "II"
        elif x < 0.5 and y < 0.5:
            return "III"
        else:
            return "IV"

    # --- sub quadrant (local)
    def get_sub(x, y):
        x_local = (x % 0.5) / 0.5
        y_local = (y % 0.5) / 0.5

        if x_local >= 0.5 and y_local >= 0.5:
            return "a"
        elif x_local < 0.5 and y_local >= 0.5:
            return "b"
        elif x_local < 0.5 and y_local < 0.5:
            return "c"
        else:
            return "d"

    df["quadrant"] = [get_quad(xi, yi) for xi, yi in zip(x, y)]
    df["sub"] = [get_sub(xi, yi) for xi, yi in zip(x, y)]
    df["region"] = df["quadrant"] + df["sub"]

    return df

# =============================================================================
# SUMMARY TABLES
# =============================================================================

def seqa_summary(df):
    total = len(df)

    # -------------------------------------------------------------------------
    # EXTREMA ANALYSIS (Top-Level Data Descriptors)
    # -------------------------------------------------------------------------

    # index positions
    idx_x_max = df["x_scaled"].idxmax()
    idx_y_max = df["y_scaled"].idxmax()
    idx_x_min = df["x_scaled"].idxmin()
    idx_y_min = df["y_scaled"].idxmin()

    # max values
    x_max = df.loc[idx_x_max, "x_scaled"]
    y_at_x_max = df.loc[idx_x_max, "y_scaled"]

    y_max = df.loc[idx_y_max, "y_scaled"]
    x_at_y_max = df.loc[idx_y_max, "x_scaled"]

    # min values
    x_min = df.loc[idx_x_min, "x_scaled"]
    y_at_x_min = df.loc[idx_x_min, "y_scaled"]

    y_min = df.loc[idx_y_min, "y_scaled"]
    x_at_y_min = df.loc[idx_y_min, "x_scaled"]

    # -------------------------------------------------------
    ## combined metrics [ OLD ]
    # df["_sum_xy"] = df["x_scaled"] + df["y_scaled"]
    # idx_combined_max = df["_sum_xy"].idxmax()
    # idx_combined_min = df["_sum_xy"].idxmin() 
    # -------------------------------------------------------

    # combined metrics [Updated using euclidean distance (from origin (0,0))] 
    """
    Found euclidean distance to be geometrically more meaningful than the sum of x and y, 
    
    Reason for this was that it captures the overall "magnitude" of the point 
    in the 2D space, rather than just the linear sum.
    """
    df["_euclid"] = np.sqrt(df["x_scaled"]**2 + df["y_scaled"]**2)

    idx_combined_max = df["_euclid"].idxmax()
    idx_combined_min = df["_euclid"].idxmin()

    combined_max = df.loc[idx_combined_max, ["x_scaled", "y_scaled"]]
    combined_min = df.loc[idx_combined_min, ["x_scaled", "y_scaled"]]

    # clean temp column
    df.drop(columns="_euclid", inplace=True)

    extrema = pd.DataFrame({
        "metric": [
            "max_x_point",
            "max_y_point",
            "min_x_point",
            "min_y_point",
            "max_combined_point",
            "min_combined_point"
        ],
        "x_value": [
            x_max,
            x_at_y_max,
            x_min,
            x_at_y_min,
            combined_max["x_scaled"],
            combined_min["x_scaled"]
        ],
        "y_value": [
            y_at_x_max,
            y_max,
            y_at_x_min,
            y_min,
            combined_max["y_scaled"],
            combined_min["y_scaled"]
        ]
    })

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _gini_from_counts(counts):
        counts = np.asarray(counts, dtype=float)

        if counts.sum() == 0:
            return 0.0

        p = counts / counts.sum()
        n = len(p)
        mu = p.mean()

        g = np.sum(np.abs(p[:, None] - p[None, :])) / (2 * n**2 * mu)

        # normalized gini
        if n > 1:
            g = g / ((n - 1) / n)

        return g

    def _entropy_from_counts(counts, normalize=True):
        counts = np.asarray(counts, dtype=float)

        if counts.sum() == 0:
            return 0.0

        p = counts / counts.sum()
        p = p[p > 0]

        H = -np.sum(p * np.log(p))

        if normalize:
            n = len(counts)
            if n > 1:
                H = H / np.log(n)

        return H

    # -------------------------------------------------------------------------
    # 4-Quadrant Summary
    # -------------------------------------------------------------------------
    q_order = ["I", "II", "III", "IV"]

    q_counts = df["quadrant"].value_counts().reindex(q_order, fill_value=0)
    q_pct = (q_counts / total) * 100

    q_summary = pd.DataFrame({
        "count": q_counts,
        "percent": q_pct
    })

    # -------------------------------------------------------------------------
    # 16-Region Summary
    # -------------------------------------------------------------------------
    r_order = [
        "Ia", "Ib", "Ic", "Id",
        "IIa", "IIb", "IIc", "IId",
        "IIIa", "IIIb", "IIIc", "IIId",
        "IVa", "IVb", "IVc", "IVd"
    ]

    r_counts = df["region"].value_counts().reindex(r_order, fill_value=0)
    r_pct = (r_counts / total) * 100

    r_summary = pd.DataFrame({
        "count": r_counts,
        "percent": r_pct
    })

    # -------------------------------------------------------------------------
    # Pairwise Metrics — 4-Quadrant Pairs
    # -------------------------------------------------------------------------
    quadrant_pairs = [
        ("I", "II"),
        ("I", "III"),
        ("I", "IV"),
        ("II", "III"),
        ("II", "IV"),
        ("III", "IV"),
    ]

    pairwise_rows_4 = []

    for q1, q2 in quadrant_pairs:
        c1 = float(q_counts[q1])
        c2 = float(q_counts[q2])
        pair_counts = np.array([c1, c2], dtype=float)

        pair_total = c1 + c2
        if pair_total == 0:
            p1 = 0.0
            p2 = 0.0
        else:
            p1 = (c1 / pair_total) * 100
            p2 = (c2 / pair_total) * 100

        g = _gini_from_counts(pair_counts)
        h = _entropy_from_counts(pair_counts, normalize=True)

        pairwise_rows_4.append({
            "pair": f"{q1}-{q2}",
            "count_1": int(c1),
            "count_2": int(c2),
            "percent_1": p1,
            "percent_2": p2,
            "pair_gini_4": g,
            "pair_entropy_4": h,
            "pair_r_spread_4": h - g,
        })

    pairwise_metrics_table_4 = pd.DataFrame(pairwise_rows_4)

    # -------------------------------------------------------------------------
    # Within-Quadrant Metrics — Whole + Pairwise
    # -------------------------------------------------------------------------
    quadrant_sub_map = {
        "I":   ["Ia", "Ib", "Ic", "Id"],
        "II":  ["IIa", "IIb", "IIc", "IId"],
        "III": ["IIIa", "IIIb", "IIIc", "IIId"],
        "IV":  ["IVa", "IVb", "IVc", "IVd"],
    }

    within_quadrant_rows = []

    for quad, subs in quadrant_sub_map.items():
        sub_counts = r_counts.reindex(subs).values.astype(float)

        g = _gini_from_counts(sub_counts)
        h = _entropy_from_counts(sub_counts, normalize=True)

        within_quadrant_rows.append({
            "quadrant": quad,
            "count_total": int(np.sum(sub_counts)),
            "gini_within_quadrant": g,
            "entropy_within_quadrant": h,
            "r_spread_within_quadrant": h - g,
            "count_a": int(r_counts[subs[0]]),
            "count_b": int(r_counts[subs[1]]),
            "count_c": int(r_counts[subs[2]]),
            "count_d": int(r_counts[subs[3]]),
        })

    within_quadrant_metrics_table_4_in_16 = pd.DataFrame(within_quadrant_rows)

    pairwise_within_quadrant_rows = []

    for quad, subs in quadrant_sub_map.items():
        local_map = {"a": subs[0], "b": subs[1], "c": subs[2], "d": subs[3]}

        for s1, s2 in [("a","b"),("a","c"),("a","d"),("b","c"),("b","d"),("c","d")]:
            c1 = float(r_counts[local_map[s1]])
            c2 = float(r_counts[local_map[s2]])
            pair_counts = np.array([c1, c2], dtype=float)

            g = _gini_from_counts(pair_counts)
            h = _entropy_from_counts(pair_counts, normalize=True)

            pairwise_within_quadrant_rows.append({
                "quadrant": quad,
                "pair": f"{s1}-{s2}",
                "subcell_1": local_map[s1],
                "subcell_2": local_map[s2],
                "count_1": int(c1),
                "count_2": int(c2),
                "percent_1": (c1/(c1+c2)*100) if (c1+c2)>0 else 0.0,
                "percent_2": (c2/(c1+c2)*100) if (c1+c2)>0 else 0.0,
                "pair_gini_within_quadrant": g,
                "pair_entropy_within_quadrant": h,
                "pair_r_spread_within_quadrant": h - g,
            })

    pairwise_within_quadrant_metrics_table_4_in_16 = pd.DataFrame(pairwise_within_quadrant_rows)

    # -------------------------------------------------------------------------
    # Inequality / Spread Metrics
    # -------------------------------------------------------------------------
    gini_4 = _gini_from_counts(q_counts.values)
    entropy_4 = _entropy_from_counts(q_counts.values)
    r_spread_4 = entropy_4 - gini_4

    gini_16 = _gini_from_counts(r_counts.values)
    entropy_16 = _entropy_from_counts(r_counts.values)
    r_spread_16 = entropy_16 - gini_16

    metrics_4 = pd.DataFrame({
        "metric": ["gini_4", "entropy_4", "r_spread_4", "gini_16", "entropy_16", "r_spread_16"],
        "value": [gini_4, entropy_4, r_spread_4, gini_16, entropy_16, r_spread_16]
    })

    summary = {
        "extrema": extrema,
        "quadrant_counts": q_counts,
        "quadrant_percent": q_pct,
        "quadrant_table": q_summary,
        "region_counts": r_counts,
        "region_percent": r_pct,

        "region_table": r_summary,

        "gini_4": gini_4,
        "entropy_4": entropy_4,
        "r_spread_4": r_spread_4,
        "gini_16": gini_16,
        "entropy_16": entropy_16,
        "r_spread_16": r_spread_16,
        
        "metrics_table_4": metrics_4,
        "pairwise_metrics_table_4": pairwise_metrics_table_4,
        "within_quadrant_metrics_table_4_in_16": within_quadrant_metrics_table_4_in_16,
        "pairwise_within_quadrant_metrics_table_4_in_16": pairwise_within_quadrant_metrics_table_4_in_16,
    }

    return summary

# =============================================================================
# PLOTTING
# =============================================================================

# =============================================================================
# HEATMAP HELPERS
# =============================================================================

def _compute_occupancy_grid(df, n_bins):
    """
    Build an occupancy grid over the unit square.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain 'x_scaled' and 'y_scaled'
    n_bins : int
        Number of bins per axis (2, 4, 8, ...)

    Returns
    -------
    grid : np.ndarray of shape (n_bins, n_bins)
        Row 0 is top (high y), last row is bottom (low y)
        Col 0 is left (low x), last col is right (high x)
    """
    x = pd.to_numeric(df["x_scaled"], errors="coerce").values
    y = pd.to_numeric(df["y_scaled"], errors="coerce").values

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    edges = np.linspace(0.0, 1.0, n_bins + 1)

    x_bin = np.clip(np.digitize(x, edges, right=False) - 1, 0, n_bins - 1)
    y_bin = np.clip(np.digitize(y, edges, right=False) - 1, 0, n_bins - 1)

    grid = np.zeros((n_bins, n_bins), dtype=int)

    for xb, yb in zip(x_bin, y_bin):
        row = (n_bins - 1) - yb
        col = xb
        grid[row, col] += 1

    return grid


# =============================================================================
# HEATMAP (WITH TRANSPARENCY + GREY UNDERLAY SCATTER)
# =============================================================================

def _plot_heatmap(
    ax,
    grid,
    title,
    cmap="Spectral_r",
    annotate=True,
    alpha=0.85,
    df_points=None,
    point_size=10,
    point_alpha=0.30,
):
    n = grid.shape[0]
    total = grid.sum()

    # ---------------------------------------------------------------------
    # BACKGROUND SCATTER (GREY, TRUE DATA COORDINATES)
    # ---------------------------------------------------------------------
    if df_points is not None:
        x = pd.to_numeric(df_points["x_scaled"], errors="coerce").values
        y = pd.to_numeric(df_points["y_scaled"], errors="coerce").values

        mask = np.isfinite(x) & np.isfinite(y)
        x = x[mask]
        y = y[mask]

        ax.scatter(
            x,
            y,
            s=point_size,
            alpha=point_alpha,
            color="grey",
            linewidths=0,
            zorder=1,
        )

    # ---------------------------------------------------------------------
    # HEATMAP (ALSO TRUE DATA COORDINATES)
    # ---------------------------------------------------------------------
    im = ax.imshow(
        grid,
        cmap=cmap,
        interpolation="nearest",
        origin="upper",
        extent=(0, 1, 0, 1),
        aspect="equal",
        alpha=alpha,
        zorder=2,
    )

    # ---------------------------------------------------------------------
    # CELL BORDERS
    # ---------------------------------------------------------------------
    edges = np.linspace(0.0, 1.0, n + 1)

    for e in edges:
        ax.axvline(e, color="white", linestyle="-", linewidth=1.0, alpha=0.8, zorder=2.5)
        ax.axhline(e, color="white", linestyle="-", linewidth=1.0, alpha=0.8, zorder=2.5)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title)

    # ---------------------------------------------------------------------
    # TICKS
    # ---------------------------------------------------------------------
    if n == 2:
        centers = np.array([0.25, 0.75])
        ax.set_xticks(centers)
        ax.set_yticks(centers)
        ax.set_xticklabels(["Low", "High"])
        ax.set_yticklabels(["Low", "High"])
    elif n == 4:
        centers = np.array([0.125, 0.375, 0.625, 0.875])
        ax.set_xticks(centers)
        ax.set_yticks(centers)
        ax.set_xticklabels(["Low", "Low-Med", "Med-High", "High"], rotation=35, ha="right")
        ax.set_yticklabels(["Low", "Low-Med", "Med-High", "High"])
    else:
        ax.set_xticks([])
        ax.set_yticks([])

    # ---------------------------------------------------------------------
    # ANNOTATIONS
    # ---------------------------------------------------------------------
    if annotate:
        vmax = grid.max() if grid.max() > 0 else 1
        x_centers = (edges[:-1] + edges[1:]) / 2
        y_centers = (edges[:-1] + edges[1:]) / 2

        for i in range(n):
            for j in range(n):
                val = int(grid[i, j])
                pct = (100 * val / total) if total > 0 else 0.0
                text_color = "black" if grid[i, j] < 0.65 * vmax else "white"

                x_text = x_centers[j]
                y_text = y_centers[::-1][i]

                ax.text(
                    x_text,
                    y_text,
                    f"{pct:.1f}%\n({val})",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=text_color,
                    zorder=3,
                )

    # ---------------------------------------------------------------------
    # MAIN DIVIDERS
    # ---------------------------------------------------------------------
    ax.axvline(0.5, color="black", lw=2, zorder=4)
    ax.axhline(0.5, color="black", lw=2, zorder=4)

    return im


# =============================================================================
# DASHBOARD
# =============================================================================

def seqa_plot_dashboard(
    df,
    meta,
    show_extrema=True,
    heatmap_alpha=0.85,
    heatmap_point_size=10,
    heatmap_point_alpha=0.30,
    show_points_under_heatmap=True,
):
    fig, axes = pai_plt.subplots(2, 2, figsize=(10, 9))

    ax_scatter = axes[0, 0]
    ax_4       = axes[0, 1]
    ax_16      = axes[1, 0]
    ax_64      = axes[1, 1]

    x_label = meta["x_col"] + (" (rescaled)" if meta["scaled_x"] else "")
    y_label = meta["y_col"] + (" (rescaled)" if meta["scaled_y"] else "")

    title_fs = 14
    cbar_frac = 0.035
    cbar_pad = 0.015

    # ---------------------------------------------------------------------
    # SCATTER PANEL
    # ---------------------------------------------------------------------
    x = pd.to_numeric(df["x_scaled"], errors="coerce").values
    y = pd.to_numeric(df["y_scaled"], errors="coerce").values

    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]

    try:
        xy = np.vstack([x, y])
        kde = gaussian_kde(xy)
        z = kde(xy)

        idx = np.argsort(z)
        x_plot, y_plot, z_plot = x[idx], y[idx], z[idx]

        sc = ax_scatter.scatter(
            x_plot,
            y_plot,
            c=z_plot,
            s=18,
            cmap="inferno",
            alpha=0.85,
            linewidths=0,
        )

        cbar_sc = fig.colorbar(sc, ax=ax_scatter, fraction=cbar_frac, pad=cbar_pad)
        cbar_sc.set_label("Density")
        cbar_sc.ax.tick_params(labelsize=9, width=0.8, length=3)
        cbar_sc.outline.set_linewidth(0.8)

        xx, yy = np.meshgrid(
            np.linspace(0, 1, 250),
            np.linspace(0, 1, 250)
        )
        grid_xy = np.vstack([xx.ravel(), yy.ravel()])
        zz = kde(grid_xy).reshape(xx.shape)

        ax_scatter.contour(
            xx,
            yy,
            zz,
            levels=8,
            colors="white",
            linewidths=0.6,
            alpha=0.40,
        )

    except Exception:
        ax_scatter.scatter(x, y, s=18, alpha=0.7)

    ax_scatter.axvline(0.5, color="black", lw=2)
    ax_scatter.axhline(0.5, color="black", lw=2)

    for v in [0.25, 0.75]:
        ax_scatter.axvline(v, color="grey", lw=1)
        ax_scatter.axhline(v, color="grey", lw=1)

    ax_scatter.set_xlim(0, 1)
    ax_scatter.set_ylim(0, 1)
    ax_scatter.set_xlabel(x_label)
    ax_scatter.set_ylabel(y_label)
    ax_scatter.set_title("Density Map", fontsize=title_fs)

    # ---------------------------------------------------------------------
    # EXTREMA ANNOTATION
    # ---------------------------------------------------------------------
    if show_extrema:
        idx_x_max = df["x_scaled"].idxmax()
        idx_x_min = df["x_scaled"].idxmin()
        idx_y_max = df["y_scaled"].idxmax()
        idx_y_min = df["y_scaled"].idxmin()

        df_tmp = df.copy()
        df_tmp["_euclid"] = np.sqrt(df_tmp["x_scaled"]**2 + df_tmp["y_scaled"]**2)
        idx_sum_max = df_tmp["_euclid"].idxmax()
        idx_sum_min = df_tmp["_euclid"].idxmin()

        points = {
            "Max X": df.loc[idx_x_max, ["x_scaled", "y_scaled"]],
            "Min X": df.loc[idx_x_min, ["x_scaled", "y_scaled"]],
            "Max Y": df.loc[idx_y_max, ["x_scaled", "y_scaled"]],
            "Min Y": df.loc[idx_y_min, ["x_scaled", "y_scaled"]],
            "Max R": df.loc[idx_sum_max, ["x_scaled", "y_scaled"]],
            "Min R": df.loc[idx_sum_min, ["x_scaled", "y_scaled"]],
        }

        arrow_kw = dict(
            arrowstyle="->",
            color="black",
            lw=1.2
        )

        for label, row in points.items():
            px = float(row["x_scaled"])
            py = float(row["y_scaled"])

            dx = 0.04 if px < 0.8 else -0.10
            dy = 0.04 if py < 0.8 else -0.08

            ax_scatter.annotate(
                label,
                xy=(px, py),
                xytext=(px + dx, py + dy),
                textcoords="data",
                fontsize=9,
                arrowprops=arrow_kw,
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    fc="white",
                    ec="none",
                    alpha=0.7
                )
            )

    # ---------------------------------------------------------------------
    # POINT TOGGLE
    # ---------------------------------------------------------------------
    df_pts = df if show_points_under_heatmap else None

    # ---------------------------------------------------------------------
    # SEQA-4
    # ---------------------------------------------------------------------
    grid_4 = _compute_occupancy_grid(df, n_bins=2)
    im4 = _plot_heatmap(
        ax_4,
        grid_4,
        "SEQA-4",
        annotate=True,
        alpha=heatmap_alpha,
        df_points=df_pts,
        point_size=heatmap_point_size,
        point_alpha=heatmap_point_alpha,
    )
    cbar4 = fig.colorbar(im4, ax=ax_4, fraction=cbar_frac, pad=cbar_pad)
    cbar4.set_label("Count")
    cbar4.ax.tick_params(labelsize=9, width=0.8, length=3)
    cbar4.outline.set_linewidth(0.8)

    # ---------------------------------------------------------------------
    # SEQA-16
    # ---------------------------------------------------------------------
    grid_16 = _compute_occupancy_grid(df, n_bins=4)
    im16 = _plot_heatmap(
        ax_16,
        grid_16,
        "SEQA-16",
        annotate=True,
        alpha=heatmap_alpha,
        df_points=df_pts,
        point_size=heatmap_point_size,
        point_alpha=heatmap_point_alpha,
    )
    cbar16 = fig.colorbar(im16, ax=ax_16, fraction=cbar_frac, pad=cbar_pad)
    cbar16.set_label("Count")
    cbar16.ax.tick_params(labelsize=9, width=0.8, length=3)
    cbar16.outline.set_linewidth(0.8)

    # ---------------------------------------------------------------------
    # SEQA-64
    # ---------------------------------------------------------------------
    grid_64 = _compute_occupancy_grid(df, n_bins=8)
    im64 = _plot_heatmap(
        ax_64,
        grid_64,
        "SEQA-64",
        annotate=False,
        alpha=heatmap_alpha,
        df_points=df_pts,
        point_size=heatmap_point_size,
        point_alpha=heatmap_point_alpha,
    )
    cbar64 = fig.colorbar(im64, ax=ax_64, fraction=cbar_frac, pad=cbar_pad)
    cbar64.set_label("Count")
    cbar64.ax.tick_params(labelsize=9, width=0.8, length=3)
    cbar64.outline.set_linewidth(0.8)

    fig.suptitle("SEQ-Analysis", y=0.96)

    fig.subplots_adjust(
        left=0.07,
        right=0.93,
        bottom=0.07,
        top=0.92,
        wspace=0.18,
        hspace=0.27
    )

    return fig, axes


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def seqa_analyse(
    df,
    x_col,
    y_col,
    show_extrema=True,
    show_plot=False,
    x_range=None,
    y_range=None,
    heatmap_alpha=0.75,
    heatmap_point_size=10,
    heatmap_point_alpha=0.90,
    show_points_under_heatmap=True,
):
    """
    Perform Symmetric Equal Quadrant Analysis (SEQA) on two variables and
    generate both quantitative summaries and a multi-panel visual dashboard.

    Overview
    --------
    SEQA is a spatial analysis framework that transforms two variables into a
    normalized 2D space (0-1 range), partitions this space into structured regions,
    and quantifies how data is distributed across those regions.

    The method provides:
        1. Structural decomposition of data into quadrants and sub-regions
        2. Inequality and distribution metrics (Gini, entropy)
        3. Visual interpretation through density and occupancy maps

    This function acts as a full pipeline:
        Raw Data → Preprocessing → Region Assignment → Statistical Summary → Visualization

    Workflow
    --------
    1. Preprocessing (seqa_preprocess)
        - Converts selected columns to numeric
        - Removes invalid values (NaN / inf)
        - Optionally trims data using x_range and/or y_range
        - Applies min-max scaling to [0, 1] if required

    2. Region Assignment (seqa_assign_regions)
        - Assigns each data point to:
            • One of 4 main quadrants (I-IV)
            • One of 16 sub-regions (a-d within each quadrant)
        - Produces categorical labels for structured spatial analysis

    3. Statistical Summary (seqa_summary)
        - Computes:
            • Quadrant and region counts + percentages
            • Gini coefficient (ΔG,dominance / distribution inequality) | Pairwise-compared
            • Entropy (ΔH, distribution spread) | Probability-compared
            • R_spread = ΔH - ΔG
                • Negative :
                    • Data behaviour is site-specific
                    • Only few regions contribute
                    • Dominant / higly localised data points
                Therefore, indicative of a “Dominant regime”
                -----
                • Positive:
                    • Data behaviour is distributed
                    • Multiple regions contribute
                    • Delocalised data points across quadrants/sub-quadrants
                Therefore, indicative of a “Distributed regime”
                -----
                • Approx. 0 (between 1.5 and -1.5):
                    Therefore, indicative of a “Moderate data dstribution”

            • Pairwise comparisons between regions
            • Within-quadrant structural breakdown
            • Extremal points (max/min x, y, and radial magnitude)

    4. Visualization (seqa_plot_dashboard)
        - Generates a 2x2 dashboard:
            • Density scatter plot with contours
            • SEQA-4 (2x2 grid)
            • SEQA-16 (4x4 grid)
            • SEQA-64 (8x8 grid)
        - Optional overlay of original data points beneath heatmaps
        - Transparency controls allow inspection of micro vs macro structure

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataset containing the variables to analyse.

    x_col : str
        Column name for the x-axis variable.

    y_col : str
        Column name for the y-axis variable.

    show_extrema : bool, default=True
        If True, annotate key extremal points on the density plot:
            • Maximum / minimum x
            • Maximum / minimum y
            • Maximum / minimum radial magnitude (Euclidean distance)

    show_plot : bool, default=False
        If True, renders the visualization using ``pai_plt.show()``.

    x_range : tuple(float, float) or None, default=None
        Optional (min, max) range to filter x values BEFORE scaling.
        Useful for isolating specific regimes of interest.

    y_range : tuple(float, float) or None, default=None
        Optional (min, max) range to filter y values BEFORE scaling.

    heatmap_alpha : float, default=0.85
        Transparency of heatmap layers (0 = fully transparent, 1 = opaque).
        Lower values reveal more of the underlying scatter distribution.

    heatmap_point_size : float, default=10
        Marker size for scatter points shown beneath heatmaps.

    heatmap_point_alpha : float, default=0.90
        Transparency of scatter points beneath heatmaps.

    show_points_under_heatmap : bool, default=True
        If True, overlays the original data points (in grey) beneath each
        heatmap panel to reveal intra-cell structure.

    Returns
    -------
    dict
        A dictionary containing:

        - ``df_regions`` : pandas.DataFrame
            Processed dataset including:
                • Scaled coordinates (`x_scaled`, `y_scaled`)
                • Assigned quadrant and sub-region labels

        - ``meta`` : dict
            Metadata describing preprocessing:
                • Whether scaling was applied
                • Original column names
                • Applied trimming ranges
                • Number of retained data points

        - ``summary`` : dict
            Comprehensive statistical outputs including:
                • Quadrant and region distributions
                • Gini and entropy metrics
                • Pairwise inequality tables
                • Within-quadrant structural analysis
                • Extremal point descriptors

        - ``fig`` : matplotlib.figure.Figure
            The generated SEQA dashboard visualization.

        - ``axes`` : numpy.ndarray
            Array of axes corresponding to the 2x2 dashboard layout.

    Notes
    -----
    - All spatial analysis is performed in normalized [0,1] space to ensure
      consistency across datasets and comparability across panels.

    - Heatmap panels (SEQA-4 / 16 / 64) represent different resolutions of the
      same underlying space:
            • SEQA-4   → coarse global structure
            • SEQA-16  → intermediate structure
            • SEQA-64  → fine-grained local structure

    - Gini measures inequality of distribution across regions,
      while entropy measures how evenly the data is spread.

    - This method is particularly useful for analysing:
            • Structure-property relationships
            • Distributional asymmetry
            • Multi-scale spatial organisation of data

    - Trimming is applied BEFORE scaling to avoid distortion of relative structure.

    """

    df_clean, meta = seqa_preprocess(
        df,
        x_col,
        y_col,
        x_range=x_range,
        y_range=y_range,
    )

    df_regions = seqa_assign_regions(df_clean)
    summary = seqa_summary(df_regions)

    fig, axes = seqa_plot_dashboard(
        df_regions,
        meta,
        show_extrema=show_extrema,
        heatmap_alpha=heatmap_alpha,
        heatmap_point_size=heatmap_point_size,
        heatmap_point_alpha=heatmap_point_alpha,
        show_points_under_heatmap=show_points_under_heatmap,
    )

    if show_plot:
        pai_plt.show()

    return {
        "df_regions": df_regions,
        "meta": meta,
        "summary": summary,
        "fig": fig,
        "axes": axes,
    }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    df = pd.read_csv(
        "ALL_DATA/FINAL_MAIN_Core_FG_Labelled_Rescaled_iteration_1_with_normal_RE_with_BM_scaffolds.csv"
    )

    a = seqa_analyse(
        df,
        "gini_r_p",
        "reaction_energy",
        show_extrema=True,
        show_plot=True,
        heatmap_alpha=0.75,
        heatmap_point_size=8,
        heatmap_point_alpha=0.25,
        show_points_under_heatmap=True,
    )

    # a["fig"].savefig("PaisAssistantTools/images/test_seqa_dashboard.png", dpi=1200)
    print(a["summary"])
