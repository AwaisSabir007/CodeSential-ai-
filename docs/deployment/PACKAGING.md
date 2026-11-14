# CodeSentinel AI — Cross-Platform Packaging & Distribution Guide

## 1. Architecture Overview
CodeSentinel AI distributes as a standalone native desktop application bundling:
1. **Frontend**: Tauri 2 + React + TypeScript (Native WebKit / WebView2)
2. **Backend**: Python 3.11 FastAPI server, frozen with PyInstaller and bundled as a
   **Tauri sidecar** that the app spawns on launch and terminates on exit
3. **Database**: Local zero-config SQLite — in packaged mode it lives in the per-user
   data directory (`~/Library/Application Support/CodeSentinelAI/` on macOS), in
   development mode next to the repository

The frontend talks to the sidecar at `http://127.0.0.1:8765` (REST) and
`ws://127.0.0.1:8765/api/v1/ws/events` (live events).

---

## 2. Step 1 — Freeze the Python Backend (PyInstaller)

From the repository root (requires the project venv with backend deps installed):

```bash
.venv/bin/pyinstaller --clean -y --onefile \
  --name codesentinel-backend \
  --distpath packaging/dist \
  --workpath packaging/build \
  --specpath packaging \
  --paths "$PWD" \
  --hidden-import sqlalchemy.dialects.sqlite.aiosqlite \
  --hidden-import aiosqlite \
  packaging/sidecar_entry.py
```

Verify the frozen binary standalone:

```bash
CODESENTINEL_PORT=8766 ./packaging/dist/codesentinel-backend &
curl http://127.0.0.1:8766/api/v1/system/health   # → {"status":"healthy",...}
```

## 3. Step 2 — Install the Sidecar into Tauri

Tauri requires the binary name to carry the Rust target triple:

```bash
cp packaging/dist/codesentinel-backend \
   "apps/desktop/src-tauri/binaries/codesentinel-backend-$(rustc -vV | sed -n 's/host: //p')"
```

Already configured in the repo:
- `tauri.conf.json` → `bundle.externalBin: ["binaries/codesentinel-backend"]`
- `Cargo.toml` → `tauri-plugin-shell = "2"`
- `src-tauri/src/lib.rs` → spawns the sidecar on startup, kills it on exit

## 4. Step 3 — Build Desktop Installers

### macOS
```bash
cd apps/desktop
npm install
npm run tauri build
```
Outputs:
- `apps/desktop/src-tauri/target/release/bundle/macos/CodeSentinel AI.app`
- `apps/desktop/src-tauri/target/release/bundle/dmg/CodeSentinel AI_<version>_x64.dmg`

> Unsigned builds: recipients must right-click → Open on first launch, or the build
> must be signed and notarized with an Apple Developer ID for distribution.

### Windows (10/11 64-bit)
Run the same two steps on a Windows machine (or CI): freeze the backend with
PyInstaller (produces `codesentinel-backend.exe`, copy it as
`binaries/codesentinel-backend-x86_64-pc-windows-msvc.exe`), then
`npm run tauri build` → MSI/NSIS installers under `bundle/`.

### Linux
Same procedure on a Linux host → `.deb` / `.AppImage` under `bundle/`.

PyInstaller does not cross-compile: each OS builds its own sidecar binary
(GitHub Actions matrix builds are the standard approach).

---

## 5. External Scanner Tools (optional, graceful degradation)

The frozen backend bundles the Python scanning *adapters*; the scanner *tools*
resolve from the host machine. Out of the box the packaged app has:

| Scanner | Status in packaged app |
|---|---|
| complexity (AST) | built-in, always available |
| npm audit | works if Node/npm installed |
| bandit / pip-audit | works if installed (`pipx install bandit pip-audit`) |
| gitleaks | works if installed (`brew install gitleaks`) |
| semgrep | works if installed (`pipx install semgrep==1.50.0` on Intel macs; latest elsewhere). Uses the bundled offline rule packs in `rules/` |

Missing tools are reported as `unavailable` in Settings — scans still run with
the remaining engines.

## 6. LLM Providers

The agent pipeline uses, in order of preference: a local Ollama server
(`http://localhost:11434`), an OpenAI API key, or a Gemini API key — configured
via Settings or `CODESENTINEL_*` environment variables. With none configured it
falls back to the deterministic mock provider (reduced reasoning quality).
