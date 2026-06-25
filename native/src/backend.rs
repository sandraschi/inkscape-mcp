use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::str::FromStr;
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::path::BaseDirectory;
use tauri::{AppHandle, Emitter, Manager};

pub struct BackendProcess(pub Mutex<Option<Child>>);

const BACKEND_NAME: &str = "inkscape-mcp-backend.exe";
const BACKEND_PORT: u16 = 11028;

fn dev_backend_path() -> Option<PathBuf> {
    if !cfg!(debug_assertions) {
        return None;
    }
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("binaries")
        .join("inkscape-mcp-backend-x86_64-pc-windows-msvc.exe");
    path.exists().then_some(path)
}

fn log_line(app: &AppHandle, message: &str) {
    eprintln!("[backend] {message}");
    if let Ok(dir) = app.path().app_log_dir() {
        let _ = fs::create_dir_all(&dir);
        let log_path = dir.join("backend-spawn.log");
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
            let _ = writeln!(file, "{message}");
        }
    }
}

fn resolve_bundled_backend(app: &AppHandle) -> Result<PathBuf, String> {
    let mut tried = Vec::new();

    if let Ok(path) = app.path().resolve(BACKEND_NAME, BaseDirectory::Resource) {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    if let Ok(path) = app
        .path()
        .resolve("resources/inkscape-mcp-backend.exe", BaseDirectory::Resource)
    {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    if let Ok(dir) = app.path().executable_dir() {
        let path = dir.join("resources").join(BACKEND_NAME);
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    Err(format!(
        "bundled backend missing from resources (tried: {})",
        tried.join("; ")
    ))
}

fn install_dir_from_backend(path: &PathBuf) -> PathBuf {
    if let Some(parent) = path.parent() {
        if parent
            .file_name()
            .is_some_and(|name| name.eq_ignore_ascii_case("resources"))
        {
            if let Some(install_dir) = parent.parent() {
                return install_dir.to_path_buf();
            }
        }
        return parent.to_path_buf();
    }
    PathBuf::from(".")
}

pub fn materialize_backend(app: &AppHandle) -> Result<PathBuf, String> {
    if let Some(dev_path) = dev_backend_path() {
        log_line(app, &format!("using dev backend: {}", dev_path.display()));
        return Ok(dev_path);
    }

    let bundled = resolve_bundled_backend(app)?;
    log_line(
        app,
        &format!("using bundled backend: {}", bundled.display()),
    );
    Ok(bundled)
}

fn free_port(port: u16) -> bool {
    #[cfg(windows)]
    {
        // ── Kill by image name (catches zombies NOT holding the port) ──
        let img_kill = "Stop-Process -Name 'inkscape-mcp-backend' -Force -ErrorAction SilentlyContinue; Stop-Process -Name 'inkscape-mcp-native' -Force -ErrorAction SilentlyContinue; taskkill /F /IM inkscape-mcp-backend.exe /T 2>nul; taskkill /F /IM inkscape-mcp-native.exe /T 2>nul".to_string();
        let _ = Command::new("powershell.exe")
            .args(["-NoProfile", "-Command", &img_kill])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();

        // ── Kill by port (handles precise port-holder) ──
        let port_kill = format!(
            "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ taskkill /F /PID $_.OwningProcess /T 2>nul }}"
        );
        let _ = Command::new("powershell.exe")
            .args(["-NoProfile", "-Command", &port_kill])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();

        // ── Wait for port to be truly free (TIME_WAIT ~240s on Windows) ──
        let poll_script = format!(
            "if (Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue) {{ 1 }} else {{ 0 }}"
        );
        for i in 0..240 {
            let output = Command::new("powershell.exe")
                .args(["-NoProfile", "-Command", &poll_script])
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .output();
            let occupied = output.ok().and_then(|o| {
                String::from_utf8(o.stdout).ok().and_then(|s| s.trim().parse::<u32>().ok())
            }).unwrap_or(1);
            if occupied == 0 {
                return true;
            }
            if i % 15 == 0 && i > 0 {
                // Re-kill every 15s (new process may have claimed the port)
                let _ = Command::new("powershell.exe")
                    .args(["-NoProfile", "-Command", &img_kill])
                    .stdout(Stdio::null()).stderr(Stdio::null()).status();
                let _ = Command::new("powershell.exe")
                    .args(["-NoProfile", "-Command", &port_kill])
                    .stdout(Stdio::null()).stderr(Stdio::null()).status();
            }
            thread::sleep(Duration::from_secs(1));
        }
        return false;
    }
    #[cfg(not(windows))]
    { true }
}

fn stop_managed_child(state: &BackendProcess) {
    if let Some(mut child) = state.0.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

pub fn spawn_backend(app: AppHandle, state: &BackendProcess) -> Result<String, String> {
    stop_managed_child(state);
    if !free_port(BACKEND_PORT) {
        let msg = format!("Could not free port {BACKEND_PORT} after 240s — TIME_WAIT not cleared");
        log_line(&app, &msg);
        return Err(msg);
    }

    let backend_path = materialize_backend(&app)?;
    let workdir = app
        .path()
        .executable_dir()
        .ok()
        .unwrap_or_else(|| install_dir_from_backend(&backend_path));

    log_line(
        &app,
        &format!(
            "spawning {} (cwd {}) on port {BACKEND_PORT}",
            backend_path.display(),
            workdir.display()
        ),
    );

    let mut command = Command::new(&backend_path);
    command
        .current_dir(&workdir)
        .env("MCP_PORT", BACKEND_PORT.to_string())
        .env("MCP_HOST", "127.0.0.1")
        .env("INKSCAPE_TAURI", "1")
        .env("PYTHONUNBUFFERED", "1")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        command.creation_flags(CREATE_NO_WINDOW);
    }

    let mut child = command
        .spawn()
        .map_err(|e| format!("Failed to spawn {}: {e}", backend_path.display()))?;

    let stdout = child.stdout.take();
    let stderr = child.stderr.take();
    state.0.lock().unwrap().replace(child);

    if let Some(out) = stdout {
        let app_handle = app.clone();
        thread::spawn(move || watch_backend_stream(out, app_handle));
    }
    if let Some(err) = stderr {
        let app_handle = app.clone();
        thread::spawn(move || watch_backend_stream(err, app_handle));
    }

    let health_app = app.clone();
    thread::spawn(move || {
        let addr = SocketAddr::from_str(&format!("127.0.0.1:{BACKEND_PORT}")).unwrap();
        for attempt in 0..30 {
            thread::sleep(Duration::from_secs(2));
            match TcpStream::connect_timeout(&addr, Duration::from_secs(2)) {
                Ok(_) => {
                    log_line(&health_app, &format!("Backend health check PASSED on port {BACKEND_PORT} (attempt {})", attempt + 1));
                    let _ = health_app.emit("backend-status", "ready");
                    return;
                }
                Err(e) => {
                    log_line(&health_app, &format!("Backend health check: {e} (attempt {})", attempt + 1));
                }
            }
        }
        log_line(&health_app, &format!("Backend health check FAILED — not listening on port {BACKEND_PORT} after 30 attempts"));
        let _ = health_app.emit("backend-status", "error: backend not reachable");
    });

    Ok(format!("Backend starting on port {BACKEND_PORT}"))
}

fn watch_backend_stream<R: std::io::Read + Send + 'static>(stream: R, app: AppHandle) {
    let reader = BufReader::new(stream);
    let mut ready = false;
    for line in reader.lines().map_while(Result::ok) {
        log_line(&app, &line);
        if !ready
            && (line.contains("Uvicorn running") || line.contains("Application startup complete"))
        {
            ready = true;
            let _ = app.emit("backend-status", "ready");
        }
    }
}
