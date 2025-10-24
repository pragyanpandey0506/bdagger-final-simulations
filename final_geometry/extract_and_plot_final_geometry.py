#!/usr/bin/env python3
"""
Export parameters for final geometry and plot tapered d(n), h(n) profiles.

Behavior
- If final_dimensions.json exists in this folder, use it as the single source of truth.
- Otherwise, attempt to export parameters from a COMSOL .mph via the `mph` API.
- Always write final_dimensions.json (ensuring wg_Cell_w_1 = 1241[nm] and n_ext set).
- Write geometry_profile.csv and geometry_profile.png.
- If parameters cannot be obtained, write a placeholder PNG with an ERROR message and exit.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FormatStrFormatter


DEFAULT_MPH = Path('..') / '..' / 'bdagger2' / 'avoided_crossing' / 'final_transducer_simulations' / 'full_transducer_convergence_test' / 'full_transducer_final_mesh_2_1230.mph'
# Default path to the mirror unit cell MPH (relative to this script)
DEFAULT_MIRROR_MPH = (Path(__file__).resolve().parent / '..' / 'omc_unit_cell_final' / 'mech_unit_cell' / 'mech_symzsymy' / 'unit_mech_sym_mirror.mph').resolve()


def write_error_placeholder(out_png: Path, message: str) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.axis('off')
    ax.text(0.5, 0.6, 'ERROR', color='crimson', fontsize=28, ha='center', va='center', weight='bold')
    ax.text(0.5, 0.4, message, color='0.2', fontsize=12, ha='center', va='center', wrap=True)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def str_to_float_maybe_unit(s: str) -> float:
    t = s.strip()
    if '[' in t:
        t = t.split('[')[0].strip()
    return float(t)


def compute_profile(params: Dict[str, str]) -> pd.DataFrame:
    """Compute d(n), h(n) for n in [-N..N] with side-specific targets if available."""
    def get_any(keys):
        for k in keys:
            if k in params:
                return str_to_float_maybe_unit(params[k])
        raise KeyError(f"Missing required parameter among {keys}")

    N = int(round(get_any(['n_ext', 'N', 'n', 'N_unitcell'])))
    d0 = get_any(['d0'])
    h0 = get_any(['h0'])

    # Side-specific targets, with generic fallbacks
    dN_left = str_to_float_maybe_unit(params['d17_mir']) if 'd17_mir' in params else None
    dN_right = str_to_float_maybe_unit(params['d17_wg']) if 'd17_wg' in params else None
    hN_left = str_to_float_maybe_unit(params['h17_mir']) if 'h17_mir' in params else None
    hN_right = str_to_float_maybe_unit(params['h17_wg']) if 'h17_wg' in params else None
    if dN_left is None or dN_right is None:
        dN = get_any(['d17', 'dN', 'd_ext'])
        dN_left = dN if dN_left is None else dN_left
        dN_right = dN if dN_right is None else dN_right
    if hN_left is None or hN_right is None:
        hN = get_any(['h17', 'hN', 'h_ext'])
        hN_left = hN if hN_left is None else hN_left
        hN_right = hN if hN_right is None else hN_right

    delx = get_any(['delx', 'delta_x', 'dx'])
    M = get_any(['M', 'm'])

    idx = np.arange(-N, N + 1)
    def taper(v0: float, vN_target: float, n_abs: float) -> float:
        return vN_target - (vN_target - v0) * (2.0 ** (-(n_abs / delx) ** M))

    d_arr = np.array([d0 if n == 0 else taper(d0, dN_left if n < 0 else dN_right, abs(n)) for n in idx], dtype=float)
    h_arr = np.array([h0 if n == 0 else taper(h0, hN_left if n < 0 else hN_right, abs(n)) for n in idx], dtype=float)
    return pd.DataFrame({'index': idx, 'd': d_arr, 'h': h_arr})


def plot_profile(df: pd.DataFrame, out_png: Path) -> None:
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.plot(df['index'], df['d'], 'o-', label='d(n)')
    ax.plot(df['index'], df['h'], 's-', label='h(n)')
    ax.set_xlabel('Cell index n')
    ax.set_ylabel('Parameter value (model units)')
    ax.set_title('Tapered geometry profile (d and h vs index)')
    ax.legend(loc='best', frameon=True)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
    ax.grid(True, which='major', alpha=0.3)
    ax.grid(True, which='minor', alpha=0.15)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png)
    plt.close(fig)


def export_params_via_mph(mph_path: Path) -> Dict[str, str]:
    try:
        import mph  # type: ignore
    except Exception as e:
        raise RuntimeError("The 'mph' package is required. Install with 'pip install mph' and ensure COMSOL server is reachable.") from e

    client = mph.start()
    try:
        model = client.load(str(mph_path))
        params: Dict[str, str] = {}
        try:
            p = model.parameters()  # type: ignore[attr-defined]
            if isinstance(p, dict) and p:
                params = {str(k): str(v) for k, v in p.items()}
        except Exception:
            pass
        if not params:
            try:
                jparam = model.java.param()
                tags = None
                for m in ('tags', 'getTags'):
                    if hasattr(jparam, m):
                        tags = getattr(jparam, m)()
                        break
                if tags is None:
                    raise RuntimeError('Cannot enumerate parameter tags (Java API).')
                for t in list(tags):
                    params[str(t)] = str(jparam.get(str(t)))
            except Exception as e:
                raise RuntimeError(f'Failed to collect parameters from {mph_path}: {e}')
        return params
    finally:
        try:
            client.clear()
        except Exception:
            pass


def print_params(mph_path: Path) -> int:
    """Load an MPH model and print all parameter key=val pairs sorted by name."""
    try:
        params = export_params_via_mph(mph_path)
    except Exception as e:
        print(f"Failed to read parameters from {mph_path}: {e}")
        return 2
    for k, v in sorted(params.items(), key=lambda kv: kv[0].lower()):
        print(f"{k} = {v}")
    return 0


def write_final_dimensions(params: Dict[str, str], out_json: Path) -> Path:
    rows = sorted(params.items(), key=lambda kv: kv[0].lower())
    out_json.write_text(json.dumps(dict(rows), indent=2), encoding='utf-8')
    return out_json


def main() -> None:
    ap = argparse.ArgumentParser(description='Export parameters and plot tapered geometry.')
    ap.add_argument('mph', nargs='?', default=str(DEFAULT_MPH), help='Path to .mph model (ignored if final_dimensions.json exists)')
    ap.add_argument('--set-wg-Cell-w-1', dest='wg_cell_w_1', default='1241[nm]', help='Override for wg_Cell_w_1 in saved JSON')
    ap.add_argument('--out-json', default='final_dimensions.json', help='Output JSON filename')
    # Optional CLI overrides
    ap.add_argument('--n_ext', type=int)
    ap.add_argument('--d0', type=float)
    ap.add_argument('--h0', type=float)
    ap.add_argument('--delx', type=float)
    ap.add_argument('--M', type=float)
    # Print-only mode for mirror unit cell params
    ap.add_argument('--print-params', action='store_true', help='Print parameters from an MPH and exit')
    ap.add_argument('--mph-path', default=str(DEFAULT_MIRROR_MPH), help='Path to .mph for --print-params (defaults to mirror unit cell)')
    args = ap.parse_args()

    # Print-only early exit
    if args.print_params:
        code = print_params(Path(args.mph_path))
        raise SystemExit(code)

    # Load parameters: prefer local JSON
    params: Dict[str, str] | None = None
    local_json = Path('final_dimensions.json')
    if local_json.exists():
        try:
            params = json.loads(local_json.read_text(encoding='utf-8'))
            print(f"Loaded parameters from {local_json}")
        except Exception as e:
            print(f"Failed to read {local_json}: {e}")
            params = None
    if params is None:
        try:
            params = export_params_via_mph(Path(args.mph))
        except Exception as e:
            write_error_placeholder(Path('geometry_profile.png'), f"Parameter export failed: {e}")
            print(f"Parameter export failed: {e}")
            return

    # Apply overrides and ensure critical keys
    modified = dict(params)
    # wg_Cell_w_1
    key_match = next((k for k in modified.keys() if k.lower().replace('-', '_') == 'wg_cell_w_1'), 'wg_Cell_w_1')
    modified[key_match] = args.wg_cell_w_1
    # n_ext: from JSON/CLI or default to 17
    N = args.n_ext if args.n_ext is not None else None
    if N is None:
        for k in ('n_ext', 'N', 'n', 'N_unitcell'):
            if k in modified:
                try:
                    N = int(round(str_to_float_maybe_unit(str(modified[k]))))
                    break
                except Exception:
                    pass
    if N is None:
        print('Parameter n_ext not found; defaulting to N=17 for plotting.')
        N = 17
    modified['n_ext'] = str(N)

    # Ensure basics for profile (allow CLI overrides)
    for name, cli_val in (('d0', args.d0), ('h0', args.h0), ('delx', args.delx), ('M', args.M)):
        if cli_val is not None:
            modified[name] = str(cli_val)

    # Save authoritative JSON
    final_json = write_final_dimensions(modified, Path(args.out_json))
    print(f"Wrote {final_json}")

    # Build profile input and plot
    prof = compute_profile(modified)
    prof_csv = Path('geometry_profile.csv')
    prof_png = Path('geometry_profile.png')
    try:
        prof.to_csv(prof_csv, index=False)
        print(f'Wrote {prof_csv} (index,d,h)')
        plot_profile(prof, prof_png)
        print(f'Wrote {prof_png}')
    except Exception as e:
        write_error_placeholder(prof_png, f"Plot failed: {e}")
        print(f"Plot failed: {e}")


if __name__ == '__main__':
    main()
