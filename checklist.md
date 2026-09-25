
# ConlangEngine Offline Desktop Checklist (PySide6 + Nuitka)

This checklist keeps the current React app, packages it for desktop, and disables online-only parts for offline use.

## 0) Safety first
- [ ] Make a backup copy of the repo
- [ ] Create a new branch if using Git:
  - `git checkout -b offline-pyside6`
- [ ] Confirm the app runs in the browser before desktop packaging:
  - `npm install`
  - `npm run build`

## 1) Install Python tools
- [ ] Create `requirements-desktop.txt`:
  ```txt
  PySide6
  PySide6-Essentials
  PySide6-WebEngine
  nuitka
  ```
- [ ] Install:
  - `python -m pip install -r requirements-desktop.txt`

## 2) Prepare the web app for local/offline packaging
- [ ] Open `vite.config.js`
- [ ] Add:
  ```js
  base: './',
  ```
  at the top of the exported config
- [ ] This helps asset URLs work when loaded from the local desktop app

## 3) Remove online-only UI dependency
- [ ] Open `src/main.jsx`
- [ ] Remove:
  ```js
  import { PayPalScriptProvider } from "@paypal/react-paypal-js";
  ```
- [ ] Remove the wrapping:
  ```jsx
  <PayPalScriptProvider ...>
     ...
  </PayPalScriptProvider>
  ```
- [ ] Keep only:
  ```jsx
  <BrowserRouter>
    <App />
  </BrowserRouter>
  ```
- [ ] Reason: PayPal is internet-dependent

## 4) Build the web app
- [ ] Run:
  ```bash
  npm install
  npm run build
  ```
- [ ] Confirm the app generates a `dist/` folder
- [ ] Confirm `dist/index.html` exists

## 5) Create the desktop launcher
- [ ] Create a new file at repo root:
  - `desktop_launcher.py`
- [ ] Use a PySide6 window with a `QWebEngineView`
- [ ] Start a local HTTP server serving the `dist/` folder
- [ ] Load the app with:
  - `http://127.0.0.1:<port>/`
- [ ] This avoids React Router and asset path issues
- [ ] This is the right approach for your current project structure (React app, not Python app)

## 6) Keep the app offline-safe
- [ ] Open `src/hooks/useAutoSync.jsx`
- [ ] Add a guard before any Supabase calls:
  ```js
  const isOfflineDesktop = import.meta.env.VITE_OFFLINE_DESKTOP === 'true';
  if (isOfflineDesktop) return;
  ```
- [ ] Create `.env.local`:
  ```env
  VITE_OFFLINE_DESKTOP=true
  ```
- [ ] Rebuild the app:
  - `npm run build`
- [ ] Reason: this disables cloud sync for desktop/offline mode

## 7) Optional: hide online features
- [ ] If needed, disable or hide:
  - Supabase sync buttons
  - cloud project/share UI
  - public viewer sharing button
  - PayPal UI
  - online semantic suggestions if you want a fully offline experience
- [ ] This is optional; the app can still work offline with those disabled

## 8) Create desktop build script
- [ ] Create `build_desktop.bat` (Windows)
- [ ] Include:
  ```bat
  @echo off
  setlocal

  echo [1/4] npm install
  call npm install
  if errorlevel 1 goto error

  echo [2/4] build web app
  call npm run build
  if errorlevel 1 goto error

  echo [3/4] install python deps
  python -m pip install -r requirements-desktop.txt
  if errorlevel 1 goto error

  echo [4/4] nuitka build
  python -m nuitka ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --include-data-dir=dist=dist ^
    --output-dir=build ^
    --output-filename=ConlangEngine.exe ^
    desktop_launcher.py

  if errorlevel 1 goto error

  echo Build complete
  pause
  exit /b 0

  :error
  echo Build failed
  pause
  exit /b 1
  ```
- [ ] This is the easiest repeatable build flow

## 9) Build executable with Nuitka
- [ ] Run:
  ```bash
  python -m nuitka --standalone --enable-plugin=pyside6 --include-data-dir=dist=dist --output-dir=build --output-filename=ConlangEngine.exe desktop_launcher.py
  ```
- [ ] Verify the output folder exists:
  - `build/`
- [ ] Run the built app from the generated folder
- [ ] Important: do not move just the `.exe`; keep the whole output folder together

## 10) Test the desktop version
- [ ] Launch the desktop app
- [ ] Verify:
  - [ ] app starts
  - [ ] home page loads
  - [ ] dictionary works
  - [ ] creation/editing works
  - [ ] local data persists
  - [ ] export/import works
  - [ ] app still works with no internet
- [ ] If something fails, check the terminal output from `python desktop_launcher.py`

## 11) Final offline compatibility check
- [ ] Confirm these are disabled or non-blocking:
  - [ ] Supabase sync
  - [ ] PayPal
  - [ ] public cloud sharing
  - [ ] online suggestions
- [ ] Confirm local saves still work:
  - [ ] browser localStorage
  - [ ] IndexedDB
  - [ ] JSON backup import/export

## 12) Notes about your repo
- [ ] You do NOT need to rewrite the app in Python
- [ ] You do NOT need to replace all JSX files
- [ ] You are packaging the already-working React app inside a desktop window
- [ ] This is the most practical and lowest-risk setup for your project

## 13) Recommended order
- [ ] Build web app
- [ ] Launch PySide6 desktop window
- [ ] Confirm functionality
- [ ] Disable online sync
- [ ] Package with Nuitka
- [ ] Test final executable

## 14) Done when
- [ ] `npm run build` succeeds
- [ ] `python desktop_launcher.py` launches from local folder
- [ ] the desktop app loads the built React app
- [ ] app works offline without internet
- [ ] Nuitka executable launches successfully
