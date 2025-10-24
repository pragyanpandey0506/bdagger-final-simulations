# B‑Dagger Final Simulations

This workspace groups final OMC (optomechanical crystal) artifacts for unit cells, band simulations, electromechanics, full OMC devices, and full transducers.

Folders
- `omc_unit_cell_final/` — Final unit‑cell models and references (optical and mechanical; symzsymy and allsym variants), each with entries for defect cell, mirror external cell, and waveguide external cell. Entries are `.txt` pointers to source `.mph` models or a note if not found.
- `omc_band_sim_final/` — Band‑simulation setup reduced to two configurations (mirror and waveguide) for both mechanics and optics. Includes placeholder PNG outputs and a combined sweep figure.
- `electromechanics/` — Placeholder for EMC model and `g_em` vs frequency outputs.
- `full_omc/` — Full device models; includes pointers to OMC model, placeholder figures for `g_om` vs frequency and optical Q, and a pointer to a circle‑PML Q‑factor study.
- `full_transducer/` — Final transducer model pointer plus subfolders for avoided‑crossing and EMC period‑number analysis.

Notes
- `.txt` placeholders name files as they would appear if `.mph` were copied. They contain the source path (if found) or the message "could not find the relevant file".
- Placeholder PNGs are tiny (1×1) so pipelines have targets; regenerate with your analysis notebooks to produce real figures.

