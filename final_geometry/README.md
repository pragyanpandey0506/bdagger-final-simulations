Final geometry extraction and profiles for the full transducer/OMC.

Purpose
- This folder is the single source of truth for device geometry across the project. Downstream scripts and notebooks should read parameters from here.

What this does
- Exports parameters from a selected `.mph` model when COMSOL is available (via the `mph` Python API). If COMSOL is unavailable, place or edit `final_dimensions.json` manually.
- Saves only the modified JSON named `final_dimensions.json` (no other param files). This JSON includes `wg_Cell_w_1 = 1241[nm]` and all geometry controls.
- Computes the tapered unit‑cell profiles for `d(n)` and `h(n)` over cell index `n = -N..N` using the SI formula:

    v(n) = v_N − (v_N − v_0) · 2^(-( |n| / δx )^M)

  where `v ∈ {d, h}`, `N = n_ext`, and `δx = delx`.

Left/Right convention (important)
- `d17_mir` and `h17_mir` correspond to the left side of the OMC (negative indices, n = −N; mirror side).
- `d17_wg` and `h17_wg` correspond to the right side of the OMC (positive indices, n = +N; waveguide side; “wg”).
- The profile builder uses side‑specific targets: for n < 0 it tapers from `v0` to the mirror target; for n > 0 it tapers from `v0` to the waveguide target; at n = 0 it returns `v0`.

Files
- `extract_and_plot_final_geometry.py` — main script (reads local JSON if present; otherwise exports from `.mph`).
- `final_dimensions.json` — authoritative parameter set for all tools.
- `geometry_profile.csv` — table with columns: `index,d,h` for `n = -N..N`.
- `geometry_profile.png` — plot of `d(n)` and `h(n)` for `n = -N..N`.
  - If parameter export fails and no JSON is present, a placeholder PNG with an ERROR message is produced and no JSON/CSV are written.

Usage
- Preferred (JSON already present):
  - `cd bdagger-project/bdagger_final_simulations/final_geometry`
  - `python extract_and_plot_final_geometry.py`
- Export from `.mph` (requires COMSOL):
  - `pip install mph numpy pandas matplotlib`
  - `python extract_and_plot_final_geometry.py <path_to_mph>`

Notes
- Keep this JSON synchronized with any full‑device and unit‑cell models. If a change is made elsewhere, update this JSON and re‑generate the profile here so all downstream analyses are consistent.
