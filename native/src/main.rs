#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod backend;
use backend::{BackendProcess, spawn_backend};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use tauri::{Emitter, Manager};

#[tauri::command]
async fn start_backend(app: tauri::AppHandle, state: tauri::State<'_, BackendProcess>) -> Result<String, String> {
    spawn_backend(app, &state)
}

fn spawn_headless_backend() {
    // Find the backend exe relative to the native exe
    let exe = std::env::current_exe().ok();
    let backend_path = exe.as_ref()
        .and_then(|p| p.parent())
        .map(|p| p.join("resources").join("inkscape-mcp-backend.exe"))
        .filter(|p| p.exists());

    if let Some(path) = backend_path {
        let workdir = path.parent().map(|p| p.to_path_buf()).unwrap_or_default();
        eprintln!("Headless mode: spawning backend at {} from {}", path.display(), workdir.display());
        let mut cmd = std::process::Command::new(&path);
        cmd.env("MCP_PORT", "11028")
            .env("MCP_HOST", "127.0.0.1")
            .env("PYTHONUNBUFFERED", "1")
            .env("INKSCAPE_TAURI", "1");
        match cmd.spawn() {
            Ok(mut child) => {
                eprintln!("Headless backend spawned PID {}", child.id());
            }
            Err(e) => {
                eprintln!("Headless backend spawn failed: {e}");
            }
        }
    } else {
        eprintln!("Headless mode: backend exe not found");
    }
}

fn main() {
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        eprintln!("Tauri: attempting window creation...");
        tauri::Builder::default()
            .plugin(tauri_plugin_shell::init())
            .plugin(tauri_plugin_fs::init())
            .plugin(tauri_plugin_process::init())
            .manage(BackendProcess(std::sync::Mutex::new(None)))
            .invoke_handler(tauri::generate_handler![start_backend])
            .setup(|app| {
                let handle = app.handle().clone();
                tauri::async_runtime::spawn(async move {
                    if let Err(e) = spawn_backend(handle.clone(), &handle.state::<BackendProcess>()) {
                        eprintln!("Backend error: {e}");
                        let _ = handle.emit("backend-status", format!("error: {e}"));
                    }
                });
                Ok(())
            })
            .build(tauri::generate_context!())
            .expect("error building tauri application")
            .run(|app, event| {
                if let tauri::RunEvent::Exit = event {
                    if let Some(mut child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
                        let _ = child.kill();
                    }
                }
            });
    }));

    match result {
        Ok(()) => {}
        Err(panic_val) => {
            eprintln!("Tauri window failed (non-fatal): {:?}", panic_val);
            eprintln!("Keeping backend alive in headless mode");
            spawn_headless_backend();
            loop {
                thread::sleep(Duration::from_secs(30));
            }
        }
    }
}
