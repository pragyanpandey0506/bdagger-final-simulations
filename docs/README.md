# docs

This folder holds documentation and manuscript resources for the project.

- `literature/` — PDFs, notes, and a shared `refs.bib` bibliography.
- `bdagger-manuscript-prep-2025/` — manuscript (to be linked as a Git submodule).

Recommended flow
- Keep canonical LaTeX sources inside the manuscript submodule.
- Store reference PDFs and a single shared `refs.bib` in `literature/`.
- If syncing with Overleaf, connect the manuscript repo to Overleaf’s Git integration (or Overleaf↔GitHub integration) so pushes keep both in sync.

See `bdagger-manuscript-prep-2025/SETUP.md` for submodule + deploy key setup.
