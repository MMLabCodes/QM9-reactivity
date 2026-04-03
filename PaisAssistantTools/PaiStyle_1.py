# =============================================================================
# PaiStyle_1 — Matplotlib Configuration (Computer Modern)
# =============================================================================
# Author : Surya Darshan
# Purpose: Centralised plotting style for all projects
# Usage  : from PaiStyle import pai_plt
# =============================================================================

import matplotlib as mpl
import matplotlib.pyplot as pai_plt

# -----------------------------------------------------------------------------
# Function: apply_pai_style
# Purpose : Apply consistent plotting style across all figures
# -----------------------------------------------------------------------------

def apply_pai_style():
    pai_plt.rcParams.update({
        "figure.dpi": 140,
        "savefig.dpi": 300,
        "figure.figsize": (6, 6),

        # ---------------------------------------------------------------------
        # Font
        # ---------------------------------------------------------------------
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman", "CMU Serif", "DejaVu Serif"],
        "mathtext.fontset": "cm",
        "text.usetex": False,

        # ---------------------------------------------------------------------
        # Axes
        # ---------------------------------------------------------------------
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "axes.linewidth": 1.0,
        "axes.spines.top": False,
        "axes.spines.right": False,

        # ---------------------------------------------------------------------
        # Ticks
        # ---------------------------------------------------------------------
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 4,
        "ytick.major.size": 4,

        # ---------------------------------------------------------------------
        # Legend
        # ---------------------------------------------------------------------
        "legend.frameon": False,
        "legend.fontsize": 10,

        # ---------------------------------------------------------------------
        # Lines / Grid
        # ---------------------------------------------------------------------
        "lines.linewidth": 1.8,
        "grid.linewidth": 0.6,

        # ---------------------------------------------------------------------
        # Layout
        # ---------------------------------------------------------------------
        "figure.autolayout": False,
        "axes.grid": False,
    })


# -----------------------------------------------------------------------------
# AUTO-APPLY STYLE ON IMPORT
# -----------------------------------------------------------------------------

apply_pai_style()


# -----------------------------------------------------------------------------
# EXPORTS
# -----------------------------------------------------------------------------

__all__ = ["pai_plt", "apply_pai_style", "mpl"]