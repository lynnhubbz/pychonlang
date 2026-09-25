# ConlangEngine Offline Desktop

This project wraps the React/Vite ConlangEngine application in a PySide6 desktop shell. The web app remains a Git submodule; it is not rewritten in Python.

## Layout

```text
YourApp/
├─ .gitmodules
├─ src/
│  ├─ __init__.py
│  ├─ desktop/
│  │  ├─ __init__.py
│  │  ├─ main.py
│  │  └─ local_server.py
│  └─ ConlangEngine/       <- Git submodule
├─ scripts/
│  └─ build_web.py
├─ requirements.txt
└─ pyproject.toml
```

`src/desktop` contains the Python wrapper. `src/ConlangEngine` contains the React application.

## Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Initialize the web submodule if needed:

```powershell
git submodule update --init --recursive
```

## Build and run

Run these commands from the repository root:

```powershell
python scripts/build_web.py
python -m src.desktop.main
```

The build helper runs `npm ci` and `npm run build` inside `src/ConlangEngine`. It also sets `VITE_OFFLINE_DESKTOP=true`, so the desktop bundle uses the offline Supabase facade.

The launcher serves `src/ConlangEngine/dist` through a server bound only to `127.0.0.1`. Browser storage is persisted under:

```text
%USERPROFILE%\.conlang-engine\storage
```

Downloads such as Workspace JSON and Obsidian Markdown are handled by a native save dialog.

## Nuitka packaging

Nuitka is already supported through the active virtual environment:

```powershell
.venv\Scripts\python.exe -m nuitka --version
```

Build a standalone package:

```powershell
.venv\Scripts\python.exe -m nuitka `
  --standalone `
  --enable-plugin=pyside6 `
  --include-data-dir=src/ConlangEngine/dist=web `
  --include-package=src.desktop `
  --output-dir=build `
  src/desktop/main.py
```

The executable is created under `build/main.dist/`. Keep the entire directory together. The bundled web files are placed at `build/main.dist/web/`.

Try one-file mode only after standalone mode works:

```powershell
.venv\Scripts\python.exe -m nuitka `
  --onefile `
  --enable-plugin=pyside6 `
  --include-data-dir=src/ConlangEngine/dist=web `
  --include-package=src.desktop `
  --output-dir=build `
  src/desktop/main.py
```

## Submodule workflow

The submodule should point to your fork. Commit web changes inside the submodule first, push them to your fork, then commit the updated submodule pointer in the parent repository:

```powershell
Set-Location src\ConlangEngine
git add src
git commit -m "Update offline web support"
git push origin main-app
Set-Location ..\..
git add src\ConlangEngine
git commit -m "Update ConlangEngine submodule"
```

Do not commit generated files:

```text
.venv/
build/
src/ConlangEngine/node_modules/
src/ConlangEngine/dist/
```

## Offline limitations

Local dictionary editing, grammar editing, project storage, JSON export/import, and browser persistence work locally. Cloud login, cloud sync, public sharing, online semantic suggestions, Azure TTS, PayPal, and remote backup services remain unavailable in offline mode.
