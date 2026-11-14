use std::sync::Mutex;

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

/// Holds the spawned backend sidecar so it can be killed on exit.
struct BackendProcess(Mutex<Option<CommandChild>>);

#[tauri::command]
fn check_backend_status() -> String {
    "CodeSentinel Backend Connected".into()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![check_backend_status])
        .setup(|app| {
            // Spawn the bundled Python backend sidecar. In dev (`tauri dev`)
            // the binary also exists under binaries/, so this works in both modes.
            match app.shell().sidecar("codesentinel-backend") {
                Ok(sidecar) => match sidecar.env("CODESENTINEL_PARENT_WATCHDOG", "1").spawn() {
                    Ok((_rx, child)) => {
                        let state = app.state::<BackendProcess>();
                        *state.0.lock().unwrap() = Some(child);
                        eprintln!("[codesentinel] backend sidecar started");
                    }
                    Err(e) => eprintln!("[codesentinel] failed to spawn backend sidecar: {e}"),
                },
                Err(e) => eprintln!("[codesentinel] backend sidecar not found: {e}"),
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building CodeSentinel AI application");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            // Terminate the backend sidecar when the app closes.
            let child = {
                let state = app_handle.state::<BackendProcess>();
                let taken = state.0.lock().unwrap().take();
                taken
            };
            if let Some(child) = child {
                let _ = child.kill();
            }
        }
    });
}
