# ConlangEngine Offline Desktop Checklist

## Layout

- [x] Keep the React app in `src/ConlangEngine/`
- [x] Keep the PySide6 wrapper in `src/desktop/`
- [x] Keep the build helper in `scripts/build_web.py`
- [x] Add `src/__init__.py` so `src.desktop` is importable

## Development

- [x] Initialize the ConlangEngine Git submodule
- [x] Build with `python scripts/build_web.py`
- [x] Run with `python -m src.desktop.main`
- [x] Serve the web app through localhost only
- [x] Persist WebEngine data locally
- [x] Handle browser exports with a native save dialog

## Offline behavior

- [x] Use the offline Supabase facade
- [ ] Disable or replace semantic API requests
- [ ] Disable or replace Azure TTS
- [ ] Disable or replace PayPal features
- [ ] Disable remote backup services
- [ ] Test the app with the network disconnected

## Export and persistence

- [ ] Create a local project
- [ ] Add dictionary words and grammar rules
- [ ] Close and reopen the desktop app
- [ ] Confirm local data persists
- [ ] Export a Workspace JSON file
- [ ] Export an All Workspaces JSON file
- [ ] Export Obsidian Markdown
- [ ] Import a Workspace JSON file

## Packaging

- [x] Confirm Nuitka is installed
- [ ] Build standalone mode
- [ ] Run `build/main.dist/main.exe` outside the source tree
- [ ] Confirm `build/main.dist/web/index.html` is present
- [ ] Test one-file mode only after standalone mode works

## Submodule release

- [ ] Commit web changes inside `src/ConlangEngine`
- [ ] Push the submodule branch to the fork
- [ ] Commit the updated submodule pointer in the parent repository
- [ ] Keep generated `node_modules`, `dist`, `.venv`, and `build` files ignored
