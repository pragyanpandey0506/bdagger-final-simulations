# bdagger-manuscript-prep-2025 (submodule setup)

This directory will be a Git submodule pointing to your manuscript repository on GitHub.

Steps (once you have an empty GitHub repo created)
1) Add a deploy key for the manuscript repo (new key dedicated to this repo):
   - PowerShell (recommended):
     - `$ssh = Join-Path $HOME '.ssh'`
     - `New-Item -ItemType Directory -Force -Path $ssh | Out-Null`
     - `$key = Join-Path $ssh 'id_ed25519_bdagger_manuscript_2025'`
     - `ssh-keygen -t ed25519 -C 'deploy-key-bdagger_manuscript_2025' -f $key`
     - `Get-Content ($key + '.pub')`  # paste this into GitHub → Repo → Settings → Deploy Keys → Add key (Allow write)
   - Optional SSH config alias (append to `~/.ssh/config`):
     
     Host github-bdagger-manuscript
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_ed25519_bdagger_manuscript_2025
       IdentitiesOnly yes
     

2) Add the submodule to this repo (from the root of `bdagger_final_simulations`):
   - Replace `OWNER` with your username/org (e.g., `pragyanpandey0506`).
   - `git submodule add -b main git@github-bdagger-manuscript:OWNER/bdagger-manuscript-prep-2025.git docs/bdagger-manuscript-prep-2025`
   - `git commit -m "Add manuscript submodule" && git push`

3) Using the submodule
   - Update submodules: `git submodule update --init --recursive`
   - Work inside: `cd docs/bdagger-manuscript-prep-2025`
   - Commit and push manuscript changes from within the submodule directory.

4) Overleaf sync options
   - Use Overleaf’s GitHub integration to link `bdagger-manuscript-prep-2025` directly to Overleaf (recommended).
   - Or use Overleaf’s direct Git remote for the Overleaf project and add it as a second remote in the submodule.

Notes
- This parent repo ignores large COMSOL binaries; the manuscript submodule should only have text sources (LaTeX, images, BibTeX). Consider Git LFS for large figures.
