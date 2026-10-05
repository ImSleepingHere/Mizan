# Push this release to GitHub

The package is a clean source folder with no preconfigured Git remote. It has not been committed or pushed automatically. GitHub will rebuild the website from source; the local ZIP also includes the built website.

## Existing repository (recommended for your existing Mizan project)

1. Back up uncommitted work in your current clone.
2. Copy this release's project contents into that clone, including dot folders/files: `.github`, `.gitattributes`, `.gitignore` and `.models` (only the shipped adapter/licence). Preserve the clone's `.git` directory. Do not copy databases or personal imports.
3. Inspect the changes and commit from the repository root:

```powershell
git status --short
git diff --stat
git add .
git diff --cached --stat
git commit -m "Add three-plan comparison and release readiness fixes"
git push
```

Review staged file names before committing. Setup output `frontend/dist`, `data`, `work`, `node_modules`, `.venv`, model runtime and base weights are ignored. Existing files already tracked by Git are not untracked by .gitignore: if your clone previously committed private files, remove those from tracking before pushing.

## New empty repository

Create an empty repository on GitHub, then in this folder:

```powershell
git init
git add .
git diff --cached --stat
git commit -m "MIZAN local hackathon release"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the placeholder URL with your own repository. Authenticate through Git's normal prompt. No force push is needed.

After pushing, inspect Actions → Verify MIZAN. The supplied workflow checks the backend and frontend on Windows, Python 3.12 and Node 24. A provided workflow is not proof of a hosted passing run until GitHub executes it. Preserve upstream model/font/library licences. The original project has no explicit project-wide open-source licence; this release does not invent licensing permission on behalf of the team.
