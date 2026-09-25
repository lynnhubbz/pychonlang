## Best approach: **do not rewrite the React app in PySide6**

Your repository is already a React/Vite application. The easiest and safest way to make it an offline desktop app is:

1. Keep the existing React UI.
2. Build it with Vite.
3. Open the built files inside a PySide6 `QWebEngineView`.
4. Package the Python launcher and the built `dist/` folder with Nuitka.

This gives you a desktop application without rewriting approximately 90% JavaScript into Python.

The repository already says that local data uses `localStorage` and IndexedDB, so most of the app is already designed for offline use. However, cloud sync, PayPal, Supabase, and some online word suggestions will not work without internet.

---

# What you will create and modify

You will:

```text
ConlangEngine/
├── src/
│   └── main.jsx                 MODIFY
├── desktop_launcher.py          CREATE
├── requirements-desktop.txt     CREATE
├── build_desktop.bat            CREATE, Windows only
├── package.json                 MODIFY
└── dist/                        CREATED automatically by npm run build
```

You do **not** need to delete the React source code.

You do **not** need to convert every `.jsx` file to Python.

---

# Part 1 — Make a backup first

Before changing anything:

```bash
git checkout -b offline-pyside6
```

Or, if you do not use Git:

1. Copy the entire `ConlangEngine` folder.
2. Rename the copy to:

```text
ConlangEngine-offline-backup
```

Work in the original repository only after you have a backup.

---

# Part 2 — Install Python dependencies

Open a terminal inside the repository folder.

Create a new file at the repository root:

## `requirements-desktop.txt`

```text
PySide6
PySide6-Essentials
PySide6-WebEngine
```

Install them:

```bash
python -m pip install -r requirements-desktop.txt
```

If `PySide6-WebEngine` gives an error, try:

```bash
python -m pip install PySide6
```

Then test:

```bash
python -c "from PySide6.QtWebEngineWidgets import QWebEngineView; print('PySide6 WebEngine works')"
```

You should see:

```text
PySide6 WebEngine works
```

If you do not see that, do not continue to Nuitka yet.

---

# Part 3 — Remove PayPal from the desktop build

Your current `src/main.jsx` imports PayPal:

```javascript
import { PayPalScriptProvider } from "@paypal/react-paypal-js";
```

PayPal is online-only and can cause unnecessary network requests in the desktop version.

Open:

```text
src/main.jsx
```

Replace the entire file with this:

## `src/main.jsx`

```javascript
import './index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { BrowserRouter } from 'react-router-dom'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

### What changed?

You removed:

```javascript
import { PayPalScriptProvider } from "@paypal/react-paypal-js";
```

You also removed:

```javascript
<PayPalScriptProvider>
```

and:

```javascript
</PayPalScriptProvider>
```

The rest of the app remains unchanged.

---

# Part 4 — Make Vite produce desktop-friendly files

Open:

```text
vite.config.js
```

Find this section:

```javascript
export default defineConfig({
```

Change it to:

```javascript
export default defineConfig({
  base: './',
```

The beginning of your file should look like this:

## `vite.config.js`

```javascript
import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from 'vite-plugin-pwa';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  base: './',

  plugins: [
    react(),
    tailwindcss(),

    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'pwa-512x512.png'],
      manifest: {
        name: 'ConlangEngine',
        short_name: 'ConlangEngine',
        description: 'Advanced Conlang Dictionary and App',
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      }
    })
  ],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    watch: {
      usePolling: true
    }
  }
});
```

The important new line is:

```javascript
base: './',
```

This makes asset paths work better when the application is packaged.

---

# Part 5 — Build the React application

Before creating the PySide6 launcher, test the normal web build.

Run:

```bash
npm install
```

Then:

```bash
npm run build
```

You should now have:

```text
dist/
├── assets/
├── index.html
├── pwa-192x192.png
├── pwa-512x512.png
└── ...
```

Do not manually edit anything inside `dist/`.

The `dist/` folder is generated by Vite.

---

# Part 6 — Test the built app locally

Do not open `dist/index.html` by double-clicking it yet.

Instead, start Vite's preview server:

```bash
npm run preview
```

You should see an address similar to:

```text
http://localhost:4173
```

Open it in your browser.

Check:

- Home page opens.
- Navigation works.
- Dictionary works.
- You can create a word.
- Data remains after refreshing.
- Export and import work.

If the web version does not work, the PySide6 version will not work yet either.

Press:

```text
Ctrl+C
```

to stop the preview server.

---

# Part 7 — Create the PySide6 launcher

At the root of the repository, create a new file:

```text
desktop_launcher.py
```

Paste this into it:

## `desktop_launcher.py`

```python
import os
import sys
import socket
import threading
import mimetypes
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

from PySide6.QtCore import QUrl, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView


def get_application_folder() -> Path:
    """
    Get the folder containing the executable or Python script.
    Works both during development and after Nuitka packaging.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def find_dist_folder() -> Path:
    """
    Find the Vite-generated dist folder.
    """
    app_folder = get_application_folder()

    possible_locations = [
        app_folder / "dist",
        app_folder / "resources" / "dist",
        Path.cwd() / "dist",
    ]

    for location in possible_locations:
        if location.exists() and (location / "index.html").exists():
            return location

    raise FileNotFoundError(
        "Could not find the dist folder. Run 'npm run build' first."
    )


def get_free_port() -> int:
    """
    Ask the operating system for an unused local port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class LocalFileHandler(SimpleHTTPRequestHandler):
    """
    Serves the Vite dist folder locally.

    React Router needs this fallback so that routes such as
    /lexicon and /settings still load correctly.
    """

    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        requested_path = self.translate_path(self.path)

        if not os.path.exists(requested_path):
            self.path = "/index.html"

        return super().do_GET()

    def log_message(self, format, *args):
        """
        Silence HTTP request logs in the terminal.
        """
        pass


class DesktopWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(
        self,
        level,
        message,
        line_number,
        source_id,
    ):
        """
        Print JavaScript errors while debugging.
        """
        print(
            f"[JavaScript] {message} "
            f"(line {line_number}, source: {source_id})"
        )


class MainWindow(QMainWindow):
    def __init__(self, app_url: str):
        super().__init__()

        self.setWindowTitle("ConlangEngine")
        self.resize(1400, 900)
        self.setMinimumSize(QSize(900, 600))

        self.browser = QWebEngineView()
        self.browser.setPage(DesktopWebPage(self.browser))
        self.browser.setUrl(QUrl(app_url))

        self.setCentralWidget(self.browser)


def start_local_server(dist_folder: Path, port: int):
    handler = lambda *args, **kwargs: LocalFileHandler(
        *args,
        directory=str(dist_folder),
        **kwargs,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", port),
        handler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    return server


def main():
    dist_folder = find_dist_folder()
    port = get_free_port()

    server = start_local_server(dist_folder, port)

    app = QApplication(sys.argv)
    app.setApplicationName("ConlangEngine")
    app.setOrganizationName("ConlangEngine")

    window = MainWindow(f"http://127.0.0.1:{port}/")
    window.show()

    exit_code = app.exec()

    server.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

---

# Why this launcher uses a local web server

You might wonder why it does not simply open:

```text
dist/index.html
```

The reason is React Router.

Your application uses routes such as:

```text
/lexicon
/settings
/generator
/wiki
```

A local `file://` URL can cause problems with:

- React Router
- JavaScript modules
- IndexedDB
- localStorage
- asset loading
- route refreshes

The Python launcher starts a server on:

```text
127.0.0.1
```

This is still offline. It does not require the internet.

It only serves files from your own computer.

---

# Part 8 — Run the PySide6 version

Make sure you already ran:

```bash
npm run build
```

Then run:

```bash
python desktop_launcher.py
```

The desktop window should open.

Test these things:

1. Close the window.
2. Open it again.
3. Check whether your data remains.
4. Create a dictionary entry.
5. Navigate to `/lexicon`.
6. Navigate to `/settings`.
7. Export a backup.
8. Import a backup.

If the application does not start, run it from the terminal so you can see the error:

```bash
python desktop_launcher.py
```

Do not double-click it until it works from the terminal.

---

# Part 9 — Offline features versus online features

Your repository includes online services.

## These parts are online-only

### Supabase

The repository contains:

```javascript
src/utils/supabaseClient.js
```

It connects to Supabase using:

```javascript
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
```

This affects:

- Cloud sync
- User login
- Cloud project storage
- Public project sharing
- Version history stored in Supabase

These cannot work without internet unless you replace Supabase with a local database.

### PayPal

PayPal requires internet and should remain disabled in the desktop build.

### Datamuse

The semantic tools use requests like:

```javascript
fetch(...)
```

These will not work offline.

They affect features such as:

- Synonym suggestions
- Word families
- Antonyms
- Rhymes
- Modifiers
- Some semantic exploration tools

The rest of the local application can still work.

---

# Part 10 — Make offline mode explicit

Your current app uses `useAutoSync`, which tries to communicate with Supabase.

You should disable that hook for the offline desktop version.

Open:

```text
src/App.jsx
```

Find this import:

```javascript
import { useAutoSync } from './hooks/useAutoSync.jsx';
```

Replace it with:

```javascript
const OFFLINE_DESKTOP = true;
```

Then find:

```javascript
useAutoSync();
```

Replace it with:

```javascript
if (!OFFLINE_DESKTOP) {
  useAutoSync();
}
```

However, you also need to remove the import because the hook itself may initialize online services.

The top of `App.jsx` should look approximately like this:

```javascript
import React, { useState, useMemo, Suspense, lazy } from 'react';
import Header from './components/Layout/Header/Header.jsx';
import { useConfigStore } from './store/useConfigStore.jsx';
import './index.css';
import NavBar from './components/Layout/NavBar/Navbar.jsx';
import { Routes, Route, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useThemeInjector } from './hooks/useThemeInjector.jsx';
import { useFontInjector } from './utils/useFontInjector.jsx';
import { useGlobalHotkeys } from './hooks/useGlobalHotkeys.jsx';
import { useBackupManager } from './hooks/useBackupManager.jsx';
import SyncConflictManager from './components/pages/home/SyncConflictManager.jsx';
import Footer from './components/Layout/Footer/Footer.jsx';
import FloatingKeyboard from './components/UI/FloatingKeyboard/FloatingKeyboard.jsx';
import FloatingBackground from './components/pages/home/FloatingBackground.jsx';
import PWAInstallPrompt from './components/UI/PWAInstallPrompt/PWAInstallPrompt.jsx';
import CommandPalette from './components/UI/CommandPalette/CommandPalette.jsx';
import PageSkeleton from './components/UI/PageSkeleton/PageSkeleton.jsx';
import { AnimatePresence, motion } from 'framer-motion';
import { Toaster } from 'react-hot-toast';

const OFFLINE_DESKTOP = true;
```

Then find this line:

```javascript
useAutoSync();
```

Replace it with:

```javascript
if (!OFFLINE_DESKTOP) {
  // Cloud sync is intentionally disabled in the offline desktop build.
}
```

You may also want to hide cloud-related buttons later, but first get the desktop version working.

---

# Important React hook warning

Do not put a conditional hook like this in your code:

```javascript
if (!OFFLINE_DESKTOP) {
  useAutoSync();
}
```

React hooks should not be conditionally called.

Instead, the safer method is:

1. Keep the hook import.
2. Modify the hook itself so it immediately returns in offline mode.

Open:

```text
src/hooks/useAutoSync.jsx
```

At the top of the main hook function, add an offline check.

The exact function name may differ, but it will look similar to:

```javascript
export function useAutoSync() {
```

Change it to something like:

```javascript
export function useAutoSync() {
  const offlineDesktop =
    import.meta.env.VITE_OFFLINE_DESKTOP === 'true';

  if (offlineDesktop) {
    return;
  }

  // Existing useAutoSync code continues below this line.
```

Then create or modify your environment file:

## `.env.local`

```text
VITE_OFFLINE_DESKTOP=true
```

Do not commit `.env.local` if it contains secrets.

Because Vite replaces environment variables during the build, rebuild after changing it:

```bash
npm run build
```

---

# Part 11 — Disable cloud sync without breaking React hooks

A better pattern is to make the hook safe:

```javascript
export function useAutoSync() {
  const isOfflineDesktop =
    import.meta.env.VITE_OFFLINE_DESKTOP === 'true';

  React.useEffect(() => {
    if (isOfflineDesktop) {
      return;
    }

    // Existing sync setup goes here.
  }, [isOfflineDesktop]);

  return {
    isSyncing: false,
    syncNow: async () => false,
  };
}
```

Do not blindly paste this over the whole file because your current hook may return additional functions.

The important rule is:

```javascript
if (isOfflineDesktop) {
  return;
}
```

must happen before network synchronization begins.

---

# Part 12 — Add a desktop build script

Create this file in the repository root:

## `build_desktop.bat`

```bat
@echo off
setlocal

echo.
echo [1/4] Installing JavaScript dependencies...
call npm install
if errorlevel 1 goto error

echo.
echo [2/4] Building React application...
call npm run build
if errorlevel 1 goto error

echo.
echo [3/4] Installing Python desktop dependencies...
python -m pip install -r requirements-desktop.txt
if errorlevel 1 goto error

echo.
echo [4/4] Building ConlangEngine desktop executable...
python -m nuitka ^
  --standalone ^
  --enable-plugin=pyside6 ^
  --include-data-dir=dist=dist ^
  --output-dir=build ^
  --output-filename=ConlangEngine.exe ^
  desktop_launcher.py

if errorlevel 1 goto error

echo.
echo Build finished successfully.
echo The application is in:
echo build\desktop_launcher.dist\
pause
exit /b 0

:error
echo.
echo Build failed.
pause
exit /b 1
```

This script:

1. Installs JavaScript packages.
2. Builds the React application.
3. Installs PySide6.
4. Packages the desktop launcher with Nuitka.
5. Includes the Vite `dist` directory.

---

# Part 13 — Install Nuitka

Run:

```bash
python -m pip install nuitka
```

Nuitka also needs a C compiler.

On Windows, the easiest option is usually:

- Visual Studio Build Tools
- Desktop development with C++
- Windows SDK

You can check Nuitka with:

```bash
python -m nuitka --version
```

If Nuitka complains about a compiler, install Visual Studio Build Tools and select:

```text
Desktop development with C++
```

---

# Part 14 — Build the executable

Run:

```bash
build_desktop.bat
```

Or run the command manually:

```bash
python -m nuitka ^
  --standalone ^
  --enable-plugin=pyside6 ^
  --include-data-dir=dist=dist ^
  --output-dir=build ^
  --output-filename=ConlangEngine.exe ^
  desktop_launcher.py
```

The output will usually be similar to:

```text
build/
└── desktop_launcher.dist/
    ├── ConlangEngine.exe
    ├── dist/
    │   ├── index.html
    │   └── assets/
    ├── PySide6/
    ├── Qt6Core.dll
    ├── Qt6Gui.dll
    ├── Qt6WebEngineCore.dll
    └── ...
```

Run:

```text
build/desktop_launcher.dist/ConlangEngine.exe
```

Do not move only the `.exe` file out of the folder.

The entire `.dist` folder is needed because it contains:

- Qt DLLs
- WebEngine files
- Python runtime files
- React `dist` files
- JavaScript assets
- CSS assets

---

# Part 15 — Optional: create a single-file executable

Once the standalone version works, you can try:

```bash
python -m nuitka ^
  --onefile ^
  --enable-plugin=pyside6 ^
  --include-data-dir=dist=dist ^
  --output-dir=build ^
  --output-filename=ConlangEngine.exe ^
  desktop_launcher.py
```

However, for PySide6 WebEngine, `--standalone` is usually easier to debug and distribute.

Use this first:

```text
--standalone
```

Only try:

```text
--onefile
```

after the standalone version works.

---

# Recommended order for you

Because you mentioned ADHD, do only one checkpoint at a time.

## Checkpoint 1

Run:

```bash
npm run build
```

If it fails, fix that first.

## Checkpoint 2

Run:

```bash
python desktop_launcher.py
```

If the window opens, continue.

## Checkpoint 3

Test local features:

- Create a word.
- Refresh.
- Close and reopen.
- Export a JSON backup.
- Import the JSON backup.

## Checkpoint 4

Disable cloud sync using:

```text
VITE_OFFLINE_DESKTOP=true
```

Then rebuild:

```bash
npm run build
```

## Checkpoint 5

Run Nuitka in standalone mode.

## Checkpoint 6

Only after that, try one-file mode.

---

# The most important thing

You are not converting the entire project from JavaScript to Python.

You are creating this structure:

```text
React/Vite application
        ↓
npm run build
        ↓
dist/
        ↓
PySide6 QWebEngineView
        ↓
Nuitka executable
```

Your existing local-first features can remain in React. PySide6 is acting as the desktop window around your already-built application.

The repository’s current local storage, IndexedDB, JSON backup, dictionary, grammar, wiki, generator, analyzer, and study features should remain available. Supabase, PayPal, Datamuse, cloud sync, and public web sharing need to be disabled or replaced for a fully offline version.