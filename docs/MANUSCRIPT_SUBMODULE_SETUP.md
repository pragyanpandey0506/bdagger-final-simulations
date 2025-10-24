# Manuscript Submodule Setup

This project expects the manuscript to live as a Git submodule at `docs/bdagger-manuscript-prep-2025`.

Steps
1) Create the GitHub repo (empty): `pragyanpandey0506/bdagger-manuscript-prep-2025`.
2) Add a deploy key dedicated to the manuscript repo (Allow write access).
3) Add the submodule to this repo and push.

Deploy key (PowerShell)
- $ssh = Join-Path $HOME '.ssh'
- New-Item -ItemType Directory -Force -Path $ssh | Out-Null
- $key = Join-Path $ssh 'id_ed25519_bdagger_manuscript_2025'
- ssh-keygen -t ed25519 -C 'deploy-key-bdagger_manuscript_2025' -f $key
- Get-Content ($key + '.pub')  # paste into GitHub → Repo → Settings → Deploy Keys (Allow write)

Optional SSH alias (append to `~/.ssh/config`)
- Host github-bdagger-manuscript
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_bdagger_manuscript_2025
  IdentitiesOnly yes

Add the submodule (from repo root `bdagger_final_simulations`)
- git submodule add -b main git@github-bdagger-manuscript:pragyanpandey0506/bdagger-manuscript-prep-2025.git docs/bdagger-manuscript-prep-2025
- git commit -m "Add manuscript submodule"
- git push

Overleaf sync
- Use Overleaf↔GitHub integration to connect the manuscript repo.
- Alternatively, add Overleaf’s Git remote inside the submodule as a second remote.
