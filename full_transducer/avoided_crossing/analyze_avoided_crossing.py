#!/usr/bin/env python3
"""
Read avoided_crossing_data.csv and generate clean Matplotlib plots.

Outputs (in the same folder by default):
- avoided_crossing.png      : EM and OM modes vs transducer period with annotated min splitting
- avoided_crossing_split.png: Splitting Δf vs period (in MHz)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FormatStrFormatter


def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Normalize column names to be robust to minor wording differences
    cols = {c.lower(): c for c in df.columns}
    # Find columns by keywords
    def find_col(keyword: str):
        for k, orig in cols.items():
            if keyword in k:
                return orig
        raise KeyError(f"Column containing '{keyword}' not found in CSV headers: {list(df.columns)}")

    period_col = find_col('period')
    em_col = find_col('electromechanical')
    om_col = find_col('optomechanical')
    df = df.rename(columns={period_col: 'period_nm', em_col: 'em_ghz', om_col: 'om_ghz'})
    df = df.sort_values('period_nm').reset_index(drop=True)
    return df


def analyze_and_plot(df: pd.DataFrame, out_png: Path, out_split_png: Path | None = None):
    p = df['period_nm'].to_numpy()
    em = df['em_ghz'].to_numpy()
    om = df['om_ghz'].to_numpy()
    # Splitting
    split_ghz = np.abs(em - om)
    i_min = int(np.argmin(split_ghz))
    p_min = float(p[i_min])
    split_min_ghz = float(split_ghz[i_min])
    split_min_mhz = split_min_ghz * 1000.0
    g_mhz = split_min_mhz / 2.0  # rough estimate: 2g ≈ min splitting

    # --- Main plot: EM and OM vs period ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.plot(p, em, 'o-', color='#d62728', label='Electromechanical mode')
    ax.plot(p, om, 's-', color='#1f77b4', label='Optomechanical mode')
    ax.set_xlabel('Transducer period (nm)')
    ax.set_ylabel('Frequency (GHz)')
    ax.set_title('Avoided crossing: mode frequencies vs period')
    leg = ax.legend(loc='best', frameon=True)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
    ax.grid(True, which='major', alpha=0.3)
    ax.grid(True, which='minor', alpha=0.15)

    # Annotate minimum splitting — place textbox just below legend to avoid covering data
    y_mid = 0.5 * (em[i_min] + om[i_min])
    ax.vlines(p_min, om[i_min], em[i_min], colors='k', linestyles='dashed', alpha=0.6)
    # Compute a textbox anchor just below the legend in axes coordinates
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = leg.get_window_extent(renderer)
    to_axes = ax.transAxes.inverted()
    (x0, y0) = to_axes.transform((bbox.x0, bbox.y0))
    (x1, y1) = to_axes.transform((bbox.x1, bbox.y1))
    tx = min(0.98, max(0.02, (x0 + x1) / 2.0))
    ty = max(0.02, y0 - 0.05)
    ax.annotate(
        f"min Δf ≈ {split_min_mhz:.3f} MHz\n(g ≈ {g_mhz:.3f} MHz)\nat {p_min:.0f} nm",
        xy=(p_min, y_mid), xycoords='data',
        xytext=(tx, ty), textcoords=ax.transAxes, fontsize=9,
        bbox=dict(boxstyle='round', fc='white', ec='0.7'), ha='center', va='top',
        arrowprops=dict(arrowstyle='->', color='0.4', lw=1)
    )

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)

    # --- Secondary plot: splitting vs period (MHz) ---
    if out_split_png is not None:
        fig2, ax2 = plt.subplots(figsize=(9, 3.8), dpi=150)
        ax2.plot(p, split_ghz * 1000.0, 'o-', color='#2ca02c')
        ax2.set_xlabel('Transducer period (nm)')
        ax2.set_ylabel('Δf (MHz)')
        ax2.set_title('Splitting vs period')
        ax2.xaxis.set_minor_locator(AutoMinorLocator())
        ax2.yaxis.set_minor_locator(AutoMinorLocator())
        ax2.grid(True, which='major', alpha=0.3)
        ax2.grid(True, which='minor', alpha=0.15)
        ax2.axvline(p_min, color='0.3', ls='--', lw=1)
        ax2.annotate(
            f"min at {p_min:.0f} nm\nΔf ≈ {split_min_mhz:.3f} MHz",
            xy=(p_min, split_min_mhz), xytext=(12, 10), textcoords='offset points', fontsize=9,
            bbox=dict(boxstyle='round', fc='white', ec='0.7'), ha='left', va='center',
            arrowprops=dict(arrowstyle='->', color='0.4', lw=1)
        )
        fig2.tight_layout()
        fig2.savefig(out_split_png)
        plt.close(fig2)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    csv_path = Path(argv[0]) if argv else Path('avoided_crossing_data.csv')
    out_png = Path(argv[1]) if len(argv) > 1 else Path('avoided_crossing.png')
    out_split = Path(argv[2]) if len(argv) > 2 else Path('avoided_crossing_split.png')
    df = load_data(csv_path)
    analyze_and_plot(df, out_png, out_split)
    print(f"Wrote {out_png} and {out_split} (standard Matplotlib plots)")


if __name__ == '__main__':
    main()
