#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod backend;
use backend::{BackendProcess, spawn_backend};
use tauri::{Emitter, Manager};

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .manage(BackendProcess(std::sync::Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();
            if let Err(e) = spawn_backend(handle.clone(), app.state::<BackendProcess>().inner()) {
                eprintln!("Backend error: {e}");
                let _ = handle.emit("backend-status", format!("error: {e}"));
            }
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
}
